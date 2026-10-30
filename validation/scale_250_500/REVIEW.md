# Independent engineering review — 250–500 MW revision

Date: 2026-10-26. Reviewer: fresh-context `scale_final_review` agent; read-only inspection, no PSCAD session access. Final assessment: **ready for packaging and delivery after archive integrity verification; no open Critical or Important findings**.

## Evidence reviewed

- Physical scaling: 1000 MVA common base, 230/34.5 kV network, 20 kV generator, 250 MW/125 MWh equivalent BESS.
- Network impedance, current limits and current-controller gains, battery capacity/Inom percentage, aggregate filter/capacitor, transformer and energy-audit constants.
- Native machine `MM=0`, three-mass units 12/9b, generator on mass 3, gas power converted to torque at driven mass 1.
- 14 independently executed Python tests: PASS.
- Final numerical validation: 168/168 PASS. All four canonical source hashes match the final 30 s run receipts.
- Relocated execution: 4/4 PASS, exactly zero differences in compared channels over 6 s; canonical hashes preserved.
- Default intermittent profiles, optional experiment defaults, saved graph axes, scientific figures and representative native exports.

## Findings and resolutions

1. Important, resolved: portability verification reused fixed output directories, preventing repeat execution or use from an extracted package with prior evidence. `verify_scale_portability.py` now uses unique timestamped directories and records their actual paths.
2. Minor, resolved: packaging required old archives absent from an extracted current package. `package_scale_250_500.py` now verifies historical archives when their records exist and explicitly reports when they are not included. In the authoring workspace, all three historical archives remain subject to hash verification.

The main implementer also corrected native graph ranges in both PSCAD parameter-list overrides, synchronized optional experiment definition defaults, removed the ideal-source Scc annotation from generator cases, and corrected UTF-8 encoding in the root guide links. Final source-bound runs include those model changes.

## Scope decisions

- Manufacturer realism and installation design: outside this authorized didactic aggregate study. No manufacturer calibration or construction-ready equipment rating is claimed.
- Quantitative torsional damping benefit: not established. BESS modal amplitudes change −67.81% and −67.27% when the EMTDC step changes from 10 to 5 µs. Frequencies and shapes pass; amplitude convergence and physical damping benefit do not follow from that result. This limitation is explicit in the report and guide.
- Arbitrary adjusted sweeps and long-duration battery operation: available for further experiments, but not certified by the executed intermittent-profile, pulse and SOC-boundary tests.
- Archive integrity: outside the review because packaging followed it. The packaging tool must verify CRC and every payload SHA-256 and bind the delivered canonical files to the validated and relocated sources. Results are recorded separately in `delivery/scale_250_500_package_verification.json`.

All scope decisions were accepted by the implementer; no requested model or execution work was waived.
