"""Single loader for the FlyWire v783 raw tables (see flywire-data skill).

Schemas are documented in docs/DATA_SOURCES.md. Each table is read once
per process and cached.
"""
from functools import cache
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "flywire_v783"

CONNECTIVITY_COLS = ["Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"]


@cache
def neuron_ids(raw_dir: Path = RAW_DIR) -> pd.Index:
    """Model neuron root_ids; position = the *_Index used in connectivity."""
    df = pd.read_csv(raw_dir / "Completeness_783.csv", index_col=0)
    return pd.Index(df.index, name="root_id")


@cache
def connectivity(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Directed edges: pre/post model index and signed synapse count."""
    return pd.read_parquet(raw_dir / "Connectivity_783.parquet", columns=CONNECTIVITY_COLS)


@cache
def annotations(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Schlegel et al. 2024 per-neuron annotations, indexed by root_id."""
    path = raw_dir / "Supplemental_file1_neuron_annotations.tsv"
    return pd.read_csv(path, sep="\t", low_memory=False).set_index("root_id")


def to_index(root_ids) -> list[int]:
    """Map root_ids to model indices; raises KeyError on unknown ids."""
    idx = neuron_ids().get_indexer(root_ids)
    if (idx < 0).any():
        bad = [r for r, i in zip(root_ids, idx) if i < 0]
        raise KeyError(f"root_ids not in v783 model: {bad}")
    return idx.tolist()
