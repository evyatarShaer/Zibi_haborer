"""Subcircuit (P1-10): neurons on short paths from input to output neurons.

A neuron v is kept if hops(sources -> v) + hops(v -> targets) <= max_hops
(shortest directed paths over synapse edges); sources and targets are always
kept. Model.subcircuit(keep) keeps only edges between kept neurons.
"""
import numpy as np

from borer_sim import data


def _hops(n: int, src: np.ndarray, dst: np.ndarray, start, max_hops: int) -> np.ndarray:
    """Shortest hop count from `start` along src -> dst edges; max_hops + 1 if farther."""
    order = np.argsort(src, kind="stable")
    indptr = np.concatenate([[0], np.cumsum(np.bincount(src, minlength=n))])
    dst = dst[order]
    dist = np.full(n, max_hops + 1, dtype=np.int16)
    frontier = np.unique(np.asarray(start, dtype=np.int64))
    dist[frontier] = 0
    for h in range(1, max_hops + 1):
        lens = indptr[frontier + 1] - indptr[frontier]
        offset = np.arange(lens.sum()) - np.repeat(np.cumsum(lens) - lens, lens)
        nxt = np.unique(dst[np.repeat(indptr[frontier], lens) + offset])
        frontier = nxt[dist[nxt] > h]
        dist[frontier] = h
        if not len(frontier):
            break
    return dist


def keep(sources, targets, max_hops: int) -> np.ndarray:
    """Sorted model indices of the subcircuit."""
    n, pre, post, _ = data.edges()
    pre, post = np.asarray(pre, dtype=np.int64), np.asarray(post, dtype=np.int64)
    down = _hops(n, pre, post, sources, max_hops)
    up = _hops(n, post, pre, targets, max_hops)
    on_path = down.astype(np.int32) + up <= max_hops
    on_path[np.asarray(sources)] = on_path[np.asarray(targets)] = True
    return np.flatnonzero(on_path)
