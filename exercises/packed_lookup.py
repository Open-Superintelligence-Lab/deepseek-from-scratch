"""Teaching adaptation of DeepSeek Engram's packed lookup; no PyTorch needed.
Official source: https://github.com/deepseek-ai/Engram/blob/main/engram_demo_v1.py
Fixed illustrative arrays, not trained model weights. See ../assets/engram-official/LICENSE.
"""
def lookup(use_offsets=True):
    table = [[0, 0], [0.2, -0.5], [0, 0], [0, 0], [0.6, 0.1], [0, 0], [0, 0]]
    local_rows = [1, 1]
    offsets = [0, 3]
    global_rows = [row + (offset if use_offsets else 0)
                   for row, offset in zip(local_rows, offsets)]
    return global_rows, [table[row] for row in global_rows]

if __name__ == '__main__':
    for enabled in [False, True]:
        rows, vectors = lookup(enabled)
        print(f'Offsets enabled: {enabled}; global rows: {rows}; vectors: {vectors}')
    assert lookup(True) == ([1, 4], [[0.2, -0.5], [0.6, 0.1]])
    assert lookup(False) == ([1, 1], [[0.2, -0.5], [0.2, -0.5]])
