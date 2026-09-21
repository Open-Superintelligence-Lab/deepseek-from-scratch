# Swappable specialists: preregistered bounded pilot

Fixed before training or inspecting test losses, 2026-09-21.

Question: can a frozen SmolLM2 acquire useful domain-specific next-token
prediction through a swappable n-gram adapter, and is its quality/cost trade-off
better than a swappable LoRA? A negative result is a valid outcome.

## Data

- Finance: BeIR/fiqa corpus, revision 979c07a7cb5ccc6ca009792241fa1250b98055dd.
  Real financial discussions, CC-BY-SA-4.0 according to its dataset card.
- Code: CodeSearchNet Ruby functions, revision
  bd0cf261e357a3eb5c8fba490d23ec1a1cd59555. Preserve upstream provenance and
  licensing; no code is executed, no dataset or trained weights are published.
- Download directly to the existing GPU server. No generated examples.
- Custom language-modeling splits, NOT the original retrieval/code-search task.
  Finance split by SHA256 of normalized document; code by repository name,
  combining original files before repartition. Hash buckets 0-79 train, 80-89
  validation, 90-99 test. Exact normalized duplicate documents removed globally.
  Finance lacks thread IDs, so related answers may remain across splits.
- Documents ordered by SHA256 of source ID. At most 1,024 tokens/document.
  Exclude validation/test documents sharing any exact 64-token span with selected
  earlier splits. Record exclusions; this does not eliminate semantic duplicates
  or unknown base-model pretraining contamination.
- Pack documents with EOS separators into 128-token blocks. Per domain:
  512 training blocks, 64 validation blocks, 64 test blocks. Same tensors for
  every method/seed. Context can cross EOS inside a block; identical for methods.
- Preserve IDs, split hashes, source file hashes, actual counts and code hashes.

## Methods and fixed budget

- Same frozen SmolLM2-135M checkpoint as preceding experiments; original frozen
  language-model head, no classifier, no prompting/instruction tuning.
- LoRA ranks 8 and 32, alpha=2*rank, query/value projections in all 30 layers.
- Engram-inspired small and large: existing reader, layer 7, four 32-wide
  tables, orders [2,2,3,3]. Small rows [2401,2411,2417,2423]; large rows
  [13207,13217,13219,13229]. Approximately 0.46M and 1.84M adapter parameters,
  paired with LoRA rank 8/32. Only rows change across Engram capacities.
- Whole trained module is swappable (tables AND reader/gate/conv); no claim
  of table-only portability, arbitrary-base-model transfer or exact paper reproduction.
- Two epochs, AdamW, weight decay .01, clip norm 1, BF16 autocast, FP32 weights.
  Microbatch 1, accumulate 8, same example order per seed. Dense table gradients
  and dense AdamW: do NOT claim sparse training cost.
- Seed42: equal LR search [.0003,.001] and validation-selected epoch for all
  domain/method/capacity pairs. Lock each selected LR; repeat seeds43/44 with
  that LR, selecting epoch on validation. Do not retune after viewing test results.
- Sixteen tuning runs plus sixteen repeat runs, then exit. No endless GPU queue.
  Smoke runs use separate directories and cannot enter reported results.

## Evaluation and interpretation

- Primary: all held-out next-token losses, per domain and capacity, all seeds.
  Show perplexity and paired NLL differences; no executable-code or financial
  reasoning claim from perplexity alone.
- Evaluate every selected specialist on BOTH domains: correct versus wrong
  specialist and no specialist. Finance -> code -> finance restoration must
  reproduce identical logits without reloading/changing the base model.
- Descriptive buckets: prediction positions whose preceding three tokens were
  seen >=5 times, 1-4 times or zero times in THAT domain's training blocks.
  Define buckets from training only, report counts and all buckets. This is a
  correlation check, not causal proof of why a module works.
- Include a count-based trigram prediction baseline with unigram backoff,
  with its interpolation strength selected on validation only.
- General-text regression: fixed existing 64 WikiText-2 test blocks, never used
  for selection in this run. Prior experiments already inspected WikiText, so
  this is a regression check, not a fresh confirmatory benchmark.
- Record parameter count, artifact bytes, per-process peak GPU allocation,
  training wall time. Shared GPU contention prevents a clean speed claim.
  This pilot does not benchmark optimized KV-cached generation or merged LoRA.
- 65,536 training tokens/domain is a feasibility pilot, not table-saturation
  evidence. Do not extrapolate a win or loss to large-scale Engram training.

## Validation and execution

Check frozen gradients, initial identity, causal prefixes, nonzero table
gradients, finite losses, exact state reload, split disjointness and module
restoration. Persist each complete trial so restart skips it. An interrupted
trial restarts from its fixed seed; no silent parameter/data changes on OOM.
Use the existing project training lock and a bounded supervisor process.
