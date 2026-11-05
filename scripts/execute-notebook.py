#!/usr/bin/env python3
"""Execute a clean notebook with a private, package-local kernel definition."""
from pathlib import Path
import os,sys,json
root=Path(__file__).resolve().parents[1]
for key,folder in {'JUPYTER_CONFIG_DIR':'jupyter/config','JUPYTER_DATA_DIR':'jupyter','JUPYTER_RUNTIME_DIR':'jupyter/runtime','IPYTHONDIR':'ipython','MPLCONFIGDIR':'matplotlib'}.items():
    path=root/'.runtime'/folder;path.mkdir(parents=True,exist_ok=True);os.environ[key]=str(path)
os.environ['JUPYTER_PATH']=str(root/'.runtime/jupyter')
kernel=root/'.runtime/jupyter/kernels/ejps-normalized-local';kernel.mkdir(parents=True,exist_ok=True)
(kernel/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'DAMADI E.03 (local)','language':'python'}))
import nbformat
from nbclient import NotebookClient
source=root/'notebooks/01-reproduce-ejps-analysis.ipynb'
nb=nbformat.read(source,as_version=4)
for cell in nb.cells:
    if cell.cell_type=='code':cell.execution_count=None;cell.outputs=[]
NotebookClient(nb,timeout=1200,kernel_name='ejps-normalized-local',resources={'metadata':{'path':str(root/'notebooks')}}).execute()
nb.metadata['damadi_execution']={'entry_code':'E.03--MS-DA-CR','clean_kernel':True,'source_notebook':source.name,'scope':'Frozen retained revision only'}
destination=root/'executed-notebooks/01-reproduce-ejps-analysis.executed.ipynb';destination.parent.mkdir(exist_ok=True)
nbformat.write(nb,destination)
print('Clean notebook execution complete:',destination.name)
