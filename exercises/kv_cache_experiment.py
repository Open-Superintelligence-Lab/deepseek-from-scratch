#!/usr/bin/env python3
"""Bounded KV-cache mechanism benchmark using a deterministic untrained NumPy model."""
from __future__ import annotations
import json, platform, time, tracemalloc
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "kv_cache_config.json").read_text())
rng = np.random.default_rng(CFG["seed"])
D, V = CFG["d_model"], CFG["vocab_size"]
DTYPE = np.float32
scale = D ** -0.5

def weight(*shape): return (rng.standard_normal(shape) / np.sqrt(shape[0])).astype(DTYPE)
E, P = weight(V, D), weight(2048, D)
WQ, WK, WV, WO = weight(D, D), weight(D, D), weight(D, D), weight(D, D)

def softmax(x):
    z = x - x.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)

def full(tokens):
    """Recompute the complete causal prefix and return logits plus K/V cache."""
    x = E[tokens] + P[:len(tokens)]
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        q, k, v = x @ WQ, x @ WK, x @ WV
        scores = q @ k.T * scale
    scores[np.triu_indices(len(tokens), 1)] = -np.inf
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        hidden = softmax(scores) @ v
        logits = hidden @ WO @ E.T
    if not np.isfinite(logits).all(): raise FloatingPointError("non-finite full-path logits")
    return logits, (k, v)

def cached_step(token, position, cache):
    """Process one new token using keys/values retained from earlier positions."""
    x = E[token] + P[position]
    q, k, v = x @ WQ, x @ WK, x @ WV
    if cache is None:
        keys, values = k[None, :], v[None, :]
    else:
        keys = np.concatenate((cache[0], k[None, :]), axis=0)
        values = np.concatenate((cache[1], v[None, :]), axis=0)
    hidden = softmax((q @ keys.T) * scale) @ values
    return hidden @ WO @ E.T, (keys, values)

def build_cache(tokens):
    """Incrementally prefill a cache and return the final-position logits."""
    cache = None
    logits = None
    for position, token in enumerate(tokens):
        logits, cache = cached_step(int(token), position, cache)
    return logits, cache

def benchmark(fn):
    for _ in range(CFG["warmups"]): fn()
    samples=[]
    tracemalloc.start()
    for _ in range(CFG["repetitions"]):
        start=time.perf_counter_ns(); fn(); samples.append((time.perf_counter_ns()-start)/1e6)
    _, peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
    return {"median_ms": round(float(np.median(samples)),4), "samples_ms":[round(x,4) for x in samples], "python_tracemalloc_peak_bytes":peak}

def check_equivalence(prefix, forced):
    """Compare exactly the logits produced after every matched input position."""
    full_logits, full_cache = full(prefix)
    cached_logits, cache = build_cache(prefix)
    prefill_error = float(np.max(np.abs(full_logits[-1] - cached_logits)))
    cache_error = max(float(np.max(np.abs(a - b))) for a, b in zip(full_cache, cache))
    errors = []
    sequence = prefix.copy()
    for step, token in enumerate(forced):
        # Both paths now score prefix + forced[:step + 1], at the same position.
        sequence = np.append(sequence, token)
        full_logits, _ = full(sequence)
        cached_logits, cache = cached_step(int(token), len(prefix) + step, cache)
        errors.append(float(np.max(np.abs(full_logits[-1] - cached_logits))))
    max_error = max([prefill_error, cache_error, *errors])
    return {
        "prefill_last_logits_max_abs_error": prefill_error,
        "prefill_kv_max_abs_error": cache_error,
        "forced_steps_checked": len(errors),
        "forced_step_logits_max_abs_errors": errors,
        "forced_step_logits_max_abs_error": max(errors, default=0.0),
        "all_compared_outputs_match_atol_1e-5": max_error <= 1e-5,
    }

def main():
    rows=[]
    for n in CFG["context_lengths"]:
        prefix=rng.integers(0,V,size=n,dtype=np.int64)
        forced=rng.integers(0,V,size=CFG["continuation_tokens"],dtype=np.int64)
        correctness = check_equivalence(prefix, forced)
        _, prefix_cache = build_cache(prefix)
        def uncached_prefill():
            full(prefix)
        def cached_prefill():
            build_cache(prefix)
        def uncached_decode():
            sequence=prefix.copy()
            for token in forced:
                sequence=np.append(sequence,token)
                full(sequence)
        def cached_decode():
            # The already-prefilled prefix is outside both decode timers.
            local=prefix_cache
            for i,token in enumerate(forced):
                _,local=cached_step(int(token),n+i,local)
        cache_bytes=sum(a.nbytes for a in prefix_cache)
        rows.append({"context_tokens":n,"kv_cache_bytes":cache_bytes,"bytes_per_token":cache_bytes//n,
                     "correctness":correctness,
                     "prefill": {"uncached_full_prefix":benchmark(uncached_prefill),
                                 "cached_incremental_prefix":benchmark(cached_prefill)},
                     "forced_continuation_decode_excluding_prefill": {
                         "uncached_full_recomputation":benchmark(uncached_decode),
                         "cached_one_new_position":benchmark(cached_decode)}})
    result={"status":"measured","model":"deterministic untrained single-layer causal attention toy",
            "quality_evaluated":False,"device":"CPU","precision":"float32",
            "measurement":"time.perf_counter_ns median; prefill and forced-token decode timed separately; Python tracemalloc peak reported separately",
            "comparison_contract":"Both paths score the same prefix plus each appended forced token. Decode timers exclude construction of the shared prefix cache.",
            "memory_contract":"kv_cache_bytes is exact NumPy K/V tensor storage only, not Python allocations or process RSS.",
            "python":platform.python_version(),"numpy":np.__version__,"config":CFG,"results":rows}
    (ROOT/"kv_cache_results.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__ == "__main__": main()
