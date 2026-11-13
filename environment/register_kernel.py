"""Create a project-local Jupyter kernel specification; no global registration."""
from pathlib import Path
import json, sys
root=Path(__file__).resolve().parents[1]
directory=root/'work/kernels/anaconda-course'
directory.mkdir(parents=True,exist_ok=True)
(directory/'kernel.json').write_text(json.dumps(dict(argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],display_name='Anaconda course project',language='python')),encoding='utf-8')
print(directory)
