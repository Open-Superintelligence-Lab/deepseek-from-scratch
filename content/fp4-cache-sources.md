# FP4 cache lesson sources and scope

Primary: DeepSeek-V4.1-Flash technical report §2.4.4, PDF page 14, https://arxiv.org/html/2609.19969v1#S2.SS4.SSS4
Local report and official inference-kernel.py used from the archived source folder.

The report specifies E2M1 with one E4M3 scale per 16 channels, no second-level global scale, quantization after RoPE, FP8 SWA cache, and quantization-aware post-training. Main cache storage is distinguished from arithmetic precision and indexer MXFP4.

Browser demonstration: scalar nearest-level rounding using E2M1 numerical levels, manually selected exact scales 0.5/1/2, signed-zero encodings merged. Ties choose lower numerical value. No implementation of actual scale selection, packing, training, hardware rounding, or full model inference. 16 × 4 bits + 8 scale bits = 72 bits = 9 bytes; raw FP8 value-only baseline 16 bytes excludes its metadata. This is arithmetic, not a measured model result.
