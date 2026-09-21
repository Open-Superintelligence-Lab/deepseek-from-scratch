# Model-information lesson: source grounding

Primary source: DeepSeek-AI, *DeepSeek-V4.1-Flash Technical Report* (2026), local course copy at `/Users/vukrosic/my-life/open-discovery-workspace/deepseek-v4-1-architecture-course/sources/report.txt` and the official model-repository PDF: <https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/main/DeepSeek_V41_Tech_Report.pdf>.

| Lesson claim | Report grounding |
| --- | --- |
| V4.1-Flash has a 20-layer causal encoder followed by a 20-layer decoder. | §2.1, Figure 3; §4 configuration. |
| Decoder global KV is projected from the final encoder hidden state with decoder-layer-dependent projections. | §2.2, Eq. (1). The report names the final encoder state `H_(L/2)` and explains that upper-layer KV is not derived from each decoder layer’s own hidden state. |
| Local SWA KV is produced layer by layer from the current layer state. | §2.2. |
| CSA2 shares global KV and indexer K across selected layers; each layer retains its own global Q and SWA KV. | §2.3.1 and Figure 4. |
| Engram is a conditional memory module using tokenizer compression, multi-head hashing, context-aware gating, and multi-branch integration; the report places two modules at layers 1 and 14 (zero-indexed). | §2.4.2. |
| Decoder SWA bounded replay is separate from global KV and is used only for decoding, not prefix caching. | §3.2.2, “Decoder SWA Bounded Replay.” |
| The released inference implementation does not add a position-embedding vector at token lookup; it applies rotary positional encoding in attention. | Official `inference/model.py`, `apply_rotary_emb` and attention projections. |

The three-token walkthrough, labels, and card states are illustrative instructional diagrams. They are not a trace from released model weights, an exact tokenizer output, or a claim about the semantic contents of an individual tensor.
