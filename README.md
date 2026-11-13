# Hourly Capital Bikeshare use, 2024-2025

Machine Learning individual course project by **Yuan Kaige**, student ID **202612231033**.

Repository: https://github.com/Yuan-KG/Project_BikeSharing

This study combines exploratory data analysis and regression to estimate hourly **recorded departures**. It does not measure unmet demand. ERA5 weather is retrospective reanalysis, so the results describe estimation conditional on known weather rather than a verified advance forecast.

## Main findings

All 24 official monthly archives contain 12,776,970 raw rows. The documented identity and DST rules assign 12,775,602 departures to 17,540 eligible hourly targets: 8,782 in 2024 and 8,758 in 2025. Four unresolved autumn target hours remain missing. There are no zero-hour bins after coverage checks.

Settings were selected using three expanding 2024 validation windows. All six locked regressors were refitted on full 2024 and compared with the same baseline on identical 2025 hours. The validation-selected primary model is histogram gradient boosting with calendar and weather features.

| Model | Inputs | Test MAE | Test RMSE | Test R² |
|---|---|---:|---:|---:|
| Weekday-hour mean | Calendar | 240.98 | 347.01 | 0.702 |
| Ridge | Calendar | 216.32 | 307.07 | 0.767 |
| Ridge | Calendar + weather | 201.83 | 284.63 | 0.800 |
| Random forest | Calendar | 188.54 | 290.81 | 0.791 |
| Random forest | Calendar + weather | 168.79 | 250.80 | 0.844 |
| Histogram gradient boosting | Calendar | 190.73 | 288.48 | 0.794 |
| Histogram gradient boosting | Calendar + weather | 166.43 | 241.86 | 0.855 |

Errors are in rides/hour. Adding weather reduces gradient boosting RMSE from 288.48 to 241.86 (16.16%). Weather also helps the other two families on 2025, although the selected weather Ridge candidate is worse than calendar-only Ridge in pooled 2024 validation. The primary model has larger absolute errors at weekday peaks, during wet hours and in hot conditions. Its monthly bias changes sign during 2025. These are predictive findings, not causal effects.

## Files

- `BikeSharing_2024_2025.ipynb`: fully executed notebook, with real tables, charts and validation checks.
- `BikeSharing_2024_2025.html`: optional read-only notebook view.
- `src/acquire.py`: official source listing, streaming downloads, archive CRCs, hashes and provenance.
- `src/prepare.py`: chunked quality audit, disk-backed ID index, DST policy, UTC aggregation and weather alignment.
- `src/experiment.py`: train-only pipelines, chronological validation, fixed model selection, test evaluation and figures.
- `src/build_report.py`, `src/prepare_slides.py`: derive report and slide values from the saved experiment results.
- `data/raw/`: original ZIPs locally, ERA5 JSON and download manifests. The original ZIPs are excluded from Git.
- `data/processed/hourly_model_data.csv`: derived hourly study table, including explicit target-status flags.
- `data/processed/unresolved_dst_counts.csv`: preserved ambiguous fall-back local counts.
- `results/`: complete audit, validation candidates/folds, selection lock, test predictions, metrics, chart data and figures.
- `report/report.pdf`: 10-page English report, including references, in the linked ICML style with 10-point Times body text.
- `report/report.tex`, bibliography, style and generated tables: editable report source.
- `presentation/BikeSharing_Presentation.pptx`: seven-slide English deck with editable native charts and matching speaker notes.
- `presentation/English_Script.md`: 574-word script, with timing targets for a 4-5-minute talk.
- `presentation/Questions_and_Answers.md`: likely questions with short English answers and Chinese explanations.
- `中文理解笔记.md`: Chinese explanation of the research, methods, results and limitations.
- `DATA_SOURCES.md`: sources, time semantics, licenses and attribution.
- `environment/`: actual dependency versions and project-local Jupyter launch helper.
- `REQUIREMENTS_CHECK.md`: teacher-file requirements and the course-specific interpretation of ICML instructions.

## Reproduce on the author's computer

The experiment used the installed `E:\Anaconda3\python.exe`. No dependency installation into the existing environment and no system PATH change were needed. Actual Python and library versions are saved in `environment/requirements.txt` and `results/summary.json`.

1. Keep this directory structure and allow about 0.5 GB for the official compressed downloads, plus several GB for temporary processing space.
2. Run `environment/launch_notebook.cmd`, choose the project kernel, and run the notebook from top to bottom.
3. The first acquisition needs internet access. Verified existing raw archives are reused. Do not replace them with a different dataset under the same names.

The stages can also be run from PowerShell at the project root:

```powershell
& 'E:\Anaconda3\python.exe' src/acquire.py
& 'E:\Anaconda3\python.exe' src/prepare.py
& 'E:\Anaconda3\python.exe' src/experiment.py
& 'E:\Anaconda3\python.exe' src/build_report.py
```

The final notebook was executed sequentially in a fresh Anaconda kernel, with zero error outputs and zero stderr warnings. The saved predictions reproduce the reported metrics. A recorded SVD numerical correction leaves all selected model settings unchanged; it does not introduce test-based tuning. See `results/notebook_execution_check.json` and `results/numerical_stability_check.json`.

For another computer, create an independent course environment with compatible versions, update the notebook interpreter assertion, and regenerate the local kernel specification. No claim of bit-for-bit equality across other platforms is made.

## Report and presentation source

The report uses the ICML 2019 LaTeX style explicitly linked by the teacher: https://media.icml.cc/Conferences/ICML2019/Styles/icml2019_style.zip . The course requirement of 8-10 total pages takes precedence over the conference's submission page limits. The report source changes the conference notice to identify a course project and supplies the author's actual information without inventing an institution or email.

Use `report/build_report.cmd` with a LaTeX installation, or upload the report source and `results/figures/` with their relative paths to Overleaf. With pdfLaTeX, the original style loads Times; the delivered PDF was compiled using XeTeX/Tectonic and installed Times New Roman. Fonts are embedded in the PDF. Windows font files are not redistributed. The full report source and figures are also included in `report/Report_Source.zip`.

The PPTX contains native chart data and text, so ordinary PowerPoint editing does not need the authoring tools. `presentation/build_deck.mjs` documents the bundled Codex artifact runtime used to author it; it is separate from the experiment environment. Preview PNGs come from re-importing the final exported PPTX. Native PowerPoint was not used to claim visual verification.

## Data sources and license notices

Capital Bikeshare: https://capitalbikeshare.com/system-data and official monthly downloads at https://s3.amazonaws.com/capitalbikeshare-data/index.html . Use is governed by https://capitalbikeshare.com/data-license-agreement . Original ZIPs remain local and are not redistributed as a stand-alone dataset. The derived hourly table is supplied as source material for this non-commercial study. No endorsement is implied.

Weather data by [Open-Meteo.com](https://open-meteo.com/), ERA5 reanalysis from the Copernicus Climate Change Service. API data are provided under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Modifications: variable selection, alignment of precipitation to its preceding-hour interval, and joining to derived hourly departure counts. Exact request metadata are retained. Details: `DATA_SOURCES.md`.

## Repository upload and submission

The local research package is ready to upload. Exclude original ZIPs, `.part` downloads, SQLite caches, temporary authoring files and Jupyter checkpoints using the supplied `.gitignore`. Do not apply a code license to third-party data or the ICML style files. `GITHUB_UPLOAD.md` gives account-controlled upload steps.

The teacher requests electronic submission through 学习通. Confirm the due date in the class schedule and rehearse the talk to stay within 4-5 minutes, followed by 1 minute of questions. The supplied PDF states a 10% per-day late penalty.
