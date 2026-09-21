# Task construction source map

DeepSeek-V4.1-Flash §5.1 and §5.1.1, report PDF pages 25-26. Primary https://arxiv.org/html/2609.19969v1#S5.SS1.SSS1 . Local saved report independently checked.

Report-grounded: task triplets; difficulty/correctness; coding environment construction and isolation; fail-to-pass/pass-to-pass evaluation points; multiple solving agents; independent quality inspection; leakage removal; repair loop. Post-training recipe/data emphasis is limited to the described post-training pipeline, not proof architecture research is exhausted.

Original illustrative example: shipping(subtotal) domain nonnegative subtotals, $50 threshold and $5 fee. Three static functions are executed locally (no eval, no LLM). Weak suite tests60 only; stronger suite60,50,20. No training or claimed DeepSeek benchmark. Checks illustrate incomplete evaluation, not universal verification or guaranteed immunity to reward hacking.
