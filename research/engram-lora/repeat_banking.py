"""Finish the two additional full-data classifier seeds sequentially."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parent
for seed in [43,44]:
 subprocess.run([sys.executable,'-u',str(root/'train_banking.py'),'--wait-lock','--seed',str(seed),'--output',f'banking-full-seed{seed}-r01','--per-class','0','--batch','32','--epochs','4'],check=True)
