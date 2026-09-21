# Single-Pass mHC lesson sources and scope

## Primary source

DeepSeek-AI, *DeepSeek-V4.1-Flash: Pushing the Limits of KV Cache Compression*, §2.4.1 “Single-Pass mHC,” PDF pp. 12–13 / official HTML section: https://arxiv.org/html/2609.19969v1#S2.SS4.SSS1

The local course archive used for wording and equation checks is `/Users/vukrosic/my-life/open-discovery-workspace/deepseek-v4-1-architecture-course/sources/report.txt`, pp. 12–13.

## Claims used in the lesson

- Original mHC maintains `n` residual streams `X_l ∈ R^(n×d)` between adjacent Transformer blocks. Its predictor `H(X_l)` produces token-wise `A_l ∈ R^(1×n)`, `B_l ∈ R^(n×n)`, and `C_l ∈ R^(n×1)`.
- The report’s original formula is `X_(l+1) = B_l X_l + C_l F_l(A_l X_l)`. Its implementation stages residual update, coefficient prediction, and input mixing because current `A_l` depends on a hidden-dimension reduction over `X_l`.
- The report gives a lower bound of `(2n + 2)d` activation-memory traffic. Its original multi-pass implementation is `(4n + 4)d` including the pre-norm in `F_l`; a two-pass fusion is `(3n + 2)d` because it still rereads `X_l` for input mixing.
- Single-Pass mHC consumes `A_(l-1)` for the current input: `X_(l+1) = B_l X_l + C_l F_l(A_(l-1) X_l)`, while `H(X_l)` still produces the current `A_l`, `B_l`, and `C_l`. The report says the shift incurs negligible performance degradation empirically.
- For deployment, Mega-mHC fuses residual update, input mixing, and coefficient prediction. The report says it uses `(2n + 2)d`, reaches the ideal-map read/write count, and halves activation-memory traffic relative to its original implementation.

## Teaching-widget boundary

The walkthrough uses two streams and two hidden-dimension tiles solely to show a reduction dependency. It is not a numerical simulation of mHC, an implementation of DeepSeek’s predictor or Mega-mHC kernel, a training run, an ablation, or a throughput measurement. “Halves” refers specifically to the reported activation-traffic comparison `(4n + 4)d → (2n + 2)d`; it is not an end-to-end latency, FLOP, or quality claim.
