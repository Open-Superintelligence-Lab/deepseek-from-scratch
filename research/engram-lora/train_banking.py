"""Bounded real-data pilot: frozen SmolLM2 + head vs LoRA vs Engram-inspired adapter.
Small-data scenario, fixed splits and equal tuning trials; no synthetic records.
"""
from pathlib import Path
import argparse, csv, hashlib, json, math, random, time, gc, os, fcntl
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
from transformers import AutoModel, AutoTokenizer
from peft import LoraConfig, get_peft_model

ROOT=Path(__file__).resolve().parent
def seed_all(seed):
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)

class Engram(nn.Module):
    """2/3-grams, two independent hash heads each; gate, value, causal depthwise conv.
    Single residual stream; original token IDs, no tokenizer compression/mHC.
    Paper Eq. 3-5 sigmoid gate (not demo's signed-square-root score variant).
    """
    def __init__(self,d):
        super().__init__()
        self.sizes=[2401,2411,2417,2423];self.orders=[2,2,3,3]
        self.tables=nn.ModuleList([nn.Embedding(n,32) for n in self.sizes])
        self.key=nn.Linear(128,d,bias=False);self.value=nn.Linear(128,d,bias=False)
        self.qnorm=nn.RMSNorm(d);self.knorm=nn.RMSNorm(d);self.vnorm=nn.RMSNorm(d)
        self.conv=nn.Conv1d(d,d,kernel_size=4,dilation=3,groups=d,bias=False)
        self.register_buffer('multipliers',torch.tensor([[31,1009,10007],[47,1013,10009],[53,1019,10037],[59,1021,10039]],dtype=torch.long))
        for table in self.tables: nn.init.normal_(table.weight,std=.02)
        nn.init.zeros_(self.value.weight);nn.init.zeros_(self.conv.weight)
        self.enabled=True; self.ids=None; self.mask=None
    def addresses(self,ids):
        # +1 reserves 0 for left-boundary padding. Position order affects hashing.
        x=ids.long()+1; shifted=[x]
        for j in [1,2]: shifted.append(torch.nn.functional.pad(x,(j,0))[:,:x.size(1)])
        results=[]
        for i,(n,size) in enumerate(zip(self.orders,self.sizes)):
            h=shifted[0]*self.multipliers[i,0]
            for j in range(1,n):h=torch.bitwise_xor(h,shifted[j]*self.multipliers[i,j])
            results.append(h.remainder(size))
        return results
    def forward(self,h):
        if not self.enabled:return h
        e=torch.cat([table(idx) for table,idx in zip(self.tables,self.addresses(self.ids))],dim=-1)
        key=self.key(e);value=self.value(e)
        gate=torch.sigmoid((self.qnorm(h.float())*self.knorm(key.float())).sum(-1,keepdim=True)/math.sqrt(h.size(-1)))
        v=(gate*value.float())*self.mask.unsqueeze(-1)
        c=self.conv(torch.nn.functional.pad(self.vnorm(v).transpose(1,2),(9,0))).transpose(1,2)
        out=(v+torch.nn.functional.silu(c))*self.mask.unsqueeze(-1)
        return h+out.to(h.dtype)

class Classifier(nn.Module):
    def __init__(self,method,seed):
        super().__init__();seed_all(seed)
        self.backbone=AutoModel.from_pretrained(ROOT/'model',local_files_only=True,torch_dtype=torch.float32,attn_implementation='sdpa')
        self.backbone.requires_grad_(False);self.backbone.config.use_cache=False
        d=self.backbone.config.hidden_size;self.method=method;self.adapter=None
        if method=='lora':
            self.backbone=get_peft_model(self.backbone,LoraConfig(r=8,lora_alpha=16,lora_dropout=0.,target_modules=['q_proj','v_proj'],bias='none'))
        if method=='engram':
            self.adapter=Engram(d)
            self.hook=self.backbone.layers[7].register_forward_pre_hook(self.inject,with_kwargs=True)
        # Identical task head initialization regardless of adapter construction RNG.
        seed_all(seed+1000);self.head=nn.Linear(d,77)
    def inject(self,module,args,kwargs):
        if args:return (self.adapter(args[0]),)+args[1:],kwargs
        kwargs=dict(kwargs);kwargs['hidden_states']=self.adapter(kwargs['hidden_states']);return args,kwargs
    def forward(self,ids,mask):
        if self.adapter is not None:self.adapter.ids=ids;self.adapter.mask=mask
        h=self.backbone(input_ids=ids,attention_mask=mask,use_cache=False).last_hidden_state
        pooled=(h.float()*mask.unsqueeze(-1)).sum(1)/mask.sum(1,keepdim=True)
        return self.head(torch.nn.functional.layer_norm(pooled,(pooled.size(-1),)))
    def artifact(self):
        return {n:p.detach().cpu() for n,p in self.named_parameters() if p.requires_grad}
    def load_artifact(self,state):
        params=dict(self.named_parameters())
        with torch.no_grad():
            for n,v in state.items():params[n].copy_(v.to(params[n].device))

def prepare(seed,per_class):
    rows=list(csv.DictReader((ROOT/'data/banking77/train.csv').open()))
    categories=json.loads((ROOT/'data/banking77/categories.json').read_text())
    cats=sorted(categories);label={c:i for i,c in enumerate(cats)}
    # Group exact normalized duplicates before splitting to prevent leakage.
    groups={};conflicts=0
    for r in rows:
        key=' '.join(r['text'].lower().split())
        if key in groups and groups[key]['category']!=r['category']:conflicts+=1;continue
        groups[key]=r
    train=[];val=[];rng=random.Random(seed)
    for c in cats:
        rs=[dict(text=r['text'],label=label[c]) for r in groups.values() if r['category']==c]
        rng.shuffle(rs);val+=rs[:10];train+=rs[10:10+per_class] if per_class else rs[10:]
    rng.shuffle(train)
    return train,val,cats,{'raw_train_rows':len(rows),'unique_train_texts':len(groups),'conflicting_duplicates':conflicts}

def tokenized(rows,tok):
    enc=tok([r['text'] for r in rows],truncation=True,max_length=96,padding=False)
    return [{'input_ids':enc['input_ids'][i],'attention_mask':enc['attention_mask'][i],'label':r['label']} for i,r in enumerate(rows)]
def loaders(rows,tok,batch,shuffle,seed):
    def collate(items):
        labels=torch.tensor([x['label'] for x in items])
        pack=tok.pad([{k:v for k,v in x.items() if k!='label'} for x in items],padding=True,return_tensors='pt')
        return pack['input_ids'],pack['attention_mask'],labels
    return DataLoader(rows,batch_size=batch,shuffle=shuffle,collate_fn=collate,generator=torch.Generator().manual_seed(seed),num_workers=0)
def evaluate(model,loader):
    model.eval();correct=0;n=0;total=0;preds=[]
    with torch.no_grad(),torch.autocast('cuda',dtype=torch.bfloat16):
        for ids,mask,y in loader:
            ids=ids.cuda();mask=mask.cuda();y=y.cuda()
            out=model(ids,mask);loss=nn.functional.cross_entropy(out.float(),y,reduction='sum')
            p=out.argmax(-1);correct+=(p==y).sum().item();n+=len(y);total+=loss.item();preds+=p.cpu().tolist()
    return {'accuracy':correct/n,'loss':total/n,'n':n,'predictions':preds}
def checks(model,example):
    ids,mask,_=example;ids=ids.cuda();mask=mask.cuda();model.eval()
    if model.adapter is not None:
        with torch.no_grad():
            before=model(ids,mask);model.adapter.enabled=False;without=model(ids,mask);model.adapter.enabled=True
        assert torch.equal(before,without),'Zero-init Engram changes initial predictions'
        # Every address at a prefix must be independent of appended future tokens.
        short=model.adapter.addresses(ids[:,:3]);full=model.adapter.addresses(ids)
        assert all(torch.equal(a,b[:,:3]) for a,b in zip(short,full))
    for n,p in model.backbone.named_parameters():
        if p.requires_grad:assert 'lora_' in n,n

def train_one(args,method,lr,train,val,tok,outdir):
    model=Classifier(method,args.seed).cuda();checks(model,next(iter(loaders(train,tok,2,False,args.seed))))
    trainable=[p for p in model.parameters() if p.requires_grad]
    count=sum(p.numel() for p in trainable);head=sum(p.numel() for p in model.head.parameters())
    optimizer=torch.optim.AdamW(trainable,lr=lr,weight_decay=.01)
    trainloader=loaders(train,tok,args.batch,True,args.seed);valloader=loaders(val,tok,64,False,args.seed)
    initial=evaluate(model,valloader);best=-1;history=[];torch.cuda.reset_peak_memory_stats();start=time.perf_counter()
    frozen_name,frozen_param=next((n,p) for n,p in model.backbone.named_parameters() if not p.requires_grad)
    frozen_sample=frozen_param.detach().flatten()[:1024].clone()
    for epoch in range(args.epochs):
        model.train();running=0;n=0;tic=time.perf_counter()
        for step,(ids,mask,y) in enumerate(trainloader):
            ids=ids.cuda();mask=mask.cuda();y=y.cuda();optimizer.zero_grad(set_to_none=True)
            with torch.autocast('cuda',dtype=torch.bfloat16):loss=nn.functional.cross_entropy(model(ids,mask).float(),y)
            assert torch.isfinite(loss)
            loss.backward()
            if epoch==0 and step==2:
                if model.adapter is not None:assert model.adapter.tables[0].weight.grad.abs().sum()>0,'No table learning'
                assert all(p.grad is None for p in model.backbone.parameters() if not p.requires_grad)
            nn.utils.clip_grad_norm_(trainable,1.);optimizer.step();running+=loss.item()*len(y);n+=len(y)
            if step%20==0:print(json.dumps({'method':method,'lr':lr,'epoch':epoch+1,'step':step,'steps':len(trainloader),'loss':loss.item()}),flush=True)
            if args.smoke and step>=3:break
        metrics=evaluate(model,valloader);metrics.pop('predictions')
        row=dict(epoch=epoch+1,train_loss=running/n,val=metrics,seconds=time.perf_counter()-tic);history.append(row)
        print('EPOCH',method,lr,json.dumps(row),flush=True)
        if metrics['accuracy']>best:
            best=metrics['accuracy'];torch.save(model.artifact(),outdir/'adapter.pt')
        (outdir/'history.json').write_text(json.dumps(history,indent=2))
        if args.smoke:break
    assert torch.equal(frozen_sample,frozen_param.detach().flatten()[:1024]),'Frozen backbone changed'
    state=torch.load(outdir/'adapter.pt',weights_only=True);model.load_artifact(state)
    example=next(iter(valloader));ids,mask,_=example
    with torch.no_grad():expected=model(ids.cuda(),mask.cuda()).cpu()
    # Remove all trained parameters then restore the artifact exactly.
    with torch.no_grad():
        for p in trainable:p.zero_()
    model.load_artifact(state)
    with torch.no_grad():actual=model(ids.cuda(),mask.cuda()).cpu()
    assert torch.equal(expected,actual),'Artifact reload changed predictions'
    report={'method':method,'lr':lr,'seed':args.seed,'trainable_parameters':count,'classifier_parameters':head,'adapter_parameters':count-head,'best_validation_accuracy':best,'initial_validation_accuracy':initial['accuracy'],'training_wall_seconds':time.perf_counter()-start,'peak_allocated_mb':torch.cuda.max_memory_allocated()/2**20,'artifact_bytes':(outdir/'adapter.pt').stat().st_size,'reload_exact':True,'frozen_backbone_check':True,'history':history,'gpu_contended':True,'test_evaluated':False}
    (outdir/'result.json').write_text(json.dumps(report,indent=2))
    del model,optimizer,trainable,state;gc.collect();torch.cuda.empty_cache()
    return report

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');parser.add_argument('--epochs',type=int,default=4);parser.add_argument('--per-class',type=int,default=20);parser.add_argument('--batch',type=int,default=16);parser.add_argument('--seed',type=int,default=42);parser.add_argument('--output',default='pilot-r01');args=parser.parse_args()
    lock=open(ROOT/'training.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    torch.set_num_threads(4);torch.cuda.set_per_process_memory_fraction(.30);torch.backends.cuda.matmul.allow_tf32=True
    out=ROOT/'runs'/args.output;out.mkdir(parents=True,exist_ok=True)
    tok=AutoTokenizer.from_pretrained(ROOT/'model',local_files_only=True);tok.pad_token=tok.eos_token;tok.padding_side='right'
    train,val,cats,stats=prepare(args.seed,args.per_class)
    (out/'splits.json').write_text(json.dumps({'train':train,'validation':val,'categories':cats,'statistics':stats},indent=2))
    (out/'config.json').write_text(json.dumps(vars(args),indent=2))
    train=tokenized(train,tok);val=tokenized(val,tok)
    if args.smoke:train=train[:64];val=val[:64]
    results=[]
    for method in ['frozen','lora','engram']:
        for lr in ([1e-3] if args.smoke else [3e-4,1e-3]):
            trial=out/f'{method}-lr{lr}';trial.mkdir(exist_ok=True)
            if (trial/'result.json').exists():result=json.loads((trial/'result.json').read_text())
            else:result=train_one(args,method,lr,train,val,tok,trial)
            results.append(result);(out/'summary.json').write_text(json.dumps(results,indent=2))
    if args.smoke:print('SMOKE PASSED',flush=True);return
    # Only after all validation-based selections: open the held-out test set.
    label={c:i for i,c in enumerate(cats)}
    test=[{'text':r['text'],'label':label[r['category']]} for r in csv.DictReader((ROOT/'data/banking77/test.csv').open())]
    testloader=loaders(tokenized(test,tok),tok,64,False,args.seed);final=[]
    for method in ['frozen','lora','engram']:
        chosen=max([r for r in results if r['method']==method],key=lambda r:r['best_validation_accuracy'])
        model=Classifier(method,args.seed).cuda();trial=out/f'{method}-lr{chosen["lr"]}'
        model.load_artifact(torch.load(trial/'adapter.pt',weights_only=True));score=evaluate(model,testloader)
        (trial/'test-predictions.json').write_text(json.dumps(score.pop('predictions')))
        final.append(dict(method=method,chosen_lr=chosen['lr'],test=score,trainable_parameters=chosen['trainable_parameters'],peak_allocated_mb=chosen['peak_allocated_mb'],artifact_bytes=chosen['artifact_bytes'],training_wall_seconds=chosen['training_wall_seconds']))
        del model;gc.collect();torch.cuda.empty_cache()
    (out/'final-results.json').write_text(json.dumps(final,indent=2));print('FINAL',json.dumps(final),flush=True)

if __name__=='__main__':main()
