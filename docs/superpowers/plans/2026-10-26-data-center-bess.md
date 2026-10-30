# Data Center BESS Implementation Plan

> **For agentic workers:** Execute inline with superpowers:executing-plans. User authorized the full preceding prompt.

**Goal:** Two executable PSCAD 5.1 data-center cases with a switched BESS, measured comparison, SOC protection, and portable delivery.

**Architecture:** Shared 69/13.8 kV network and deterministic 4–10 MW load; 5 MW/2.5 MWh battery with native switches and grid-following control. Add smoothing and SOC recovery while retaining physical energy limits.

**Tech Stack:** PSCAD 5.1, installed mhi.pscad, GFortran, Python 3.11, numpy/matplotlib.

**Spec:** The user's approved 12-part prompt in this conversation; concrete values and acceptance requirements retained below.

## Global Constraints
- Preserve originals. Work under C:/CODES/data-center.
- Same 30 s load profile and numerical configuration for both nominal cases.
- Editable .pscx and relative .pswx; actual EMTDC evidence, never synthetic substituted results.
- Native components first; battery energy 2.5 MWh, +/-5 MW, SOC 20–80%, initial 50%.
- 69 kV/60 Hz/1000 MVA/XR10 source; 20 MVA 69/13.8 kV transformer, 8% impedance.
- Load 4–10 MW, PF .98; 2 s smoothing, .5 MW/s ramp, slow SOC recovery.

## Review Focus
- Correct battery sign and actual current blocking near SOC limits.
- Energy accounting includes DC capacitor and losses.
- Same consumption and processing between compared cases.
- Final saved topology and output receipts match.
- Workspace relocates without absolute dependencies.

## Tasks and verification
1. [x] Environment and source inspection: licensed PSCAD 5.1.0, GFortran 8.1, task-owned PID 36080/port 62172; native battery/ports inspected. Official BESS guide is reference only; archive download blocked, not a dependency.
2. [x] Model construction: editable native power circuits, embedded readable control/audit definitions, and native graphs compiled and ran.
3. [x] Final eight-run suite: 30 s base and BESS, 6 s low/high SOC, 5 s idle-loss regression, 5 s coarse/fine, 1 s switching at 5 us. Fresh source-bound receipts; all runs completed without errors. Final nominal cases saved at 30 s, 10 us, 100 us, SOC 50%.
4. [x] Analysis reader RED/GREEN 3 tests; native artifact RED/GREEN 2 tests; final numerical validation PASS 44/44; comparative figures and native exports visually verified.
5. [x] Delivery: README.md and validation/RELATORIO.md; independent review and three corrections in validation/REVIEW.md; clean-directory relocated 2.5 s simulations both PASS with identical compared channels; 160 payload files in ZIP plus manifest, CRC and every SHA-256 verified PASS in delivery/package_verification.json.

## Progress and decisions
- Initial directory empty, PSCAD 5.1 and Python mhi.pscad installed; license not yet checked.
- Ruling: proceed directly with approved prompt, without a second planning approval. This is an engineering artifact folder, not an existing git branch; keep the plan and evidence locally.
- Ruling: use native Shepherd battery and direct DC connection. Custom open-text controls and energy audit are embedded in each .pscx, with no external compiled dependency. No device/manufacturer loss or thermal claims.
- Fixed: the native #LOCAL directive accepts one variable per line; expanded declarations after compiler diagnostics.
- Fixed: grounded DC negative plus grounded AC neutral created an unintended diode path. Isolated DC with 1 Mohm earth reference eliminated it in a fresh native run.
- Ruling: lower branch short-circuit threshold to 1e-8 ohm so the 50 micro-ohm IGBT on-state resistance remains represented.
- Ruling: at SOC limits, use an allowed recovery bias of 2% rated power to cover converter idle losses; zero AC command alone does not guarantee zero battery discharge.
- Initial validation includes all samples in pulse windows (including 2.65–3.72% saturation). Reduction goals pass without discarding these intervals. The .5 MW/s value limits the grid reference, not every measured transient; actual maximum is reported.
- Final review corrections: low-SOC idle-loss protection applies to every command, native timestep gross energy integrals eliminate sampled-PWM alias, validator exits nonzero on failure, and the suite ends with nominal configurations. Each physical correction has actual regression evidence.
- Native graph API settings alone left old per-instance Y limits in PSCAD 5.1. Updated both native definition and instance view records, reopened, reran the final nominal files and inspected native bitmap exports. No electrical topology change was made for this presentation correction.
- Accepted compiler notices: six real-to-integer gate conversion warnings when BESS code is generated. The controller emits exactly 0.0 or 1.0 and generated switch calls use NINT; logical gate overlap checks pass. Zero build/runtime errors. Warning counts and full messages are retained in the delivered report and receipts.
- Final outcome: 51.5991% lower grid-power standard deviation and 89.6670% lower maximum measured 100 ms ramp over 0.6–30 s. Energy comparisons are not labeled energy savings because final stored energy differs.
