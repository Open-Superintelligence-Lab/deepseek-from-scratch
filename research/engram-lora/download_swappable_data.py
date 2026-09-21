"""Download pinned public data directly on the training machine. Does not execute dataset code."""
from pathlib import Path
from huggingface_hub import snapshot_download

root=Path(__file__).resolve().parent/'data'
for repo,revision,folder,patterns in [
    ('BeIR/fiqa','979c07a7cb5ccc6ca009792241fa1250b98055dd','fiqa',['corpus/*.parquet','README.md']),
    ('code-search-net/code_search_net','bd0cf261e357a3eb5c8fba490d23ec1a1cd59555','codesearchnet',['ruby/*.parquet','README.md']),
]:
    snapshot_download(repo,repo_type='dataset',revision=revision,local_dir=root/folder,allow_patterns=patterns)
