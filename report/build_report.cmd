@echo off
setlocal
cd /d "%~dp0.."
"E:\Anaconda3\python.exe" src\build_report.py
if errorlevel 1 exit /b 1
cd report
where pdflatex >nul 2>nul
if errorlevel 1 (
  echo Use a LaTeX installation or upload the project source and result figures to Overleaf.
  echo Select pdfLaTeX with report/report.tex as the main file.
  exit /b 1
)
pdflatex -interaction=nonstopmode -halt-on-error report.tex
if errorlevel 1 exit /b 1
bibtex report
if errorlevel 1 exit /b 1
pdflatex -interaction=nonstopmode -halt-on-error report.tex
pdflatex -interaction=nonstopmode -halt-on-error report.tex
endlocal
