"""Compose editable lesson fragments into a portable static page. No dependencies."""
from pathlib import Path
import re,os,tempfile,argparse,json
ROOT=Path(__file__).resolve().parent
INCLUDE=re.compile(r'<!-- include: ([a-zA-Z0-9_./-]+) -->')
def compose(root=ROOT):
 root=Path(root).resolve()
 def expand(path,stack=()):
  path=path.resolve()
  if not path.is_relative_to(root):raise ValueError('Include outside course directory')
  if path in stack:raise ValueError('Circular include: '+str(path))
  return INCLUDE.sub(lambda m:expand(root/m[1],stack+(path,)),path.read_text())
 text=expand(root/'index.template.html')
 ids=re.findall(r'data-edit-id="([^"]+)"',text)
 if len(ids)!=len(set(ids)):raise ValueError('Duplicate editable text IDs')
 store=root/'content/text-edits.json'
 if store.exists():
  unknown=set(json.loads(store.read_text()).get('edits',{}))-set(ids)
  if unknown:raise ValueError('Saved text would be orphaned: '+', '.join(sorted(unknown)))
 return text

def build(root=ROOT):
 root=Path(root);text=compose(root);out=root/'index.html'
 if not out.exists() or out.read_text()!=text:
  fd,name=tempfile.mkstemp(dir=root,prefix='.course-')
  with os.fdopen(fd,'w') as f:f.write(text)
  os.replace(name,out)
 return text

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
 if a.check:
  assert (ROOT/'index.html').read_text()==compose(),'Generated page is stale; run python3 build_course.py'
  print('Course page matches its lesson sources; editable IDs and saved edits valid.')
 else:
  text=build();print(f'Built index.html from {len(list((ROOT/"lessons").glob("*.html")))} lesson files.')
