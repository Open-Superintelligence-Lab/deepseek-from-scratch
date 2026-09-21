"""Post-selection analysis: real token-pattern overlap and Engram memory ablations.
These evaluations do not feed back into hyperparameter selection.
"""
from pathlib import Path
from collections import Counter
import json,csv,torch,gc,fcntl
from train_banking import Classifier,loaders,tokenized
from transformers import AutoTokenizer
ROOT=Path(__file__).resolve().parent
def main():
    lock=open(ROOT/'training.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    torch.set_num_threads(4);torch.cuda.set_per_process_memory_fraction(.3)
    tok=AutoTokenizer.from_pretrained(ROOT/'model',local_files_only=True);tok.pad_token=tok.eos_token;tok.padding_side='right'
    for name in ['pilot-r01','banking-full-r01']:
        p=ROOT/'runs'/name;splits=json.loads((p/'splits.json').read_text());final=json.loads((p/'final-results.json').read_text())
        cats=splits['categories'];label={c:i for i,c in enumerate(cats)}
        test=[{'text':r['text'],'label':label[r['category']]} for r in csv.DictReader((ROOT/'data/banking77/test.csv').open())]
        def grams(text):
            ids=tok(text,truncation=True,max_length=96)['input_ids']
            return [tuple(ids[i:i+n]) for n in [2,3] for i in range(len(ids)-n+1)]
        counts=Counter(g for r in splits['train'] for g in grams(r['text']))
        buckets=[]
        for r in test:
            gs=grams(r['text']);fraction=sum(counts[g]>=2 for g in gs)/max(1,len(gs))
            buckets.append(0 if fraction<1/3 else 1 if fraction<2/3 else 2)
        norms={' '.join(r['text'].lower().split()) for r in splits['train']}
        novel=[i for i,r in enumerate(test) if ' '.join(r['text'].lower().split()) not in norms]
        report={'overlap_definition':'Fraction of token 2/3-grams observed at least twice in training; bins <1/3, [1/3,2/3), >=2/3','exact_train_test_overlap':len(test)-len(novel),'methods':{}}
        for r in final:
            trial=p/f'{r["method"]}-lr{r["chosen_lr"]}'
            preds=json.loads((trial/'test-predictions.json').read_text());results=[]
            for bucket in range(3):
                selected=[i for i,b in enumerate(buckets) if b==bucket]
                results.append({'bucket':bucket,'n':len(selected),'accuracy':sum(preds[i]==test[i]['label'] for i in selected)/max(1,len(selected))})
            report['methods'][r['method']]={'overlap_buckets':results,'accuracy_excluding_exact_training_duplicates':sum(preds[i]==test[i]['label'] for i in novel)/len(novel)}
        from train_banking import evaluate
        chosen=next(r for r in final if r['method']=='engram');trial=p/f'engram-lr{chosen["chosen_lr"]}'
        model=Classifier('engram',42).cuda();model.load_artifact(torch.load(trial/'adapter.pt',weights_only=True))
        loader=loaders(tokenized(test,tok),tok,64,False,42)
        ablations={}
        model.adapter.enabled=False
        score=evaluate(model,loader);score.pop('predictions');ablations['disabled_with_same_trained_classifier']=score
        model.adapter.enabled=True
        saved=[x.weight.detach().clone() for x in model.adapter.tables]
        with torch.no_grad():
            for table in model.adapter.tables:
                g=torch.Generator(device='cuda').manual_seed(101)
                table.weight.copy_(table.weight[torch.randperm(table.num_embeddings,generator=g,device='cuda')].clone())
        score=evaluate(model,loader);score.pop('predictions');ablations['shuffled_rows_same_reader']=score
        with torch.no_grad():
            for table,original in zip(model.adapter.tables,saved):table.weight.copy_(original)
        score=evaluate(model,loader);preds=score.pop('predictions')
        expected=json.loads((trial/'test-predictions.json').read_text());assert preds==expected,'Restored adapter predictions changed'
        ablations['restored']=score;report['engram_ablations']=ablations
        (p/'analysis.json').write_text(json.dumps(report,indent=2));print(name,json.dumps(report),flush=True)
        del model,saved;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':main()
