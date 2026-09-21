# Expert routing: source register and claim boundaries

## Primary local sources consulted

1. `../../../../open-discovery-workspace/deepseek-v4-1-architecture-course/sources/report.txt`, [DeepSeek-V4.1-Flash technical report](https://arxiv.org/html/2609.19969v1), §2.1 and §4.2.1 (saved local copy).
   - §2.1 says V4.1-Flash retains shared and fine-grained routed experts from DeepSeekMoE.
   - §2.1.1 says text and image tokens can have distinct routing preferences; it describes separate correction biases for selection by modality, while original routing scores weight selected outputs.
   - §4.2.1 states that each MoE layer has 1 shared expert and 384 routed experts, with 6 routed experts activated per token. It also reports 552B backbone parameters and 8B / 16B activated parameters per token for prefill / decode at the whole-model level.

2. `../../../../open-discovery-workspace/deepseek-v4-1-architecture-course/sources/inference-model.py`, saved official reference implementation.
   - `Gate.forward` selects `topk` from `scores + bias`, gathers weights from the unbiased `scores`, optionally normalizes selected top-k weights, then applies `route_scale`.
   - `MoE.forward` accumulates selected routed `Expert` outputs and adds `shared_experts(x)` for every token.
   - Its small runnable defaults are explicitly a teaching-scale model (`8` routed, `2` active) and must not be reported as released V4.1 dimensions.

3. Dai et al., *DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models* (2024), cited by the V4.1 report for the shared and fine-grained routed-expert design: https://arxiv.org/abs/2401.06066

## Boundaries used in this lesson

- “Expert” means a learned feed-forward network. No claim is made that any deployed expert has a fixed human-readable domain.
- The four-expert, top-2 interactive calculator uses fixed scores and two-dimensional outputs created only to show the arithmetic. Its normalized weights are an explicit toy convention, not a measurement or a claim about every V4.1 configuration.
- Sparse activation reduces the amount of routed-expert computation attempted per token. It does not by itself establish end-to-end latency, which also depends on routing balance, batching, kernels, device placement, memory traffic and communication.
- The 8B and 16B figures belong to the report's whole architecture and its stated prefill/decode modes. They are not inferred from the one-layer 1-shared + 384-routed configuration.
