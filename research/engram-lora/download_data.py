"""Download the exact model and data used in the recorded experiment."""
from pathlib import Path
import hashlib, json, urllib.request
from huggingface_hub import snapshot_download
ROOT=Path(__file__).resolve().parent
model_revision='93efa2f097d58c2a74874c7e644dbc9b0cee75a2'
snapshot_download('HuggingFaceTB/SmolLM2-135M',revision=model_revision,local_dir=ROOT/'model',allow_patterns=['*.json','*.safetensors','*.txt','*.model','*.jinja','README.md','LICENSE*'])
rev='57ec275d8078af65b7731c2a98be812d844a6d6b'
dest=ROOT/'data/banking77';dest.mkdir(parents=True,exist_ok=True)
hashes={}
for name in ['train.csv','test.csv','categories.json']:
    url=f'https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/{rev}/banking_data/{name}'
    raw=urllib.request.urlopen(url).read();(dest/name).write_bytes(raw);hashes[name]=hashlib.sha256(raw).hexdigest()
(dest/'source.json').write_text(json.dumps(dict(revision=rev,sha256=hashes),indent=2))
snapshot_download('Salesforce/wikitext',repo_type='dataset',revision='b08601e04326c79dfdd32d625aee71d232d685c3',local_dir=ROOT/'data/wikitext2',allow_patterns=['wikitext-2-raw-v1/*.parquet','README.md','LICENSE*'])
print('Pinned model and datasets downloaded beside the experiment scripts.')
