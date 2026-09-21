"""Bounded, reproducible finance/code specialist comparison. See SWAPPABLE-PROTOCOL.md."""
from pathlib import Path
from collections import Counter, defaultdict
import argparse, fcntl, gc, hashlib, json, math, time
import numpy as np
import pyarrow.parquet as pq
import torch
from torch import nn
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from train_banking import ROOT, Engram, seed_all
from train_text import blocks as wiki_blocks

OUT = ROOT / 'runs/swappable-r01'
DOMAINS = ['finance', 'code']
METHODS = ['lora8', 'engram-small', 'lora32', 'engram-large']
LRS = [.0003, .001]
LENGTH = 128

def sha(x):
    return hashlib.sha256(x.encode() if isinstance(x, str) else x).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2)); tmp.replace(path)

def clean():
    gc.collect(); torch.cuda.empty_cache()

def source_documents(domain):
    if domain == 'finance':
        paths = sorted((ROOT/'data/fiqa/corpus').glob('*.parquet'))
        rows = pq.read_table(paths[0]).to_pylist()
        docs = [(str(r['_id']), r['text'], None) for r in rows]
    else:
        paths = sorted((ROOT/'data/codesearchnet/ruby').glob('*.parquet'))
        docs = []
        for path in paths:
            for r in pq.read_table(path).to_pylist():
                docs.append((r['func_code_url'], r['func_code_string'], r['repository_name']))
    sources = [{'file':str(p.relative_to(ROOT/'data')), 'sha256':sha(p.read_bytes())} for p in paths]
    splits = defaultdict(list); seen = set(); duplicates = 0
    for ident, text, repo in sorted(docs, key=lambda d:sha(d[0])):
        normalized = ' '.join(text.split())
        if not normalized or normalized in seen:
            duplicates += 1; continue
        seen.add(normalized)
        bucket = int(sha(repo if repo is not None else normalized), 16) % 100
        split = 'train' if bucket < 80 else 'validation' if bucket < 90 else 'test'
        splits[split].append((ident, text, repo))
    return splits, dict(sources=sources, raw_documents=len(docs), duplicate_or_empty=duplicates,
                       split_available={k:len(v) for k,v in splits.items()})

def spans(ids):
    return {sha(np.asarray(ids[i:i+64], dtype=np.int32).tobytes()) for i in range(len(ids)-63)}

def prepare(tok):
    dest = OUT/'data.pt'
    if dest.exists(): return torch.load(dest, weights_only=True)
    data = {}; receipts = {}
    for domain in DOMAINS:
        splits, receipt = source_documents(domain); prior_spans = set(); data[domain] = {}
        receipt['selected'] = {}
        for split, limit in [('train',512), ('validation',64), ('test',64)]:
            stream = []; selected = []; rejected = 0; own_spans = set()
            for ident, text, repo in splits[split]:
                ids = tok.encode(text, add_special_tokens=False, truncation=True, max_length=1024)
                fingerprints = spans(ids)
                if split != 'train' and fingerprints & prior_spans:
                    rejected += 1; continue
                stream.extend(ids + [tok.eos_token_id]); own_spans.update(fingerprints)
                selected.append(dict(id=ident, repository=repo))
                if len(stream) >= limit*LENGTH: break
            assert len(stream) >= limit*LENGTH, (domain, split, len(stream))
            tensor = torch.tensor(stream[:limit*LENGTH], dtype=torch.long).reshape(limit,LENGTH)
            data[domain][split] = tensor; prior_spans.update(own_spans)
            receipt['selected'][split] = dict(documents=selected, filtered_shared_64_token_spans=rejected,
                blocks=limit, tokens=tensor.numel(), tensor_sha256=sha(tensor.numpy().tobytes()))
        # Code groups cannot cross splits under deterministic repository hashing.
        if domain == 'code':
            groups = [{r['repository'] for r in receipt['selected'][s]['documents']} for s in ['train','validation','test']]
            assert not (groups[0]&groups[1] or groups[0]&groups[2] or groups[1]&groups[2])
        receipts[domain] = receipt
    data['general'] = {'test':wiki_blocks('test',tok,64).reshape(-1,LENGTH)}
    OUT.mkdir(parents=True,exist_ok=True); torch.save(data,dest)
    write(OUT/'data-receipt.json', receipts)
    print('DATA_READY', json.dumps({d:{s:list(t.shape) for s,t in splits.items()} for d,splits in data.items()}),flush=True)
    return data

class Model(nn.Module):
    def __init__(self, method, seed):
        super().__init__(); seed_all(seed)
        self.model = AutoModelForCausalLM.from_pretrained(ROOT/'model', local_files_only=True,
            torch_dtype=torch.float32,attn_implementation='sdpa')
        self.model.requires_grad_(False); self.model.config.use_cache=False; self.adapter=None
        if method.startswith('lora'):
            rank=int(method[4:]); self.model=get_peft_model(self.model,LoraConfig(r=rank,
                lora_alpha=2*rank,lora_dropout=0.,target_modules=['q_proj','v_proj'],bias='none'))
        elif method.startswith('engram'):
            self.adapter=Engram(self.model.config.hidden_size)
            if method=='engram-large':
                self.adapter.sizes=[13207,13217,13219,13229]
                self.adapter.tables=nn.ModuleList([nn.Embedding(n,32) for n in self.adapter.sizes])
                for t in self.adapter.tables:nn.init.normal_(t.weight,std=.02)
            self.model.model.layers[7].register_forward_pre_hook(self.inject,with_kwargs=True)
    def inject(self,module,args,kwargs):
        if args:return (self.adapter(args[0]),)+args[1:],kwargs
        kwargs=dict(kwargs);kwargs['hidden_states']=self.adapter(kwargs['hidden_states']);return args,kwargs
    def forward(self,ids):
        if self.adapter is not None:self.adapter.ids=ids;self.adapter.mask=torch.ones_like(ids)
        return self.model(input_ids=ids,use_cache=False).logits
    def artifact(self):return {n:p.detach().cpu().clone() for n,p in self.named_parameters() if p.requires_grad}
    def restore(self,state):
        params={n:p for n,p in self.named_parameters() if p.requires_grad}
        assert params.keys()==state.keys()
        with torch.no_grad():
            for n,p in params.items():p.copy_(state[n].to(p.device))

def token_losses(model, ids):
    with torch.autocast('cuda',dtype=torch.bfloat16):
        logits=model(ids)
        return nn.functional.cross_entropy(logits[:,:-1].float().reshape(-1,logits.size(-1)),
            ids[:,1:].reshape(-1),reduction='none').reshape(ids.size(0),-1)

@torch.no_grad()
def evaluate(model, data, counts=None):
    model.eval(); losses=[]; bucket=defaultdict(list)
    for row in data:
        values=token_losses(model,row[None].cuda())[0].cpu().numpy();losses.append(values)
        if counts is not None:
            for i in range(2,len(row)-1):
                n=counts.get(tuple(row[i-2:i+1].tolist()),0)
                name='frequent_5plus' if n>=5 else 'seen_1to4' if n else 'unseen'
                bucket[name].append(float(values[i]))
    nll=float(np.concatenate(losses).mean())
    return dict(nll=nll,perplexity=math.exp(nll),predicted_tokens=data.size(0)*(data.size(1)-1),
        block_nll=[float(v.mean()) for v in losses],buckets={k:dict(nll=float(np.mean(v)),tokens=len(v)) for k,v in bucket.items()})

def context_counts(data):
    return Counter(tuple(row[i-2:i+1].tolist()) for row in data for i in range(2,len(row)-1))

def train(domain,method,seed,lr,data,smoke=False):
    dest=OUT/('smoke' if smoke else 'trials')/f'{domain}-{method}-s{seed}-lr{lr}'
    if (dest/'result.json').exists():return json.loads((dest/'result.json').read_text())
    dest.mkdir(parents=True,exist_ok=True); model=Model(method,seed).cuda()
    params=[p for p in model.parameters() if p.requires_grad]
    train_data=data[domain]['train'][:16] if smoke else data[domain]['train']
    val=data[domain]['validation'][:2] if smoke else data[domain]['validation']
    model.eval();ids=train_data[:1,:12].cuda()
    with torch.no_grad():
        initial=model(ids)
        if model.adapter is not None:
            model.adapter.enabled=False; base=model(ids);model.adapter.enabled=True
        else:
            with model.model.disable_adapter():base=model(ids)
        assert torch.equal(initial,base),'initial identity failed'
        changed=ids.clone();changed[:,-2:]=0
        assert torch.allclose(initial[:,:-2],model(changed)[:,:-2],atol=1e-5,rtol=1e-5),'causality failed'
    del initial,base,changed,ids
    opt=torch.optim.AdamW(params,lr=lr,weight_decay=.01);best=float('inf');history=[]
    torch.cuda.reset_peak_memory_stats();start=time.perf_counter()
    for epoch in range(1 if smoke else 2):
        model.train();order=torch.randperm(len(train_data),generator=torch.Generator().manual_seed(seed+epoch))
        total=0.;opt.zero_grad(set_to_none=True)
        for step,indices in enumerate(order.split(8)):
            for idx in indices:
                ids=train_data[idx:idx+1].cuda();loss=token_losses(model,ids).mean()
                assert torch.isfinite(loss);(loss/len(indices)).backward();total+=float(loss.detach())
            assert all(p.grad is None for p in model.parameters() if not p.requires_grad)
            if model.adapter is not None and epoch==0 and step==1:
                assert model.adapter.tables[0].weight.grad.abs().sum()>0,'table gradient absent'
            nn.utils.clip_grad_norm_(params,1.);opt.step();opt.zero_grad(set_to_none=True)
            if step%16==0:print('STEP',domain,method,seed,lr,epoch+1,step,float(loss.detach()),flush=True)
        score=evaluate(model,val);history.append(dict(epoch=epoch+1,train_nll=total/len(train_data),validation=score))
        if score['nll']<best:best=score['nll'];torch.save(model.artifact(),dest/'adapter.pt')
        print('EPOCH',domain,method,seed,lr,epoch+1,score['nll'],flush=True)
    model.restore(torch.load(dest/'adapter.pt',weights_only=True));model.eval()
    with torch.no_grad():
        expected=model(train_data[:1,:12].cuda()).cpu()
        for p in params:p.zero_()
        model.restore(torch.load(dest/'adapter.pt',weights_only=True))
        assert torch.equal(expected,model(train_data[:1,:12].cuda()).cpu()),'reload failed'
    result=dict(domain=domain,method=method,seed=seed,lr=lr,best_validation_nll=best,history=history,
        trainable_parameters=sum(p.numel() for p in params),artifact_bytes=(dest/'adapter.pt').stat().st_size,
        training_wall_seconds=time.perf_counter()-start,peak_allocated_mb=torch.cuda.max_memory_allocated()/2**20,
        artifact=str((dest/'adapter.pt').relative_to(OUT)),checks_passed=True)
    write(dest/'result.json',result)
    del model,opt,params,expected,loss;clean()
    return result

def count_baseline(train,val,test,vocab):
    unigram=Counter(train.flatten().tolist()); contexts=defaultdict(Counter)
    for row in train.tolist():
        for i in range(2,len(row)):contexts[tuple(row[i-2:i])][row[i]]+=1
    total=sum(unigram.values());denom=total+.1*vocab
    def score(data,strength):
        losses=[]
        for row in data.tolist():
            for i in range(1,len(row)):
                word=row[i];prior=(unigram[word]+.1)/denom
                c=contexts.get(tuple(row[i-2:i]),{}) if i>=2 else {}
                probability=(c.get(word,0)+strength*prior)/(sum(c.values())+strength)
                losses.append(-math.log(probability))
        return float(np.mean(losses))
    strengths=[1.,10.,100.];chosen=min(strengths,key=lambda s:score(val,s));nll=score(test,chosen)
    return dict(nll=nll,perplexity=math.exp(nll),validation_selected_strength=chosen)

def finish(data,selected):
    counts={d:context_counts(data[d]['train']) for d in DOMAINS};results=[]
    base=Model('frozen',42).cuda()
    baseline={d:evaluate(base,data[d]['test'],counts.get(d)) for d in [*DOMAINS,'general']}
    del base;clean();write(OUT/'baseline.json',baseline)
    for seed in [42,43,44]:
        for method in METHODS:
            model=Model(method,seed).cuda();model.eval()
            states={d:torch.load(OUT/selected[f'{d}:{method}:{seed}']['artifact'],weights_only=True) for d in DOMAINS}
            # Actual same-instance hot swap A -> B -> A, not separate base loads.
            ids=data['finance']['test'][:1,:12].cuda()
            model.restore(states['finance'])
            with torch.no_grad():original=model(ids).cpu()
            model.restore(states['code'])
            with torch.no_grad():swapped=model(ids).cpu()
            model.restore(states['finance'])
            with torch.no_grad():assert torch.equal(original,model(ids).cpu())
            delta=float((original-swapped).abs().max())
            for specialist in DOMAINS:
                model.restore(states[specialist]);rec=dict(selected[f'{specialist}:{method}:{seed}'])
                rec['evaluation']={d:evaluate(model,data[d]['test'],counts.get(d)) for d in [*DOMAINS,'general']}
                rec['swap_restoration_exact']=True;rec['swap_max_logit_change']=delta;results.append(rec)
                write(OUT/'partial-evaluation.json',results)
                print('TEST',specialist,method,seed,json.dumps({d:r['nll'] for d,r in rec['evaluation'].items()}),flush=True)
            del model,states,original,swapped;clean()
    classical={d:count_baseline(data[d]['train'],data[d]['validation'],data[d]['test'],49152) for d in DOMAINS}
    write(OUT/'final-results.json',dict(baseline=baseline,count_baseline=classical,adapters=results))
    print('COMPLETE',OUT/'final-results.json',flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--prepare-only',action='store_true');p.add_argument('--smoke',action='store_true');a=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    lock=open(ROOT/'training.lock','w');fcntl.flock(lock,fcntl.LOCK_EX)
    torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=True
    tok=AutoTokenizer.from_pretrained(ROOT/'model',local_files_only=True);data=prepare(tok)
    if a.prepare_only:return
    torch.cuda.set_per_process_memory_fraction(.18)
    if a.smoke:
        for method in ['lora32','engram-large']:train('finance',method,42,.001,data,True)
        print('SMOKE_PASSED',flush=True);return
    protocol=ROOT/'SWAPPABLE-PROTOCOL.md'
    write(OUT/'run-receipt.json',dict(protocol_sha256=sha(protocol.read_bytes()),
        script_sha256=sha(Path(__file__).read_bytes()),started_unix=time.time(),seeds=[42,43,44],
        methods=METHODS,learning_rates=LRS,training_blocks_per_domain=512,epochs=2,
        effective_batch=8,microbatch=1,context=128,gpu_contended=True))
    selected={}
    for domain in DOMAINS:
        for method in METHODS:
            trials=[train(domain,method,42,lr,data) for lr in LRS]
            selected[f'{domain}:{method}:42']=min(trials,key=lambda r:r['best_validation_nll'])
    write(OUT/'locked-selection-seed42.json',selected)
    # All LR choices locked before any test evaluation or seed repeats.
    for seed in [43,44]:
        for domain in DOMAINS:
            for method in METHODS:
                lr=selected[f'{domain}:{method}:42']['lr']
                selected[f'{domain}:{method}:{seed}']=train(domain,method,seed,lr,data)
    write(OUT/'selected.json',selected);finish(data,selected)

if __name__=='__main__':main()
