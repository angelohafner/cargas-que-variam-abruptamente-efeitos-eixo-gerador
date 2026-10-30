# GitHub snapshot

Repository: https://github.com/angelohafner/cargas-que-variam-abruptamente-efeitos-eixo-gerador

This repository contains the current editable PSCAD models and relative workspace, Python study scripts and tests, the current 250-500 MW result summaries and figures, native execution receipts and metadata, and the final five-scene Manim/Schemdraw video with its source and numerical data.

The selected raw numerical channels (`raw_selected.npz`, 66.5 MB) are stored as three byte-preserving transport parts in `data_archives/raw_selected/` because of the publishing integration's per-request limit. Run `py -3.11 scripts/restore_video_data.py` once after cloning. The script verifies every part and the reconstructed file against the original SHA-256 and preserves any existing mismatched file. The smaller `display.npz` is included directly in the video directory. These data preserve the published film's reproducibility without installing PSCAD. See its README for the Python, LaTeX and FFmpeg dependencies. The complete video ZIP can be rebuilt locally from the published files after restoration and validation.

Full EMTDC `.out` blocks, compiler build directories, portability extraction copies, historical backups, obsolete render caches and large duplicate ZIP deliveries remain in the authoring workspace. They are not part of this GitHub snapshot. Their source receipts and hashes remain in the evidence. Older documentation and receipts can refer to these local-only paths; they are not downloadable repository files.

The full native simulations can be rerun using the current `scale` / `250_500` workflows and a licensed PSCAD installation. Repository publication reuses the existing verified simulation results and does not claim a new PSCAD execution.

## Validation from a clone

```powershell
py -3.11 scripts/restore_video_data.py
py -3.11 -m unittest discover -s tests
Set-Location video/BESS_Load_Smoothing
py -3.11 verify_delivery.py
py -3.11 package_video.py
```

Use `verify_delivery.py` without `--project-root` for this portable repository snapshot. Checks against full original `.out` blocks, local history and cached individual chapter clips require the authoring workspace. Rendering the film with `render_video.py` regenerates its chapter clips.

Historical review records describe their own revision and scope. The current delivery and package verification reports identify the current video by SHA-256; repository integrity is listed separately in `GITHUB_MANIFEST.json`.

`.gitattributes` disables automatic line-ending conversion so the model and evidence hashes remain valid on checkout.
