"""Diagnostic: swap only independently trained tables, keeping the other reader.
No retraining or test-based selection. Whole-module controls are in final-results.json.
"""
import fcntl,json,time
import torch
from swappable import ROOT,OUT,Model,evaluate,clean,write

def main():
    lock=open(ROOT/'training.lock','w');fcntl.flock(lock,fcntl.LOCK_EX)
    torch.set_num_threads(4);torch.cuda.set_per_process_memory_fraction(.18)
    data=torch.load(OUT/'data.pt',weights_only=True)
    selected=json.loads((OUT/'selected.json').read_text());records=[]
    for method in ['engram-small','engram-large']:
        model=Model(method,42).cuda();model.eval()
        states={d:torch.load(OUT/selected[f'{d}:{method}:42']['artifact'],weights_only=True)
                for d in ['finance','code']}
        for reader,tables in [('finance','code'),('code','finance')]:
            hybrid={k:(states[tables][k] if k.startswith('adapter.tables.') else v)
                    for k,v in states[reader].items()}
            model.restore(hybrid)
            rec=dict(method=method,seed=42,reader_from=reader,tables_from=tables,
                     evaluation={d:evaluate(model,data[d]['test']) for d in ['finance','code']})
            records.append(rec)
            print('TABLE_SWAP',method,reader,tables,{d:v['perplexity'] for d,v in rec['evaluation'].items()},flush=True)
        del model,states,hybrid;clean()
    write(OUT/'table-only-swaps.json',dict(scope='Diagnostic, seed42 only; no shared-reader training',records=records))

if __name__=='__main__':main()
