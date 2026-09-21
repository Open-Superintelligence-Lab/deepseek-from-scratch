# Attention-designs lesson: source and claim ledger

## Primary report

- DeepSeek-AI, *DeepSeek-V4.1-Flash Technical Report*, §2.3 “Compressed Sparse Attention 2 (CSA2)”, §2.3.1 “Cross-Layer KV and Index Reuse”, Figure 4, and §2.3.2 “Hierarchical Sparse Indexer”, Figure 5. Local archival text used for this lesson: `/Users/vukrosic/my-life/open-discovery-workspace/deepseek-v4-1-architecture-course/sources/report.txt`.
- Official report PDF: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/main/DeepSeek_V41_Tech_Report.pdf
- Model card: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash

The report supports these statements:

1. CSA2 uses a main/global KV path plus a layer-local sliding-window-attention (SWA) KV path. For a fixed window, local SWA storage is bounded with respect to context length; global cache storage grows with context length.
2. Full mode produces main KV, indexer K, indexer Q, and a fresh Top-K selection. Reindex reuses main KV and indexer K but computes a new indexer query and new Top-K selection. Reuse keeps the main KV and latest compatible Top-K indices, skipping new index scoring. All modes compute their own main query and SWA KV.
3. CSA2 uses a lightweight indexer to select global entries; selected global entries are read with local SWA KV. A selected address is distinct from an attention weight or layer output.
4. The report configuration uses encoder CSA2 compression ratio 2 and decoder CSA2 compression ratio 1; it uses Top-512 global entries per query, a 128-token local window, and a hierarchical decoder candidate pool of up to 2,048 blocks × 8 positions.
5. The hierarchical candidate pool bounds later decoder Reindex searches, but the first Full-mode decoder layer still scores the causally visible global context.

## Released reference implementation

- Local source used: `/Users/vukrosic/my-life/open-discovery-workspace/deepseek-v4-1-architecture-course/sources/inference-model.py`.
- Public reference: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/main/inference/model.py

Relevant implementation checks:

- `Compressor` pools consecutive token representations with a learned softmax gate only when `compress_ratio > 1`; ratio 1 returns a normalized projection.
- `Attention._window_kv` creates a per-layer ring buffer for local-window KV; `_compress_kv` publishes a compressed/global cache only from a KV source layer.
- `Indexer` derives index keys from the latent cache; `SharedAttentionRuntime` transfers global compressed KV, index keys, Top-K indices, and candidate masks between source and consumer layers.

## Deliberate boundaries in this lesson

- All 8-position, 4-layer, 8-value, and byte counts are invented teaching arithmetic. They are labelled illustrative and are not V4.1 dimensions, cache bytes, measured quality, latency, or throughput.
- The lesson does not reuse the report’s 890 bytes/token figure because that accounting includes V4.1-specific precision, scale, and owner scheduling details. It should not be inferred from the toy counts.
- “Compress”, “share”, and “select” are separated as mechanism categories. They may co-occur in CSA2, but no causal quality or speed claim is made here.
- This is specifically a V4.1 CSA2 lesson. It does not assert that MLA, CSA, or other DeepSeek releases have the same cache layout or schedule.
