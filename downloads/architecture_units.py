"""Illustrative arithmetic only; no model or dependencies. Run: python3 architecture_units.py"""

def make_cache_entry(h):
    return h[0] + 2*h[1], -h[0] + h[1]

assert make_cache_entry([2, 3]) == (8, 1)
assert make_cache_entry([3, 3]) == (9, 0)

def select_values(scores, values, k=2):
    ids = sorted(range(len(scores)),
                 key=lambda i: (-scores[i], i))[:k]
    return [values[i] for i in ids]

assert select_values([.2,.9,.1,.8], [10,20,30,40]) == [20,40]
assert select_values([.95,.9,.1,.8], [10,20,30,40]) == [10,20]

def mix_streams(a, b, wa, wb):
    return [wa*x + wb*y for x, y in zip(a, b)]

assert mix_streams([2,0], [0,4], .25, .75) == [.5,3]
assert mix_streams([2,0], [0,4], .5, .5) == [1,2]

print("PASS: all 6 architecture unit checks")
