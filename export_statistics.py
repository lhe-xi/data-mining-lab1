"""Reproduce the student's recorded computations to export report statistics only."""
from pathlib import Path
import contextlib
import io
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parent
nb=json.loads((root/'lab1.ipynb').read_text(encoding='utf-8'))
cells=[c for c in nb['cells'] if c['cell_type']=='code']
assert len(cells)==16
namespace={'display':lambda *args,**kwargs:None,'plt':plt}
capture=io.StringIO()
plt.show=lambda *args,**kwargs:plt.close('all')
with contextlib.redirect_stdout(capture):
    for i in [1,6,7,8,9,11,12,14,15]:
        exec(compile(''.join(cells[i]['source']),f'lab1.ipynb code cell {i+1}','exec'),namespace)
n=namespace
assert n['X_missing'].isna().sum().sum()==156
assert len(n['X_drop'])==78
assert n['iqr_mask'].sum().sum()==42 and n['z_mask'].sum().sum()==13
assert n['X_capped'].loc[0,'magnesium']==131.5
assert n['y_onehot'].shape==(178,3)
pd=n['pd']
stats=pd.DataFrame({
    'before_mean':n['X_capped'].mean(),
    'before_std':n['X_capped'].std(ddof=0),
    'minmax_mean':n['X_minmax'].mean(),
    'minmax_std':n['X_minmax'].std(ddof=0),
    'z_mean':n['X_zscore'].mean(),
    'z_std':n['X_zscore'].std(ddof=0),
})
stats.to_csv(root/'tables/scaling_before_after.csv',encoding='utf-8-sig',float_format='%.6f')
n['missing_summary'].to_csv(root/'tables/missing_by_feature.csv',encoding='utf-8-sig',float_format='%.6f')
(root/'evidence/28_report_statistics_reproduction.txt').write_text(
    'Report statistics export using original code cells 2,7,8,9,10,12,13,15,16.\n'
    'No Notebook modification. Existing results independently matched: missing=156, drop rows=78, IQR=42, Z-score=13, capped injection=131.5, onehot=(178,3).\n'
    'Scaling comparison std uses ddof=0 for all stages. Newly exported values are actual rerun statistics, not inferred from figures.\n\n'+capture.getvalue(),encoding='utf-8')
print(stats.round(4).to_string())
