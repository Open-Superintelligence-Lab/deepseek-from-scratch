"""Render measured results, never illustrative or invented benchmark values."""
from pathlib import Path
import json, statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'charts';OUT.mkdir(exist_ok=True)
colors={'frozen':'#90969e','engram':'#edbd6b','lora':'#73cfb5'}
plt.rcParams.update({'figure.facecolor':'#151719','axes.facecolor':'#151719','savefig.facecolor':'#151719','text.color':'#efeeea','axes.labelcolor':'#c7c9cc','xtick.color':'#c7c9cc','ytick.color':'#c7c9cc','font.family':'DejaVu Sans','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#53585f'})
def load(name):return json.loads((ROOT/'results'/name/'final-results.json').read_text())
methods=['frozen','engram','lora'];labels=['Baseline','N-gram memory','LoRA']
fig,axs=plt.subplots(1,2,figsize=(15,7));fig.subplots_adjust(left=.07,right=.97,bottom=.21,top=.76,wspace=.3)
fig.text(.07,.94,'Does n-gram memory help a frozen language model?',fontsize=24,weight='bold')
fig.text(.07,.87,'Measured SmolLM2-135M results | Similar adapter budgets (~460k parameters)',color='#b3b7bd',fontsize=13)
ax=axs[0];x=np.arange(2);width=.23
for i,m in enumerate(methods):
    ys=[next(r['test']['accuracy']*100 for r in load(run) if r['method']==m) for run in ['pilot-r01','banking-full-r01']]
    bars=ax.bar(x+(i-1)*width,ys,width,color=colors[m],label=labels[i])
    ax.bar_label(bars,labels=[f'{y:.1f}%' for y in ys],fontsize=11,padding=5,color=colors[m])
ax.set(ylim=(0,105),xticks=x,xticklabels=['1,540 train examples','9,229 train examples'],ylabel='Test accuracy (%) · higher is better')
ax.set_title('Classify banking questions',loc='left',pad=18,weight='bold');ax.yaxis.grid(True,alpha=.1);ax.set_axisbelow(True)
fig.legend(*ax.get_legend_handles_labels(),frameon=False,loc='lower left',bbox_to_anchor=(.065,.125),ncol=3,fontsize=10)
ax=axs[1]
runs=[load(n) for n in ['text-pilot-r01','text-seed43-r01','text-seed44-r01']]
values=[[next(r['test']['perplexity'] for r in rows if r['method']==m) for rows in runs] for m in methods]
means=[statistics.mean(v) for v in values];sds=[statistics.stdev(v) for v in values]
bars=ax.bar(np.arange(3),means,color=[colors[m] for m in methods],width=.6,yerr=sds,capsize=5,error_kw={'ecolor':'#ffffff','elinewidth':1.4})
ax.bar_label(bars,labels=[f'{y:.2f}' for y in means],padding=10,fontsize=14,color='#efeeea')
ax.set(ylim=(0,38),xticks=range(3),xticklabels=labels,ylabel='Test perplexity · lower is better')
ax.set_title('Predict unseen WikiText passages',loc='left',pad=18,weight='bold');ax.yaxis.grid(True,alpha=.1);ax.set_axisbelow(True)
fig.text(.07,.095,'Classification: one seed, 3,080 test questions. Text: 3 seeds, mean ± sample SD; 32,640 scored tokens.',fontsize=11,color='#b3b7bd')
fig.text(.07,.05,'Small-data pilot, not a full WikiText benchmark. Better perplexity does not establish factual or chatbot quality.',fontsize=11,color='#b3b7bd')
for ext in ['png','svg']:fig.savefig(OUT/f'comparison.{ext}',dpi=170)
plt.close(fig)

a=json.loads((ROOT/'results/banking-full-r01/analysis.json').read_text())['engram_ablations']
fig,ax=plt.subplots(figsize=(12,6));fig.subplots_adjust(left=.30,right=.91,top=.72,bottom=.23)
fig.text(.07,.92,'Does the trained memory actually contribute?',fontsize=23,weight='bold')
fig.text(.07,.84,'Same trained classifier in all three conditions | Larger BANKING77 run',fontsize=13,color='#b3b7bd')
keys=['restored','shuffled_rows_same_reader','disabled_with_same_trained_classifier']
names=['Trained memory','Memory rows shuffled','Memory adapter disabled']
ys=[a[k]['accuracy']*100 for k in keys]
bars=ax.barh(range(3),ys,color=['#edbd6b','#939ba6','#606874'],height=.55)
ax.bar_label(bars,labels=[f'{y:.2f}%' for y in ys],padding=10,fontsize=14,color='#efeeea')
ax.set(yticks=range(3),yticklabels=names,xlim=(0,100),xlabel='Test accuracy (%) · higher is better');ax.invert_yaxis();ax.xaxis.grid(True,alpha=.1);ax.set_axisbelow(True)
fig.text(.07,.10,'Breaking the lookup mapping hurts performance. The module is doing useful work.',fontsize=13,color='#edbd6b')
fig.text(.07,.045,'Diagnostic only: disabling the module keeps the head trained with it. It is not the separately trained baseline.',fontsize=10.5,color='#b3b7bd')
for ext in ['png','svg']:fig.savefig(OUT/f'memory-check.{ext}',dpi=170)
print(OUT)
