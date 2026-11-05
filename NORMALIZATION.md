# Normalized computational companion

This unreleased update carries the shared execution and approved figure presentation from DAMADI archive v0.1.1, E.03 manuscript/presentation edition 0.1.6, into the private EJPS repository.

Deposited inputs, targets, supplied analysis products, independent checker, restoration helper, submitted figures, license and reviewer guide are retained. The eight CSVs and numerical summary remain the scientific targets. Mathematical function bodies match the archive; only initialization, project paths, output protection and run metadata are adapted.

scripts/reproduce.py is the readable numerical entry point and keeps --data-dir and --output-dir. The older alternative checking-plot construction is replaced by the approved exports available through ./run.sh. A direct numerical reconstruction does not require R. Existing check_results.py, verify_files.py and materialize_inputs.py commands remain available.

The notebook runs the same analysis functions. A fresh private kernel writes executed-notebooks/; source notebooks have no saved outputs. Script and notebook outputs go to reproduced/ and verification/, with disposable caches under .runtime/.

figures/ contains three exact approved normalized PDFs. manuscript-figures/ retains the four deposited assets, including the historical table and original PNG impact plot. These are retained sources; new plot exports are PDFs only.

The waffle retains no upper coordinate axes, equal layout-row heights, subclass offset +0.45 and vjust = 0.2. Impact: 156 x 90 mm. Waffle: 156 x 122.218 mm. Stratum: the author's Quartz profile, 7 x 4 inches, size legend and 8.5-point x-axis labels. Its manuscript inclusion is 156 mm wide. These approved exceptions are preserved.

The Python-only route avoids the additional graphics dependencies. Approved figure exports require the separately documented R packages, rsvg-convert, macOS Quartz and command-line compiler tools. Fonts are registered within the process. No new cross-platform graphical certification is claimed.

The existing Zenodo DOI identifies the deposited scientific baseline, not a newly released normalized update. A later release should identify these execution/presentation changes explicitly. The fixed archive and research originals remain separate.
