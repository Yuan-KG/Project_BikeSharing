# Runtime

The actual experiment uses the existing `E:\Anaconda3\python.exe`. No packages were installed into or removed from that environment and system PATH was not changed. `requirements.txt` records the versions needed for the experiment. `results/summary.json` records the versions used by the executed notebook.

From the project root, run:

```powershell
& 'E:\Anaconda3\python.exe' src/acquire.py
& 'E:\Anaconda3\python.exe' src/prepare.py
& 'E:\Anaconda3\python.exe' src/experiment.py
```

Use `launch_notebook.cmd` to open Jupyter with the project-local kernel specification. The notebook can be run from top to bottom and executes all three stages itself. Raw-data acquisition requires internet access and approximately 0.5 GB of downloads. The chunked audit uses a temporary SQLite identity index in `work/`; leave a few GB of free disk space. It is a derived cache and can be regenerated.

For a different computer, create a separate conda course environment rather than modifying an existing base environment. Update the notebook interpreter assertion and project-local kernel specification to the new environment path, then rerun all cells. Do not claim bit-for-bit equivalence across different library versions or CPU platforms.

The report is editable LaTeX using the original ICML 2019 style linked by the teacher. Compile `report/report.tex` with a LaTeX distribution, or open the complete `report/` directory and figures in Overleaf. The project includes `report/build_report.cmd`. A portable Tectonic compiler was used for this delivery without adding it to PATH. Report/slide authoring tools are separate from the Anaconda experiment environment.
