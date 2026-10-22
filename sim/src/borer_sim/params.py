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
BIN_MS = 20.0         # spike-count bins kept for replay

TASTING_MS = 1500     # simulated per tasting (SPEC §6; fallback 2000, DECISIONS.md 2026-10-22)

# "Taste of words" (SPEC §4); values from smell of words, DECISIONS.md 2026-10-20 / 2026-10-22.
TASTE = {
    "max_chars": 280,     # normalized text is truncated to this length
    "r_base": 8.0,        # baseline receptor rate (Hz)
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
