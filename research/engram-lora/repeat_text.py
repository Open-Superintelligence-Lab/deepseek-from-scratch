"""Two additional preplanned seeds; trials still select only on validation."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parent
for seed in [43,44]:
 subprocess.run([sys.executable,'-u',str(root/'train_text.py'),'--seed',str(seed),'--output',f'text-seed{seed}-r01'],check=True)
