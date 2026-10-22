"""borer_sim.anatomy resolves the named neuron sets the simulator needs."""
import pytest

from borer_sim import anatomy, data

pytestmark = pytest.mark.needs_data

# (selector, args, expected count per side) — verified against v783, see flywire-data skill.
EXPECTED = [
    (anatomy.mn9, (), {"left": 1, "right": 1}),
    (anatomy.giant_fiber, (), {"left": 1, "right": 1}),
]
NAMES = {anatomy.mn9: "CB0701", anatomy.giant_fiber: "DNp01"}


@pytest.mark.parametrize("select,args,counts", EXPECTED)
def test_counts_per_side(select, args, counts):
    for side, n in counts.items():
        assert len(select(*args, side)) == n


@pytest.mark.parametrize("select,args,counts", EXPECTED)
def test_ids_in_model_and_match_filter(select, args, counts):
    a = data.annotations()
    expected_type = NAMES[select]
    for side in anatomy.SIDES:
        idx = select(*args, side)
        assert idx == sorted(idx) and len(set(idx)) == len(idx)
        root_ids = data.neuron_ids()[idx]  # IndexError if out of the model
        assert (a.loc[root_ids, "cell_type"] == expected_type).all()
        assert (a.loc[root_ids, "side"] == side).all()


@pytest.mark.parametrize("select,args,counts", EXPECTED)
def test_left_right_disjoint(select, args, counts):
    assert not set(select(*args, "left")) & set(select(*args, "right"))


def test_bad_side_and_unknown_type():
    with pytest.raises(ValueError):
        anatomy.mn9("center")
    with pytest.raises(KeyError):
        anatomy.cell_type("NOT_A_CELL_TYPE", "left")
