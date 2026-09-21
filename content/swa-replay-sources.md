# SWA Bounded Replay: sources and claim boundaries

Primary source: DeepSeek-AI, *DeepSeek-V4.1-Flash: Pushing the Limits of KV Cache Compression*, technical report, §2.2 (Causal Encoder-Decoder), §3.2.1 (Persistent KV Cache Management), §3.2.2 (SWA Bounded Replay), and §6 (limitations). Local source inspected for this lesson: `/Users/vukrosic/my-life/open-discovery-workspace/deepseek-v4-1-architecture-course/sources/report.txt`. Public HTML: https://arxiv.org/html/2609.19969v1#S2.SS2 and https://arxiv.org/html/2609.19969v1#S3.SS2.

## Reported mechanism

- V4.1 removes SWA KV from the persistent cache. Global KV remains persistent with a reported guaranteed lifetime of at least 72 hours; short-lived SWA KV uses a distributed host-DRAM pool with a minutes-scale TTL (§3.2.1).
- On a global-KV hit with missing encoder SWA KV, Encoder SWA Bounded Replay replays the last `n_win` cached-prefix tokens with the uncached suffix. Replayed tokens regenerate only SWA KV and reuse cached global KV without recomputing or overwriting it; the new suffix generates both (§3.2.2).
- Exact reconstruction of SWA KV for `L` layers requires replaying `L × n_win` tokens. Bounded replay uses only `n_win` and truncates local attention at the replay start, so it is approximate (§3.2.2).
- CED obtains decoder global KV by projecting final encoder hidden states, but decoder SWA KV comes from each decoder layer’s own hidden states. Decoder bounded replay runs the last `n_win` prompt-token encoder outputs through decoder layers to create SWA KV for decoding, not prefix caching (§2.2, §3.2.2).
- The authors report negligible response-quality impact in their experiments. This is an author-reported experimental finding, not a universal quality or correctness guarantee. The report says approximate state reconstruction may still cause degradation in untested boundary cases (§3.2.2, §6).

## Interactive model scope

The browser widget’s eight positions, four local layers, selectable 1–4-position segment, labels, and arithmetic such as `4 × 3 = 12` are invented teaching values. They illustrate the report’s dependency accounting and do not state V4.1 layer counts, window sizes, cache layout, request timing, throughput, hit rate, storage bytes, or quality. It does not execute attention or model inference. In the toy, the theoretical stacked span is `L × n_win`, while the exact replay used is `min(prefix length, L × n_win)`; a prefix shorter than that span can be replayed in full. Neither count is a measured token count for a deployed request.
