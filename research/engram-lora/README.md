# Task adaptation with n-gram memory: a comparison with LoRA

[Read the experiment in the course](../../index.html#engram-research) · [Results](report.html)

We freeze SmolLM2-135M and compare a trainable Engram-inspired memory adapter with rank-8 LoRA. Classification and next-token prediction are separate experiments. These are preliminary measurements (one classifier seed; three text-generation seeds), not an exact DeepSeek reproduction or a claim of a novel general architecture.

## Reproduce

Use Python 3.12 and a compatible CUDA PyTorch installation. The recorded machine used an RTX 4090. Install the pinned packages in `requirements-resolved.txt` and `pyarrow==25.0.1` (or a compatible Parquet reader). Model/data downloads happen on the machine where these commands run.

```bash
python -m pip install -r requirements-resolved.txt pyarrow
python download_data.py
python train_banking.py --output pilot-r01 --epochs 4 --per-class 20 --batch 16
python train_banking.py --output banking-full-r01 --epochs 4 --per-class 0 --batch 32
python analyze_banking.py
python train_text.py --smoke --output text-smoke-r01
python train_text.py --output text-pilot-r01
python repeat_text.py
# Optional classifier replication:
python repeat_banking.py
```

Scripts share a GPU lock, use one job at a time, and cap their PyTorch allocator at 30% of GPU memory. Adjust this cap for a different machine. Outputs go to `runs/`; checked-in `results/` contains compact metric snapshots, not model weights or datasets.

## Classification protocol

- BANKING77: real banking questions, 77 intent labels. Normalize exact duplicate training text before splitting.
- Seed 42; 10 validation examples per class (770 total); either 20 training examples per class (1,540), or all remaining training examples (9,229).
- Four epochs, learning rates 0.0003 and 0.001 for each method. Validation accuracy selects the epoch and learning rate before the official 3,080-example test evaluation.
- Max length 96, BF16 autocast, AdamW, weight decay 0.01, gradient norm cap 1.0.
- A mean-pooled, normalized hidden state feeds a 77-class linear head. All methods get the same head initialization. The frozen baseline trains only this head.
- LoRA: query/value projections in all 30 layers; rank 8, alpha 16, zero dropout; 460,800 adapter parameters.
- Engram: one insertion before block 8, raw token 2/3-grams, two hash heads per length, four 32-dimensional tables, context gate and causal depthwise convolution; 460,352 adapter parameters.
- Memory rows: 2,401 / 2,411 / 2,417 / 2,423. Multiplicative XOR addressing. Table vectors are concatenated and projected into keys and values. The gate uses normalized dot product followed by sigmoid. The value projection and convolution start at zero.
- This adapter omits the paper's tokenizer compression and multi-stream architecture. Its placement differs from LoRA: this compares adaptation recipes, not only hashing in isolation.

## Text-generation protocol

Original next-token output head retained and frozen; no classifier. Train 512 contiguous blocks of 256 tokens from WikiText-2's official training split. Tune with 64 validation blocks and evaluate 128 test blocks. Blocks do not overlap; the first token in each block is not scored. Each adapter gets two epochs and the same two learning rates. Select by validation negative log likelihood; report test NLL and its exponential (perplexity).

This is a small subset with 256-token context resets, not the standard full-dataset WikiText perplexity benchmark. Four prompts are fixed in code before the run; all greedy continuations are saved. All methods recompute the full prefix, so generation timings are not optimized KV-cache benchmarks. Base-model pretraining overlap with WikiText has not been audited.

## Limits and planned work

One seed, a small base model, and a shared GPU. Wall-clock speed is affected by other workloads. Text seeds 42, 43 and 44 are complete, using fixed data subsets. Classification seeds 43 and 44 are queued/running; their seed also changes the stratified training/validation split. Verified-answer generation, unrelated-task retention, and task-specific module swapping are planned. Transfer across different backbones is not tested. The baseline is a base language model, not an instruction-tuned assistant.

Original model and dataset licenses apply. BANKING77 attribution: PolyAI; WikiText: Salesforce Research; SmolLM2: Hugging Face. Original Engram: DeepSeek-AI. See their source repositories and the course attribution.
