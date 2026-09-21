#!/usr/bin/env python3
"""A deliberately small, CPU-only causal language-model training experiment."""
import argparse, json, math, random, sys, time
from collections import Counter
from pathlib import Path

import torch
from torch import nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent

def grammar_sentences():
    """Original finite compositional command grammar; no downloaded text."""
    colors = ["red", "blue", "green"]
    shapes = ["circle", "square", "triangle"]
    directions = ["left", "right", "up", "down"]
    counts = ["once", "twice"]
    out = []
    for c in colors:
      for s in shapes:
       for d in directions:
        for n in counts:
         for new_c in colors:
          out.append(f"move the {c} {s} {d} {n} then paint it {new_c}")
          out.append(f"paint the {c} {s} {new_c} then move it {d} {n}")
    return out

def make_data(cfg):
    sentences = grammar_sentences()
    shuffled = sentences[:]
    random.Random(cfg["split_seed"]).shuffle(shuffled)
    cut = int(len(shuffled) * cfg["train_fraction"])
    train, valid = shuffled[:cut], shuffled[cut:]
    assert not set(train) & set(valid)
    tokens = sorted({t for s in sentences for t in s.split()})
    vocab = ["<pad>", "<bos>", "<eos>"] + tokens
    stoi = {t:i for i,t in enumerate(vocab)}
    def encode(s): return [stoi["<bos>"]] + [stoi[t] for t in s.split()] + [stoi["<eos>"]]
    return train, valid, vocab, stoi, encode

class Block(nn.Module):
    def __init__(self, dim, heads, mlp):
        super().__init__()
        self.ln1, self.attn = nn.LayerNorm(dim), nn.MultiheadAttention(dim, heads, batch_first=True)
        self.ln2 = nn.LayerNorm(dim)
        self.ff = nn.Sequential(nn.Linear(dim, mlp), nn.GELU(), nn.Linear(mlp, dim))
    def forward(self, x, mask):
        y, _ = self.attn(self.ln1(x), self.ln1(x), self.ln1(x), attn_mask=mask, need_weights=False)
        return x + y + self.ff(self.ln2(x + y))

class TinyCausalLM(nn.Module):
    def __init__(self, v, cfg):
        super().__init__()
        self.context = cfg["context"]
        self.token = nn.Embedding(v, cfg["dim"])
        self.position = nn.Embedding(cfg["context"], cfg["dim"])
        self.blocks = nn.ModuleList([Block(cfg["dim"], cfg["heads"], cfg["mlp_dim"]) for _ in range(cfg["layers"])])
        self.norm, self.head = nn.LayerNorm(cfg["dim"]), nn.Linear(cfg["dim"], v, bias=False)
    def forward(self, ids):
        b, t = ids.shape
        assert t <= self.context
        x = self.token(ids) + self.position(torch.arange(t, device=ids.device))[None]
        # True values mean positions that must be hidden: every future token.
        future = torch.triu(torch.ones(t, t, device=ids.device, dtype=torch.bool), diagonal=1)
        for block in self.blocks: x = block(x, future)
        return self.head(self.norm(x))

def batches(sequences, batch_size, pad, rng=None):
    order = list(range(len(sequences)))
    if rng: rng.shuffle(order)
    for i in range(0, len(order), batch_size):
        part = [sequences[j] for j in order[i:i+batch_size]]
        longest = max(map(len, part))
        x = torch.full((len(part), longest - 1), pad, dtype=torch.long)
        y = torch.full_like(x, pad)
        for row, seq in enumerate(part):
            x[row, :len(seq)-1] = torch.tensor(seq[:-1])
            y[row, :len(seq)-1] = torch.tensor(seq[1:])
        yield x, y

def token_mean_ce(model, sequences, cfg, pad):
    model.eval(); total = 0.0; count = 0
    with torch.no_grad():
      for x, y in batches(sequences, cfg["batch_size"], pad):
        loss = F.cross_entropy(model(x).reshape(-1, model.head.out_features), y.reshape(-1), ignore_index=pad, reduction="sum")
        total += loss.item(); count += int((y != pad).sum())
    return total / count, count

def greedy(model, ids, itos, steps=8):
    model.eval()
    with torch.no_grad():
      for _ in range(steps):
        nxt = int(model(torch.tensor([ids[-model.context:]]) )[0, -1].argmax())
        ids.append(nxt)
        if itos[nxt] == "<eos>": break
    return " ".join(itos[i] for i in ids)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path(__file__).parent, help="new empty run folder; existing finished runs are never overwritten")
    args = ap.parse_args(); out = args.out.resolve()
    cfg = json.loads((ROOT / "config.json").read_text())
    if out.exists() and any(out.iterdir()):
        # Allow executing this source in r01 once, but never replace a finished result.
        allowed = {Path(__file__).name}
        if {p.name for p in out.iterdir()} - allowed:
            raise SystemExit(f"refusing to overwrite populated run folder: {out}")
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(cfg["torch_threads"]); random.seed(cfg["training_seed"]); torch.manual_seed(cfg["training_seed"])
    train_s, valid_s, vocab, stoi, encode = make_data(cfg); pad = stoi["<pad>"]
    train, valid = list(map(encode, train_s)), list(map(encode, valid_s))
    assert max(map(len, train + valid)) - 1 <= cfg["context"]
    data_record = {"provenance":"Original generated compositional command grammar; no external corpus.", "dataset_seed":cfg["dataset_seed"], "split_seed":cfg["split_seed"], "train_fraction":cfg["train_fraction"], "vocab":vocab, "train_sentences":train_s, "validation_sentences":valid_s}
    (out / "dataset.json").write_text(json.dumps(data_record, indent=2) + "\n")
    model = TinyCausalLM(len(vocab), cfg)
    n_params = sum(p.numel() for p in model.parameters())
    counts = Counter(t for seq in train for t in seq[1:])
    denom = sum(counts.values()) + len(vocab)
    unigram = torch.tensor([(counts[i] + 1) / denom for i in range(len(vocab))])
    def baseline_ce(sequences, probs):
      targets = [t for seq in sequences for t in seq[1:]]
      return float(-torch.log(probs[torch.tensor(targets)]).mean())
    uniform = math.log(len(vocab)); unigram_valid = baseline_ce(valid, unigram)
    untrained, valid_tokens = token_mean_ce(model, valid, cfg, pad)
    prompt = [stoi[x] for x in "<bos> move the red circle".split()]
    before = greedy(model, prompt[:], vocab)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"])
    curve = [{"step":0, "train_ce":token_mean_ce(model, train, cfg, pad)[0], "validation_ce":untrained}]
    rng = random.Random(cfg["training_seed"] + 1); start = time.perf_counter()
    for step in range(1, cfg["steps"] + 1):
      model.train()
      x, y = next(batches(train, cfg["batch_size"], pad, rng))
      opt.zero_grad(); loss = F.cross_entropy(model(x).reshape(-1, len(vocab)), y.reshape(-1), ignore_index=pad)
      loss.backward(); opt.step()
      if step % cfg["eval_every"] == 0 or step == cfg["steps"]:
        curve.append({"step":step, "train_ce":token_mean_ce(model, train, cfg, pad)[0], "validation_ce":token_mean_ce(model, valid, cfg, pad)[0]})
    runtime = time.perf_counter() - start
    trained, _ = token_mean_ce(model, valid, cfg, pad)
    after = greedy(model, prompt[:], vocab)
    # Future changes may alter their own logits, but cannot alter earlier positions.
    probe = torch.tensor([[stoi["<bos>"], stoi["move"], stoi["the"], stoi["red"], stoi["circle"], stoi["left"]]])
    altered = probe.clone(); altered[0, -1] = stoi["right"]
    model.eval()
    with torch.no_grad(): diff = float((model(probe)[0, :-1] - model(altered)[0, :-1]).abs().max())
    assert diff == 0.0, diff
    torch.save({"model_state_dict":model.state_dict(), "config":cfg, "vocab":vocab}, out / "trained.pt")
    rows = "\n".join(f"{x['step']},{x['train_ce']:.6f},{x['validation_ce']:.6f}" for x in curve)
    (out / "loss_curve.csv").write_text("step,train_ce,validation_ce\n" + rows + "\n")
    # Portable no-dependency plot for the course page.
    W,H=640,360; xs=[x["step"] for x in curve]; ys=[v for x in curve for v in (x["train_ce"],x["validation_ce"])]; lo,hi=min(ys),max(ys); scale=lambda x:50+(W-75)*x/cfg["steps"]; sy=lambda y:H-40-(H-70)*(y-lo)/max(hi-lo,1e-9)
    line=lambda key,color:" ".join(f"{scale(x['step']):.1f},{sy(x[key]):.1f}" for x in curve)
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/><path d="M50 20V320H620" stroke="#333" fill="none"/><text x="50" y="15" font-family="sans-serif" font-size="14">Token-weighted cross-entropy (lower is better)</text><polyline fill="none" stroke="#1976d2" stroke-width="3" points="{line("train_ce", "#1976d2")}"/><polyline fill="none" stroke="#d32f2f" stroke-width="3" points="{line("validation_ce", "#d32f2f")}"/><text x="480" y="45" fill="#1976d2">train</text><text x="480" y="65" fill="#d32f2f">validation</text><text x="45" y="340">0</text><text x="590" y="340">steps {cfg["steps"]}</text></svg>'
    (out / "loss_curve.svg").write_text(svg)
    result={"experiment":"tiny trained causal language-model baseline", "honesty":"Educational synthetic grammar experiment only; it is not DeepSeek and does not establish natural-language generalization.", "device":"cpu", "torch_version":torch.__version__, "config":cfg, "parameters":n_params, "vocab_size":len(vocab), "train_sentence_count":len(train_s), "validation_sentence_count":len(valid_s), "validation_target_tokens":valid_tokens, "metrics":{"uniform_validation_ce":uniform,"smoothed_train_unigram_validation_ce":unigram_valid,"untrained_validation_ce":untrained,"trained_validation_ce":trained,"curve":curve}, "causal_mask_invariance":{"max_abs_difference_at_earlier_positions":diff,"passed":diff == 0.0}, "fixed_prompt_samples":{"prompt":"<bos> move the red circle","before":before,"after":after}, "runtime_seconds":runtime, "checkpoint":"trained.pt"}
    (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    (out / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
    (out / "samples.txt").write_text(f"Fixed prompt: <bos> move the red circle\nBefore training: {before}\nAfter training:  {after}\n")
    print(json.dumps(result, indent=2))
if __name__ == "__main__": main()
