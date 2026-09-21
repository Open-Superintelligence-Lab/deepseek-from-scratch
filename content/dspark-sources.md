# DSpark lesson sources and scope

## Primary source

- DeepSeek-AI, *DeepSeek-V4.1-Flash: Pushing the Limits of KV Cache Compression*, §2.4.3 “DSpark”, https://arxiv.org/html/2609.19969v1#S2.SS4.SSS3 (archived locally at `/Users/vukrosic/my-life/open-discovery-workspace/deepseek-v4-1-architecture-course/sources/report.txt`).

The report specifies: three Transformer drafter blocks; a 128-token sliding attention window; base logits for five draft positions in one pass; a lightweight Markov head for draft-token dependencies; a confidence head that predicts per-position conditional acceptance probabilities; estimated prefix survival; and a scheduler that combines estimates with profiled engine-throughput curves to choose a verification length dynamically under current load. It also specifies the training boundary: DSpark is trained alone after backbone pre-training with the backbone frozen; during post-training it trains alongside the backbone, while DSpark-objective gradients do not enter the backbone.

## Released reference implementation

- `sources/inference-model.py`, DSparkAttention, DSparkMarkovHead, DSparkConfidenceHead, DSparkBlock, and `forward_spec` in the same archived course source folder.
- `sources/inference-README.md` says this is a readable reference and that generation itself is plain autoregressive sampling.

The reference supports the lesson’s structural claims: draft input uses a block-size configuration, the first draft position receives the input ID while remaining positions receive a noise token, the Markov head samples a proposal sequence and contributes embeddings, and the confidence head consumes draft hidden states plus those embeddings. It does not implement the production serving scheduler or establish its throughput.

## Teaching calculations and boundaries

The browser widget uses five invented conditional values. It computes prefix survival with the pedagogical product `S_j = product(a_1 ... a_j)`, expected accepted draft tokens `E[A_L] = sum_{j=1..L} S_j`, and an explicitly invented cost `C_L = 1 + 0.45L` arbitrary units. It ranks `E[A_L] / C_L`. Expected accepted draft tokens exclude correction tokens and any bonus token after rejection. This is not an extracted DeepSeek scheduler, an engine profile, a measured acceptance rate, or a measured token throughput result.

The fixed-word comparison is only a deterministic shared-prefix visualization. It is explicitly not a sampling-distribution-preserving speculative-decoding implementation: it contains neither target and draft probabilities, acceptance ratios, rejection correction, target sampling, nor KV/RNG state management. The lesson therefore does not claim an exact output distribution, a five-times speedup, or that confidence equals actual target verification.
