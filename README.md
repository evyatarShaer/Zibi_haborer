# HaBorer (הבורר) — The Arbiter

A WhatsApp-shared web game where two people argue and a simulation of a
real fruit-fly brain decides who wins. Arguments become smells; the fly
turns toward one side.

**Status:** early POC. Nothing to run yet.

- Spec: [`docs/SPEC.md`](docs/SPEC.md)
- Decisions: [`docs/DECISIONS.md`](docs/DECISIONS.md)
- Tasks: [`docs/TASKS.md`](docs/TASKS.md)
- Claude context: [`CLAUDE.md`](CLAUDE.md)

## Data & license

The simulator uses the **FlyWire whole-brain connectome, public release
v783**, which is licensed under
[**CC BY-NC 4.0**](https://creativecommons.org/licenses/by-nc/4.0/)
(see [flywire.ai/guidelines](https://flywire.ai/guidelines)).
**This project is therefore non-commercial only** until a separate
license is obtained from Princeton/FlyWire. The raw data is not stored in
this repo; see [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md).

Code in this repo is separate from the data; the data terms above apply
to any connectome-derived file or output.

**Required citations** (per FlyWire's citation guidelines):

- Dorkenwald, S. et al. *Neuronal wiring diagram of an adult brain.*
  Nature 634, 124–138 (2024). doi:10.1038/s41586-024-07558-y
- Schlegel, P. et al. *Whole-brain annotation and multi-connectome cell
  typing of Drosophila.* Nature 634, 139–152 (2024).
  doi:10.1038/s41586-024-07686-5 — cell-type annotations
  (`flyconnectome/flywire_annotations`).
- Eckstein, N. et al. *Neurotransmitter classification from electron
  microscopy images at synaptic sites in Drosophila melanogaster.*
  Cell 187, 2574–2594 (2024). doi:10.1016/j.cell.2024.03.016 —
  neurotransmitter predictions (excitatory/inhibitory sign).
- Shiu, P. K. et al. *A Drosophila computational brain model reveals
  sensorimotor processing.* Nature 634, 210–219 (2024).
  doi:10.1038/s41586-024-07763-9 — the model and the
  `Connectivity_783` / `Completeness_783` files
  (`philshiu/Drosophila_brain_model`, code MIT).

**Acknowledgement:** We thank the Princeton FlyWire team and members of
the Murthy and Seung labs for development and maintenance of FlyWire
(supported by BRAIN Initiative grants MH117815, MH129268 and
U24 NS126935 to Murthy and Seung), and the FlyWire consortium for
neuron proofreading and annotation.
