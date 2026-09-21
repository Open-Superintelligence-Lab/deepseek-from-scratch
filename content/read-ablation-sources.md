# Source notes — reading the V4.1-Flash bundled result

## Source and exact scope

Primary source: DeepSeek-AI, *DeepSeek-V4.1-Flash: Pushing the Limits of KV Cache Compression*, local copy at `/Users/vukrosic/my-life/open-discovery-workspace/deepseek-v4-1-architecture-course/sources/DeepSeek_V41_Tech_Report.pdf`.

The lesson uses **§4.3.2 and Table 1, PDF pp. 23–24**. The report calls this a comparison among DeepSeek-V4-Flash-Base, DeepSeek-V4-Pro-Base, and DeepSeek-V4.1-Flash-Base. It says all models are evaluated in its internal framework and share the same evaluation setting. This is a model comparison, **not an isolated architecture ablation**.

## Exact selected Table 1 values

| Row | DeepSeek-V4-Flash-Base | DeepSeek-V4.1-Flash-Base |
| --- | ---: | ---: |
| Activated parameters | 13B | 8B / 16B |
| MMLU-Pro (EM), 5-shot | 68.3 | 74.1 |
| BigCodeBench (Pass@1), 3-shot | 56.8 | 60.6 |
| HumanEval (Pass@1), 0-shot | 69.5 | 79.4 |
| MATH (EM), 4-shot | 57.4 | 61.1 |
| MGSM (EM), 8-shot | 85.7 | 80.2 |
| LongBench-V2 (EM), 1-shot | 44.7 | 45.2 |

Table 1 says a score gap no greater than 0.3 is considered the same level. Its 8B / 16B notation is explained in the report’s architecture discussion: V4.1-Flash activates 8B parameters per token during prefill and 16B during decode.

## What the table does and does not identify

The report’s §4.3.2 says V4.1-Flash has a reduced KV cache and different activated-parameter profile while showing competitive scores. It also explicitly attributes results in part to substantial pre-training data-curation improvements and says the version introduces native multimodal training. Table 1 therefore bundles changes in architecture, size, data, and training. It cannot identify a contribution from CED, CSA2, FP4 main-KV caching, Engram, or any other one component.

The report does not state seed counts, standard deviations, confidence intervals, or per-run results for Table 1. It is an internal evaluation framework. These are limits on causal and external-generalization claims.

## Why not call the FP4 or bounded-replay claims an ablation?

- PDF p. 14, §2.4.4 says quantizing before RoPE yields only a marginal accuracy improvement and omitting a global scale causes no measurable decrease in accuracy.
- PDF p. 20, §3.2.2 says SWA Bounded Replay has negligible impact / barely compromises response quality.

Those are qualitative claims in the report. No numerical controlled row table is supplied that would permit a faithful one-change ablation lesson. The proposed follow-up in the lesson is deliberately a future matched FP4-versus-FP8 experiment, not a claim that the course ran it.
