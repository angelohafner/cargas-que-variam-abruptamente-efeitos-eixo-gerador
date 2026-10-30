# BESS and Abrupt Loads Video Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Render an English 1080p Manim/Schemdraw film from the existing PSCAD comparison, with minimal prose and all mathematics/numerals in LaTeX.

**Architecture:** Verify and extract the archived generator cases, animate their real channels, then inspect rendered frames and package reproducible sources and data. Keep the original models, runs and archives intact.

**Tech Stack:** Python 3.11, Manim 0.21, Schemdraw 0.23, NumPy, SciPy, LaTeX/dvisvgm, FFmpeg.

**Spec:** The user's approved prompt in the conversation, refined by the instruction to use the existing PSCAD results.

## Global Constraints

- All visible video content in English; few words; variables, numbers and units rendered with MathTex.
- No visible data-center references. Illustrative application icons are not separate PSCAD simulations.
- Use the same load command and analysis windows for with/without comparisons.
- Preserve the actual three-mass model and distinguish electromagnetic and shaft torque.
- The existing BESS torsional amplitudes are not timestep-converged: do not claim physical damping improvement or invent numerical torsional benefits.
- New artifacts belong in video/BESS_Load_Smoothing. This folder is not a Git checkout; no branch or commits apply.

## Review Focus

1. Correct channel mapping, receipt/output integrity and matched timelines.
2. Generator-terminal power distinguished from downstream Pgrid measurements.
3. Power smoothing disclosed; raw shaft torque retained in a slow-motion zoom.
4. No fabricated shaft damping claim or misleading independent vertical scales.
5. English-only visible wording, LaTeX numerical labels, unclipped graph content.

### Task 1: Verified data and provenance

- [x] Add and run failing tests for mismatched timelines/load commands and numerical metric windows.
- [x] Implement data_pipeline.py using the project's source-bound reader, retaining full-rate selected channels in raw_selected.npz and reducing only display traces.
- [x] Recompute power metrics, record channel mapping, hashes, source snapshots and torsional limitations.
- [x] Verify tests and compare downstream metrics to the existing audit.

### Task 2: Storyboard and render

- [x] Create Schemdraw SVG symbols and Manim scenes: applications, parallel circuit, abrupt rise/fall, same-demand power comparison, three-mass shaft, real torque zoom, measured benefits and limitation.
- [x] Render keyframes/preview and inspect typography, mathematics, bounds, synchronization and honest shaft scaling.
- [x] Render all scenes at 1920 by 1080 and 30 fps, concatenate to a chaptered MP4.

### Task 3: Validation and delivery

- [x] Probe and fully decode the MP4, verify geometry/duration/frame rate, generate a contact sheet and inspect representative frames.
- [x] Write README, dependency lock, source/data manifest and reproduction commands.
- [x] Request independent read-only review, address material findings and verify the package CRC and payload hashes.

## Execution ledger

Ruling: Execute within the approved scope without another approval gate; the user explicitly requested full execution and reasonable implementation decisions.

Ruling: Reuse completed PSCAD runs instead of launching new simulations; their receipts and channel data will be verified freshly. No claim of a new EMTDC run will be made.

Ruling: Keep torsional content focused on mechanism and observed traces. The available evidence does not support a quantified damping benefit.

Ruling: Download the official Schemdraw core and electrical-elements source through the available GitHub connector because shell package networking is unavailable. Preserve upstream file identities and license.

Task 1: complete. Five data-pipeline tests pass; source/output hashes and archived downstream metrics match.
Task 2: complete. Seven final 1080p/30 fps chapters assembled into a 110.3-second silent English film; typography and circuit spacing reviewed and corrected.
Task 3: complete. Independent review has no Critical/Important findings; 52/52 delivery checks pass; 3309 frames decoded; 110-file ZIP passes CRC and all SHA-256 payload checks.
