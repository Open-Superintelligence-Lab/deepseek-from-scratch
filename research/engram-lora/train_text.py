"""Bounded next-token adaptation on real WikiText-2; no classification head.
Run beside train_banking.py and the pinned model/data directories.
"""
from pathlib import Path
import argparse, json, math, time, gc, fcntl
import pyarrow.parquet as pq
import torch
from torch import nn
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from train_banking import Engram, seed_all, ROOT

class LanguageModel(nn.Module):
    def __init__(self, method, seed):
        super().__init__(); seed_all(seed)
        self.model=AutoModelForCausalLM.from_pretrained(ROOT/'model',local_files_only=True,torch_dtype=torch.float32,attn_implementation='sdpa')
        self.model.requires_grad_(False); self.model.config.use_cache=False
        self.adapter=None
        if method=='lora':
            self.model=get_peft_model(self.model,LoraConfig(r=8,lora_alpha=16,lora_dropout=0.,target_modules=['q_proj','v_proj'],bias='none'))
        if method=='engram':
            self.adapter=Engram(self.model.config.hidden_size)
            self.model.model.layers[7].register_forward_pre_hook(self.inject,with_kwargs=True)
    def inject(self,module,args,kwargs):
        if args:return (self.adapter(args[0]),)+args[1:],kwargs
        kwargs=dict(kwargs);kwargs['hidden_states']=self.adapter(kwargs['hidden_states']);return args,kwargs
    def forward(self,ids):
        if self.adapter is not None:self.adapter.ids=ids;self.adapter.mask=torch.ones_like(ids)
        return self.model(input_ids=ids,use_cache=False).logits
    def artifact(self):return {n:p.detach().cpu() for n,p in self.named_parameters() if p.requires_grad}
    def restore(self,state):
        with torch.no_grad():
            for n,p in self.named_parameters():
                if p.requires_grad:p.copy_(state[n].to(p.device))

def blocks(split,tok,limit,length=256):
    path=ROOT/'data/wikitext2/wikitext-2-raw-v1'/f'{split}-00000-of-00001.parquet'
    rows=pq.read_table(path,columns=['text']).column('text').to_pylist()
    # Non-overlapping contiguous blocks; official train/validation/test stay separate.
    ids=[]
    for text in rows:
        if text.strip():ids.extend(tok.encode(text,add_special_tokens=False)+[tok.eos_token_id])
        if len(ids)>=limit*length:break
    n=min(limit,len(ids)//length)
    return torch.tensor(ids[:n*length],dtype=torch.long).reshape(n,length)

def loss_for(logits,ids):
    return nn.functional.cross_entropy(logits[:,:-1].float().reshape(-1,logits.size(-1)),ids[:,1:].reshape(-1))

@torch.no_grad()
def evaluate(model,data,batch=4):
    model.eval();total=0.;count=0
    for ids in data.split(batch):
        ids=ids.cuda()
        with torch.autocast('cuda',dtype=torch.bfloat16):loss=loss_for(model(ids),ids)
        n=ids.size(0)*(ids.size(1)-1);total+=loss.item()*n;count+=n
    nll=total/count
    return dict(nll=nll,perplexity=math.exp(nll),predicted_tokens=count,context_tokens=256)

@torch.no_grad()
def samples(model,tok,prompts):
    model.eval();out=[]
    for prompt in prompts:
        ids=tok(prompt,return_tensors='pt').input_ids.cuda();original=ids.size(1)
        torch.cuda.synchronize();start=time.perf_counter()
        for _ in range(40):
            with torch.autocast('cuda',dtype=torch.bfloat16):nxt=model(ids)[:,-1].argmax(-1,keepdim=True)
            ids=torch.cat([ids,nxt],dim=1)
            if nxt.item()==tok.eos_token_id:break
        torch.cuda.synchronize();seconds=time.perf_counter()-start
        out.append(dict(prompt=prompt,continuation=tok.decode(ids[0,original:],skip_special_tokens=True),new_tokens=ids.size(1)-original,seconds=seconds))
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='text-pilot-r01');p.add_argument('--seed',type=int,default=42);p.add_argument('--smoke',action='store_true');a=p.parse_args()
    lock=open(ROOT/'training.lock','w');fcntl.flock(lock,fcntl.LOCK_EX)
    torch.set_num_threads(4);torch.cuda.set_per_process_memory_fraction(.30);torch.backends.cuda.matmul.allow_tf32=True
    out=ROOT/'runs'/a.output;out.mkdir(parents=True,exist_ok=True)
    tok=AutoTokenizer.from_pretrained(ROOT/'model',local_files_only=True)
    train=blocks('train',tok,8 if a.smoke else 512);val=blocks('validation',tok,4 if a.smoke else 64)
    prompts=['The history of artificial intelligence','The city of New York','In a scientific experiment,','The company announced that']
    config=dict(seed=a.seed,train_blocks=len(train),validation_blocks=len(val),block_length=256,epochs=1 if a.smoke else 2,batch=4,learning_rates=[.001] if a.smoke else [.0003,.001],data='Salesforce/wikitext wikitext-2-raw-v1',selection='lowest validation NLL',generation_prompts=prompts,generation='greedy, 40 tokens, full-prefix recomputation for ALL methods; not an optimized decode benchmark',gpu_contended=True,scope='Small contiguous subsets of official splits, not a full WikiText benchmark; no cross-model transfer test')
    (out/'config.json').write_text(json.dumps(config,indent=2));print('CONFIG',json.dumps(config),flush=True)
    trials=[]
    for method in ['lora','engram']:
        for lr in config['learning_rates']:
            dest=out/f'{method}-lr{lr}';dest.mkdir(exist_ok=True)
            model=LanguageModel(method,a.seed).cuda();params=[x for x in model.parameters() if x.requires_grad]
            ids=train[:1,:12].cuda();model.eval()
            if method=='engram':
                with torch.no_grad():
                    before=model(ids);model.adapter.enabled=False;without=model(ids);model.adapter.enabled=True
                assert torch.equal(before,without),'Nonzero initial adapter'
            # Future tokens must not change prefix logits, including convolution.
            with torch.no_grad():
                original=model(ids);changed=ids.clone();changed[:,-2:]=0;altered=model(changed)
            assert torch.allclose(original[:,:-2],altered[:,:-2],atol=1e-5,rtol=1e-5),'Causality failed'
            optimizer=torch.optim.AdamW(params,lr=lr,weight_decay=.01);best=float('inf');history=[]
            torch.cuda.reset_peak_memory_stats();start=time.perf_counter()
            for epoch in range(config['epochs']):
                model.train();order=torch.randperm(len(train),generator=torch.Generator().manual_seed(a.seed+epoch));total=0
                for step,ix in enumerate(order.split(4)):
                    ids=train[ix].cuda();optimizer.zero_grad(set_to_none=True)
                    with torch.autocast('cuda',dtype=torch.bfloat16):loss=loss_for(model(ids),ids)
                    assert torch.isfinite(loss);loss.backward()
                    if method=='engram' and epoch==0 and step==1:assert model.adapter.tables[0].weight.grad.abs().sum()>0
                    assert all(x.grad is None for x in model.parameters() if not x.requires_grad)
                    nn.utils.clip_grad_norm_(params,1.);optimizer.step();total+=loss.item()*len(ix)
                    if step%16==0:print('STEP',method,lr,epoch+1,step,float(loss),flush=True)
                score=evaluate(model,val);history.append(dict(epoch=epoch+1,train_nll=total/len(train),validation=score))
                print('EPOCH',method,lr,json.dumps(history[-1]),flush=True)
                if score['nll']<best:best=score['nll'];torch.save(model.artifact(),dest/'adapter.pt')
            state=torch.load(dest/'adapter.pt',weights_only=True);model.restore(state)
            with torch.no_grad():expected=model(train[:1,:12].cuda()).cpu()
            with torch.no_grad():
                for param in params:param.zero_()
            model.restore(state)
            with torch.no_grad():assert torch.equal(expected,model(train[:1,:12].cuda()).cpu())
            record=dict(method=method,lr=lr,best_validation_nll=best,trainable_parameters=sum(x.numel() for x in params),history=history,training_wall_seconds=time.perf_counter()-start,peak_allocated_mb=torch.cuda.max_memory_allocated()/2**20,artifact_bytes=(dest/'adapter.pt').stat().st_size,reload_exact=True)
            (dest/'result.json').write_text(json.dumps(record,indent=2));trials.append(record)
            del model,optimizer,params,state;gc.collect();torch.cuda.empty_cache()
    if a.smoke:print('SMOKE PASSED',flush=True);return
    test=blocks('test',tok,128);results=[]
    for method in ['frozen','lora','engram']:
        model=LanguageModel(method,a.seed).cuda();record={'method':method}
        if method!='frozen':
            chosen=min([r for r in trials if r['method']==method],key=lambda r:r['best_validation_nll'])
            model.restore(torch.load(out/f'{method}-lr{chosen["lr"]}'/'adapter.pt',weights_only=True));record.update(chosen)
        record['test']=evaluate(model,test);record['samples']=samples(model,tok,prompts);results.append(record)
        del model;gc.collect();torch.cuda.empty_cache()
    (out/'final-results.json').write_text(json.dumps(results,indent=2));print('FINAL',json.dumps(results),flush=True)

if __name__=='__main__':main()
