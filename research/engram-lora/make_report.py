"""Render small downloaded metric files; no weights or datasets needed locally."""
from pathlib import Path
import json,html
p=Path(__file__).parent
sections=[]
for name,title in [('pilot-r01','Small data: 20 examples per intent'),('banking-full-r01','All available training examples')]:
    f=p/'results'/name/'final-results.json'
    if not f.exists():continue
    rows=json.loads(f.read_text());summary=json.loads((f.parent/'summary.json').read_text())
    labels={'frozen':'Frozen model + classifier','lora':'LoRA + classifier','engram':'Engram + classifier'}
    body=''
    for r in rows:
        acc=r['test']['accuracy']*100
        body+=f'<tr><td>{labels[r["method"]]}</td><td><strong>{acc:.2f}%</strong><div class="bar" style="width:{acc}%"></div></td><td>{r["trainable_parameters"]:,}</td><td>{r["peak_allocated_mb"]:.0f} MB</td><td>{r["artifact_bytes"]/1e6:.2f} MB</td></tr>'
    curves=''
    for method in ['frozen','lora','engram']:
        r=max([x for x in summary if x['method']==method],key=lambda x:x['best_validation_accuracy'])
        points=' → '.join(f'{x["val"]["accuracy"]*100:.1f}%' for x in r['history'])
        curves+=f'<p><b>{labels[method]}</b><br>Validation by epoch: {points}<br><small>Selected learning rate: {r["lr"]}; saved module reload verified.</small></p>'
    extra=''
    analysis=f.parent/'analysis.json'
    if analysis.exists():
        a=json.loads(analysis.read_text());ab=a['engram_ablations']
        extra+='<h3>Does the trained memory matter?</h3><table><tr><th>Engram condition</th><th>Test accuracy</th></tr>'
        for key,label in [('restored','Trained module'),('shuffled_rows_same_reader','Same reader, randomly rearranged memory rows'),('disabled_with_same_trained_classifier','Module disabled, same trained classifier')]:
            extra+=f'<tr><td>{label}</td><td>{ab[key]["accuracy"]*100:.2f}%</td></tr>'
        extra+='</table><p>Rearranging rows breaks the mapping between a token group and its learned vector. This is a diagnostic, not a separately retrained competing model.</p>'
        extra+='<h3>How much do familiar token patterns help?</h3><table><tr><th>Method</th><th>Low overlap</th><th>Medium overlap</th><th>High overlap</th></tr>'
        for key,r in a['methods'].items():
            extra+=f'<tr><td>{labels[key]}</td>'+''.join(f'<td>{x["accuracy"]*100:.1f}% <small>(n={x["n"]})</small></td>' for x in r['overlap_buckets'])+'</tr>'
        extra+='</table><p>Overlap is the fraction of input token pairs/triples seen at least twice in training. Bins: below one third, one to two thirds, and at least two thirds. These are observational groups, not a controlled causal test.</p>'
        extra+=f'<small>Exact normalized train/test query overlap: {a["exact_train_test_overlap"]}. Duplicate-excluded accuracy is saved in analysis.json.</small>'
    sections.append(f'<section><h2>{title}</h2><p>Test: 3,080 previously held-out BANKING77 queries · 77 intents</p><table><thead><tr><th>Method</th><th>Test accuracy</th><th>Trainable parameters</th><th>Peak allocated VRAM</th><th>Saved module</th></tr></thead><tbody>{body}</tbody></table><details><summary>Learning curves and settings</summary>{curves}</details>{extra}</section>')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Engram vs LoRA — first experiment</title><style>
body{background:#171717;color:#ecebe5;font:18px/1.6 system-ui;margin:0}main{max-width:1160px;margin:60px auto;padding:0 30px}h1{font-size:46px;line-height:1.15;max-width:850px}h2{font-size:26px}p{max-width:950px;color:#bdbdb5}section{margin:42px 0;padding:28px;background:#22221f;border:1px solid #414139;border-radius:12px}table{width:100%;border-collapse:collapse;font-size:16px}th,td{text-align:left;padding:16px 10px;border-bottom:1px solid #45453b}th{color:#aaa;font-size:13px}.bar{height:5px;background:#cfb775;margin-top:8px}strong{font-size:24px;color:#f0d78c}small{color:#a4a49c}details{margin-top:24px}summary{cursor:pointer;color:#d1ba7c}a{color:#d1ba7c}.tag{font-size:13px;letter-spacing:2px;color:#d1ba7c}.note{border-left:3px solid #c8ad63;padding-left:20px}</style><main><div class="tag">REAL DATA · FROZEN SMOLLM2-135M</div><h1>Can a trainable memory module compete with LoRA?</h1><p>One pretrained checkpoint. A shared classifier design. An Engram-inspired module with hashed 2/3-gram lookups, a context gate, and causal convolution, compared with rank-8 LoRA on query/value projections.</p>'''
page+=''.join(sections)
page+='''<section><h2>What this experiment establishes</h2><p>We train and evaluate real task adapters on BANKING77. The base model stays frozen; classifier-only adaptation is the baseline. Each method gets two learning-rate trials and four epochs; validation chooses the learning rate and checkpoint. Trainable adapter budgets differ by less than 0.1%.</p><p class="note">One seed and one dataset so far. These are preliminary classification results, not proof of general reasoning, factual-memory portability, or superiority across tasks. The GPU had another workload, so timings are not clean throughput benchmarks. SST-2 and WikiText-2 are downloaded but not trained in this report.</p><p>Saved artifacts contain the task head and trained adapter; no base-model copy. Model and dataset source revisions are recorded. Engram uses raw token IDs and one insertion layer; this is an adaptation study, not an exact DeepSeek reproduction.</p><a href="https://github.com/PolyAI-LDN/task-specific-datasets">BANKING77 source</a> · <a href="https://github.com/deepseek-ai/Engram">Engram source</a></section></main></html>'''
(p/'report.html').write_text(page)
print(p/'report.html')
