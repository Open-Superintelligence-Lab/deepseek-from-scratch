# N-gram module switching and capacity cost

September 21, 2026. Source: results/swappable-r01/final-results.json and
table-only-swaps.json. Whole-module results average seeds42/43/44; table-only
diagnostic uses seed42 only. Lower perplexity is better.

| Loaded small module | Finance test | Code test |
|---|---:|---:|
| None | 31.53 | 23.44 |
| Finance | 30.42 | 23.25 |
| Code | 31.75 | 19.64 |

All same-model A/B/A restoration checks passed. Modules contain the tables and
their learned reader, gate and convolution; the tokenizer is unchanged. This
tests module loading given a known domain, not automatic routing or improved
factual question answering.

## Can only the tables be switched?

For the small module and code test, seed42:

- Complete code module: 19.6396.
- Code tables + finance reader: 23.2893.
- Finance tables + code reader: 21.4499.

Independently trained tables do not transfer the full specialty by themselves.
The reader also carries learned changes. This does not establish that table-only
switching is impossible: a reader explicitly trained to work with several tables
would be a different experiment. No new model training was needed for this diagnostic.

## Cost as rows grow

| Property | Small | Large |
|---|---:|---:|
| Total rows across four tables | 9,652 | 52,872 |
| Row width | 32 | 32 |
| Lookups per token | 4 | 4 |
| Module parameters including reader | 460,352 | 1,843,392 |
| Saved FP32 module bytes | 1,844,869 | 7,377,029 |
| Measured peak training allocation, MiB | 882.45 | 904.30 |

Fixed heads and width: more rows increase weight storage linearly, but do not
increase the number of retrieved vectors or reader matrix dimensions per token.
Cache misses, memory bandwidth, device transfers and loading a replacement module
can still raise latency. We did not benchmark uncontended or optimized inference.

Our implementation uses dense embedding gradients and dense AdamW. More rows
therefore increase gradient/optimizer memory and table-wide optimizer work too.
FP32 weights + gradients + two Adam moments require approximately 16 bytes per
table parameter, excluding temporary buffers and the backbone. Four tables with
one million rows each and width32 would require 512 MB for FP32 weights, and
roughly 2.048 GB for these four training tensors. These are arithmetic estimates,
not measurements of that larger configuration.

Increasing head count or row width is different: it also increases retrieved
data and reader computation. Merely adding rows is the cheap-compute capacity
axis. Current timings are GPU-contention-dependent; no speedup claim is justified.
