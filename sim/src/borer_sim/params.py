"""LIF constants from Shiu et al. 2024 (model.py default_params), unitless.

Times in ms, potentials in mV. The single source for both borer_sim.model
and the Brian2 port in sim/validation/shiu_brian2.py.
"""

LIF = {
    "v_0": -52.0,     # resting potential (mV)
    "v_rst": -52.0,   # reset potential after a spike (mV)
    "v_th": -45.0,    # spike threshold (mV)
    "t_mbr": 20.0,    # membrane time constant (ms)
    "tau": 5.0,       # synaptic time constant (ms)
    "t_rfc": 2.2,     # refractory period (ms)
    "t_dly": 1.8,     # synaptic delay (ms)
    "w_syn": 0.275,   # weight per synapse (mV)
    "f_poi": 250,     # Poisson input weight = f_poi * w_syn
}

DT_MS = 0.1           # integration step (Brian2 default)
BIN_MS = 10.0         # spike-count bins kept (readout 50 ms, replay 20 ms aggregate them)

TASTING_MS = 1500     # simulated per tasting (SPEC §6; fallback 2000, DECISIONS.md 2026-10-22)

# "Taste of words" (SPEC §4); values from smell of words, DECISIONS.md 2026-10-20 / 2026-10-22.
TASTE = {
    "max_chars": 280,     # normalized text is truncated to this length
    "r_base": 2.0,        # baseline receptor rate (Hz); silence sweep, DECISIONS.md 2026-10-22
    "r_max": 150.0,       # added rate at saturation (Hz)
    "cap": 120.0,         # max per-GRN rate of a letter's group (Hz), DECISIONS.md 2026-10-22
    "coverage_ref": 0.6,  # coverage at or above which a text keeps full drive (OLD+NEW minimum)
    "coverage_power": 2.0,  # drive x (coverage / coverage_ref) ** power below the ref
    "k": 0.05,            # half-saturation, in share of letters (~1/22 per letter)
    "len_ref": 140,       # length (chars) at which the length gain is 1
    "punct_max": 75.0,    # cap on the rate added by "!" or "?" (Hz)
    "punct_k": 2.0,       # half-saturation, in number of marks
    "verbose_marks": 1.0, # a max-length text adds this many "!" (too much → aversive)
}

# Fly mood (SPEC §5): an added layer, seeded per case, identical for both tastings.
MOOD = {
    "hunger_base_max": 0.4,  # hunger at case open ~ U(0, this); waiting adds the rest
    "hunger_per_hour": 0.1,  # + per hour from case open until both submitted (cap 1)
    "wait_mean_h": 2.0,      # hearing without a wait (SPEC §5, §14): wait ~ Exp(this) h from the seed
    "hunger_gain": 0.5,      # MN9-exciting groups' drive above baseline x (1 + gain * hunger)
    "arousal_max": 0.45,     # arousal ~ U(0, this): no runaway below 0.48 (DECISIONS.md 2026-10-24)
    "noise_hz": 10.0,        # background kicks per neuron at arousal 1 (Hz); 20 Hz ignites runaways
    "noise_mv": 2.0,         # size of one background kick, random sign (mV)
}

# Readout and outcome thresholds (SPEC §6–§7): the ONLY place they are set.
# Calibrated on OLD+NEW with product mood (validation.mood_calib, DECISIONS.md 2026-10-24).
OUTCOME = {
    "readout_bin_ms": 50,    # MN9 bins for decision time and direction flips
    "tie_gap": 0.05,         # Win needs gap = |A - B| / (A + B) >= this
    "froze_hz": 6.0,         # Froze: both A and B below this (Hz, MN9 L + R); calibrated 0.7.0
    "food_hunger": 0.8,      # Went for food: hunger above this and gap < tie_gap
    "dither_flips": 8,       # Dithered: at least this many flips and gap < tie_gap; calibrated 0.7.0
    "decision_spikes": 3,    # decision: cumulative binned A - B stays >= this (spikes)
}
