"""Fetch the small benchmark files directly onto the experiment server."""
from pathlib import Path
import json
from huggingface_hub import HfApi,snapshot_download
root=Path(__file__).resolve().parent/'data'
for repo,folder,prefix in [('stanfordnlp/sst2','sst2',''),('Salesforce/wikitext','wikitext2','wikitext-2-raw-v1/')]:
    info=HfApi().dataset_info(repo,files_metadata=True)
    files=[s.rfilename for s in info.siblings if s.rfilename.endswith('.parquet') and s.rfilename.startswith(prefix)]
    if not files: raise RuntimeError(f'No expected files in {repo}')
    dest=root/folder
    snapshot_download(repo,repo_type='dataset',revision=info.sha,local_dir=dest,allow_patterns=files+['README.md','LICENSE*'])
    record={'repo':repo,'revision':info.sha,'files':files,'subset':prefix,'downloaded_on_server':True}
    (dest/'source.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record),flush=True)
