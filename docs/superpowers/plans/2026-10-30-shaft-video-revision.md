# Shaft Twist Video Revision Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this approved revision.

**Goal:** Make the measured shaft response visible with two large, equally scaled twist-change indicators.

**Architecture:** Preserve the first delivery; replace only ShaftMechanism using the existing PSCAD theta2/theta3 and T23 channels; reuse the other six rendered chapters unchanged, then reassemble and validate the deliverable.

**Tech Stack:** Existing Python/NumPy/Manim/LaTeX/FFmpeg environment.

**Spec:** The user's approval of the proposed large paired indicators, zero pre-step baseline, common magnification, colored arcs, pointer trails and synchronized torque plot.

## Global Constraints

- English-only visible content, sparse text, MathTex for variables/numbers/units.
- Common gain 200 for both cases, no independent normalization.
- Twist change is theta2 minus theta3, minus its mean over 1.8 <= t < 1.95 s.
- Preserve all original PSCAD data. Show the same 1.8-2.8 s event and retain the documented torsional convergence limitation.
- Preserve the previous video and complete ZIP with SHA-256 evidence.

## Review Focus

- Baseline and common rigid-body motion do not contaminate the twist signal.
- The same gain preserves the actual amplitude ratio and is visible on screen.
- Large needle, arc, trail and raw T23 plot share the same simulation clock.
- No clipping or overlaps at maximum excursion or with changing numeric readouts.
- The other six chapter files remain byte-for-byte unchanged.

### Task 1: Data transform and preservation

- [x] Preserve the previous video, package and editable source; hash unchanged chapters.
- [x] Add failing tests for baseline removal, common-rotation invariance, scale preservation and malformed baseline.
- [x] Implement the twist transform and a recorded summary of the observed event.

### Task 2: Scene revision

- [x] Replace small pointers with two large gauges, common physical ticks, colored arcs and recent pointer trails.
- [x] Add the highlighted three-mass context and synchronized raw T23 chart.
- [x] Inspect preview frames at baseline, event response and peak before final rendering.

### Task 3: Delivery

- [x] Render the revised chapter at 1080p/30 fps and reassemble with the unchanged chapters.
- [x] Refresh documentation, independent review, visual evidence, full-video decode, numeric and preservation checks.
- [x] Deliver updated full video, isolated revised scene and verified complete ZIP.

## Rulings

The user already approved this design and execution. No further design approval is needed.
This directory is not a Git checkout. File snapshots and the previous complete ZIP preserve the source history.
The comparison is an observed transient response; no damping ratio or general torsional benefit is inferred.

## Completed verification

Eleven numerical unit tests pass. Final delivery verification: 63/63 checks; 118.2 s; 3546 decoded frames. The standalone revised chapter is 24.6 s. All six other chapter hashes and all preserved historical files match. ZIP CRC and every payload SHA-256 passed. Independent review found no Critical/Important or material Minor issues.
