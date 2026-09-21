# V4.1 theory expansion review

Four written lessons integrated into the modular course on September 20: model-information, attention-designs, expert-routing, read-ablation. Main route is theory first; existing experiments remain available after theory. No new video or training run in this batch.

## Source review
- CED information flow checked against report §2.2; Engram stays inside configured encoder layers; local SWA KV distinguished from global projected memory. RoPE not described as added position embeddings.
- CSA2 checks against §2.3 and §4.2.1: toy design comparison does not pretend to be production byte accounting; independent tabs isolate compression (512 B), sharing (256 B), or selection (1024 B / 3 reads), against the same 1024 B / 8-read baseline.
- Expert configuration checked against §4.2.1 and official inference implementation: shared + routed expert distinction and selection bias versus original output scores. Toy vectors/weights labeled illustrative, full weighted sum shown.
- Table 1 subset checked against report PDF p24. Benchmark comparison is not labeled a one-change ablation. Follow-up inference precision study is proposed only.

## Verification
- Course build/check and existing four Python build tests passed.
- Existing Engram JS exercise regression checks passed.
- New JavaScript syntax checks passed.
- Browser verified prediction/reveal, encoder Engram walkthrough, attention sharing and selection, expert route changes and weighted vector output, and source table values.
- Narrow-layout review fixed nested aside/sidebar conflict and equation overflow; final browser console contains no errors.
- All existing saved author overrides preserved; approved yellow Engram introduction and video files unchanged.
