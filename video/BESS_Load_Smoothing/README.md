# BESS and Abrupt Loads

A short English film rendered with Python, Manim and Schemdraw, using the project's existing PSCAD/EMTDC generator simulations. All visible variables, numerals and units use Manim MathTex and local LaTeX/dvisvgm. The video is silent and uses sparse English labels, animated energy flow, synchronized traces and shaft motion.

## Watch

`output/BESS_Abrupt_Loads_1080p.mp4` is the final chaptered 1920 x 1080, 30 fps MP4. `evidence/contact_sheet_final.jpg` provides representative frames. Exact timing and encoding are recorded in `evidence/final_timeline.json` and `evidence/final_probe.json`.

The current cut contains five chapters and ends with **What the simulation demonstrates**. The separate load-step close-up and closing limitation slide have been removed. A short contextual note about numerical step-size sensitivity appears in the shaft-scene footer. `output/Shaft_Twist_Comparison_1080p.mp4` contains only the current shaft scene for immediate review.

The converter symbol in **A parallel energy buffer** shows an AC sine wave in the upper, bus-connected half and a solid line above three dashes in the lower, battery-connected DC half. The same symbol is used in `assets/parallel_single_line.svg`. This correction changes only that chapter; the other four chapter files, animation timing and numerical data are unchanged. The previous video, ZIP, sources and affected assets are preserved in the history folder identified in `evidence/converter_baseline.json`. Earlier revisions have preservation records in `evidence/edit_baseline.json` and `evidence/revision_baseline.json`.

The current duration, decoded frame count and check totals are recorded in `evidence/delivery_verification.json`. Validation covers full-video decoding, timestamps, signal/metric reproduction, LaTeX inventory, preserved source files, unchanged chapters and eleven numerical unit tests. ZIP CRC and payload hashes are checked independently when the package is built.

## Evidence and scope

The two generator cases come from the completed 2026-10-26 suite identified by `results/scale_250_500/latest_suite.json` in the parent project. This production reuses those runs; it does not claim a new PSCAD execution. The new extraction verified the project hashes, every output-file hash in each run receipt, .inf channel indexes, finite values, block timestamps, completed duration, common integration settings, and identical load commands. The original PSCAD models, outputs and historical packages were left intact.

The motors, rolling mill, crane and pulsed-load images are illustrative application examples. They do not represent four additional simulations. The numerical animation uses the same aggregate load-command profile in both generator cases. Measured load power can differ slightly between cases during transients; both traces are shown.

The physical source is a native three-mass shaft driven by a simplified net gas-turbine model. The intermediate mass is an equivalent coupling inertia. It is an illustrative aggregate system, not a manufacturer-calibrated machine.

## Meaning of the comparisons

| Quantity | PSCAD channel | Meaning |
|---|---|---|
| P_L | Pload_MW | Measured load consumption |
| P_G | Pgen_MW | Active power at the generator terminals |
| P_B | Pbess_MW | BESS AC power; positive means discharge into the bus |
| T_e (retained data) | Generator_Te_pu | Generator electromagnetic torque |
| T_12 (retained data) | Shaft_T12_pu | Transmitted torque between turbine and coupling masses |
| T_23 | Shaft_T23_pu | Transmitted torque between coupling and generator masses |
| theta_i | Shaft_theta1/2/3_rad | Mechanical angle deviations recorded by PSCAD |

Pgrid_MW is a different measurement, on the downstream 34.5 kV side of the network transformer. It is retained in the data and independently checked against the original audit, but it is not relabeled as generator-terminal power. The circuit equation includes total network losses. The circuit is a single-line equivalent; transformers and detailed converter switching circuitry are omitted from the visual for readability. Flow particles and arrow widths are qualitative, not a numerical power scale.

For the power plots, a centered one-cycle moving average (1/60 s) is applied before display sampling. Raw T_23 and shaft angles are not averaged. The raw selected channels retain the original 100 microsecond output samples; the display archive uses 0.5 ms spacing. The full-profile plot uses 8 ms point spacing, and the shaft-torque plot uses every display sample. All reported metrics are computed from the original full-rate averaged signals, before display decimation. Shaft-torque values lie within the common 0.22 to 0.52 pu scale. The rotor release occurs at 1.2 s; the displayed event is at 2 s.

The revised shaft scene highlights the segment between the coupling and generator masses. Each large indicator shows `(theta2 - theta3) - mean_pre(theta2 - theta3)`, using 1.8 <= t < 1.95 s as the reference. Subtracting the two angles cancels common rotation; subtracting the pre-step mean removes the equilibrium twist. Small residual pre-step fluctuations are retained instead of being artificially clamped to zero.

Both indicators use the same geometric magnification of 200. The maximum visual excursions over 1.8-2.8 s are approximately 56.08 degrees without BESS and 3.15 degrees with BESS. Tick marks and live numerical readouts remain in physical milliradians; their values are not multiplied by 200. The corresponding observed peak absolute twist changes are 4.8942 and 0.2751 mrad. These are event-specific traces, not damping ratios or a convergence-validated torsional benefit. The white ring marker holds the greatest positive excursion reached so far. Faint radial traces show values from the preceding 12-85 ms of simulation time.

The indicators and raw T23 plot share one clock. One simulated second is played over 18 seconds, with a brief pause at the load-step marker. The same physical ticks and torque axis are used for both cases. `evidence/shaft_twist_revision.json` records the exact baseline, scale and observed values. The original six small rotor pointers remain available in the preserved previous video.

For generator-terminal power over 1.5-30 s, with a 100 ms ramp interval:

| Metric | Without BESS | With BESS | Reduction |
|---|---:|---:|---:|
| Power standard deviation | 106.7735 MW | 55.1936 MW | 48.3078% |
| Maximum absolute ramp | 2541.6625 MW/s | 260.4880 MW/s | 89.7513% |

These values are freshly recalculated in `data/metrics.json`. They differ slightly from the original report's downstream Pgrid metrics because the measurement locations differ.

The selected step shows a smaller fast shaft-torque excursion with BESS. **This is an observed trace comparison, not a quantified physical damping benefit.** In the source validation, BESS torsional modal amplitudes changed by about -67.8% and -67.3% when the EMTDC step was reduced from 10 to 5 microseconds. Modal frequencies and shapes passed the existing checks, but amplitude convergence and damping benefit were not established. This limitation appears in the video and is preserved in `evidence/existing_pscad_validation.json`. No damping ratio, fatigue-life improvement or energy-saving claim is made.

## Parameters from the existing model

- Load command: 250-500 MW; full-range transition: 20 ms.
- Generator and shaft base: 1000 MVA; generator terminal voltage: 20 kV; nominal frequency: 60 Hz.
- Three-mass inertia constants: 1.5, 1.0 and 2.5 s; nominal speed: 3600 rpm.
- Native shaft stiffness inputs: 40 and 50; mutual damping inputs: 1 and 1. Consult the native component for its per-unit parameter convention.
- BESS: 250 MW / 125 MWh equivalent; initial SOC: 50%; configured SOC window: 20-80%.
- Smoothing time constant: 2 s; reference ramp limit: 25 MW/s. This controller reference limit is not a guarantee that every measured generator-terminal ramp is below 25 MW/s.
- EMTDC step: 10 microseconds; output sample step: 100 microseconds; archived run duration: 30 s.

## Reproduce

Requirements: Python 3.11, a TeX installation with `latex` and `dvisvgm` on PATH, and FFmpeg/FFprobe on PATH. The official Schemdraw 0.23 core and electrical-elements subset is included under `vendor/`, with its license and upstream blob identities; it needs no separate installation. A normal Schemdraw 0.23 distribution can also be used.

From this directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe diagram_assets.py
.\.venv\Scripts\python.exe shaft_twist.py
.\.venv\Scripts\python.exe -m unittest test_data_pipeline test_shaft_twist
.\.venv\Scripts\python.exe render_video.py --preview
.\.venv\Scripts\python.exe render_video.py
.\.venv\Scripts\python.exe verify_delivery.py
```

The supplied `data/display.npz` allows standalone rendering without a PSCAD installation. `data/raw_selected.npz` contains all selected original samples; `data/provenance.json` maps them to source channels and source-file hashes. To re-extract from the original project, run:

```powershell
py -3.11 data_pipeline.py --project-root C:\CODES\data-center
```

The evidence snapshots include the exact executed .pscx files, .inf metadata and receipts. Full .out blocks remain in the original project; this video package carries the selected raw channels rather than duplicating all switch/gate diagnostics. To run the actual native simulation again, use the parent project's PSCAD workflow and licensing requirements.

## Files

- `scenes.py`, `visuals.py`: editable animation and typography.
- `shaft_twist.py`, `twist_visuals.py`: baseline-relative shaft data, large indicators, arcs, trails and MathTex readouts.
- `diagram_assets.py`, `assets/`: Schemdraw vector symbols and circuit.
- `data_pipeline.py`, `source_reader.py`: verified extraction and metric calculation.
- `render_video.py`: rendering, chapters, MP4 assembly and review frames.
- `verify_delivery.py`: dataset, source protection, video decoding and payload verification.
- `data/`: portable raw/display arrays, metrics and provenance.
- `evidence/`: receipts, source snapshots, review notes, frame inspections and technical checks.

## Upstream references

- [Manim configuration](https://docs.manim.community/en/stable/guides/configuration.html).
- [Manim SVGMobject](https://docs.manim.community/en/stable/reference/manim.mobject.svg.svg_mobject.SVGMobject.html).
- [Schemdraw usage and SVG export](https://schemdraw.readthedocs.io/en/0.23/usage/start.html).
- [Official Schemdraw source](https://github.com/cdelker/schemdraw).
