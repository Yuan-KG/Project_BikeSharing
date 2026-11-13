# Account-controlled GitHub upload

Destination supplied by the author: https://github.com/Yuan-KG/Project_BikeSharing

This research package is ready for the account owner to upload. Raw monthly ZIPs and temporary caches are excluded by `.gitignore`; the small derived hourly table, code, executed notebook, report, slides, sources and manifests are included. Keep these together as a non-commercial study rather than publishing a stand-alone data mirror.

If the target repository is empty, open a terminal in `E:\MachineLearning\Project_BikeSharing` and run the commands below with your installed Git. Complete any GitHub browser sign-in yourself. First check `git status` and the staged file list before pushing. If the remote already has commits, fetch and review them rather than force pushing or overwriting existing work.

The delivered local directory has already been initialized on `main`, the remote has been configured, and 117 files (about 11 MB) have been staged. All 24 original ZIPs are excluded. When using that prepared directory, skip the first three commands below and start with `git status`. Git author name/email are not configured on this computer; use your own real identity before committing.

```powershell
git init -b main
git remote add origin https://github.com/Yuan-KG/Project_BikeSharing.git
git add .
git status --short
git diff --cached --stat
git commit -m "Add bikeshare course study and reproducible results"
git push -u origin main
```

Use your own Git author identity if Git requests one. Do not invent an email address. Do not use `--force`. Verify the notebook, processed table, report PDF and PPTX appear on the destination page, and test that the report's repository link is accessible to the teacher.

The report already contains the URL supplied by the author. A supplied URL alone is not evidence that the materials have been published. The delivery verification record distinguishes local files from any remote publication.
