"""borer_sim.anatomy resolves the named neuron sets the simulator needs."""
import pytest

from borer_sim import anatomy, data

pytestmark = pytest.mark.needs_data

# (selector, args, expected count per side) — verified against v783, see flywire-data skill.
EXPECTED = [
    (anatomy.orns, ("V",), {"left": 34, "right": 33}),
    (anatomy.orns, ("DA2",), {"left": 16, "right": 22}),
    (anatomy.turning_dns, (), {"left": 1, "right": 1}),
    (anatomy.giant_fiber, (), {"left": 1, "right": 1}),
]
NAMES = {anatomy.orns: None, anatomy.turning_dns: "DNa02", anatomy.giant_fiber: "DNp01"}


@pytest.mark.parametrize("select,args,counts", EXPECTED)
def test_counts_per_side(select, args, counts):
    for side, n in counts.items():
        assert len(select(*args, side)) == n


@pytest.mark.parametrize("select,args,counts", EXPECTED)
def test_ids_in_model_and_match_filter(select, args, counts):
    a = data.annotations()
    expected_type = NAMES[select] or anatomy.ORN_PREFIX + args[0]
    for side in anatomy.SIDES:
        idx = select(*args, side)
        assert idx == sorted(idx) and len(set(idx)) == len(idx)
        root_ids = data.neuron_ids()[idx]  # IndexError if out of the model
        assert (a.loc[root_ids, "cell_type"] == expected_type).all()
        assert (a.loc[root_ids, "side"] == side).all()


@pytest.mark.parametrize("select,args,counts", EXPECTED)
def test_left_right_disjoint(select, args, counts):
    assert not set(select(*args, "left")) & set(select(*args, "right"))


def test_orn_glomeruli_table():
    t = anatomy.orn_glomeruli()
    assert len(t) == 53
    assert t.loc["V", ["left", "right"]].tolist() == [34, 33]
    assert t.loc["DA2", ["left", "right"]].tolist() == [16, 22]
    palp = set(t.index[t.nerve.str.contains("MxLbN")])
    assert palp == {"VA4", "VA7l", "VC1", "VC2", "VM7d", "VM7v"}


def test_bad_side_and_unknown_type():
    with pytest.raises(ValueError):
        anatomy.orns("V", "center")
    with pytest.raises(KeyError):
        anatomy.orns("NOT_A_GLOMERULUS", "left")
