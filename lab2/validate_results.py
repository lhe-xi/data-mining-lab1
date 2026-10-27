"""独立从保存的预测重算指标，并在指定时从头复跑核对稳定性。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,roc_auc_score,confusion_matrix

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'final_results'
parser=argparse.ArgumentParser();parser.add_argument('--rerun',action='store_true');args=parser.parse_args()
table=pd.read_csv(OUT/'comparison.csv')
split=pd.read_csv(OUT/'split_indices.csv')
assert len(split)==569 and split.row_index.nunique()==569
assert (split.subset=='train').sum()==398 and (split.subset=='test').sum()==171
for row in table.itertuples():
    p=pd.read_csv(OUT/f'{row.model}_{row.phase}_predictions.csv')
    assert len(p)==171 and p.row_index.nunique()==171
    assert np.array_equal(p.row_index,split.loc[split.subset=='test','row_index'])
    assert np.array_equal(p.y_true,split.loc[split.subset=='test','original_label'])
    assert np.isfinite(p.prob_malignant).all() and p.prob_malignant.between(0,1).all()
    computed=[accuracy_score(p.y_true,p.y_pred),precision_score(p.y_true,p.y_pred,pos_label=0),
        recall_score(p.y_true,p.y_pred,pos_label=0),f1_score(p.y_true,p.y_pred,pos_label=0),
        roc_auc_score(p.y_true==0,p.prob_malignant)]
    assert np.allclose(computed,[row.accuracy,row.precision,row.recall,row.f1,row.auc],atol=1e-12)
    assert np.array_equal(confusion_matrix(p.y_true,p.y_pred,labels=[0,1]).ravel(),[row.TP,row.FN,row.FP,row.TN])
print(f'PASS: {len(table)} prediction files independently reproduce all metrics and confusion matrices.')
meta=json.loads((OUT/'metadata.json').read_text(encoding='utf-8'))
for name,s in meta['search'].items():
    cv=pd.read_csv(OUT/f'{name}_cv.csv')
    assert len(cv)==s['candidate_count']
    assert np.isclose(cv.mean_test_score.max(),s['cv_mean'])
    assert len([c for c in cv.columns if c.startswith('split') and c.endswith('_test_score')])==5
print('PASS: candidate counts, five-fold outputs and selected CV scores verified.')
prior=ROOT/'tables'/'knn_k5_results.json'
if prior.exists():
    old=json.loads(prior.read_text(encoding='utf-8'))
    current=pd.read_csv(OUT/'KNN_base_predictions.csv')
    assert old['split']['test_indices']==current.row_index.tolist()
    assert old['y_pred']==current.y_pred.tolist()
    assert np.allclose(old['malignant_probability'],current.prob_malignant)
    print('PASS: final KNN baseline reproduces the saved student split, predictions and probabilities.')
if args.rerun:
    target=ROOT.parent/'tmp'/'lab2-report'/'recheck'
    result=subprocess.run([sys.executable,str(ROOT/'run_all.py'),'--output',str(target)],
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',check=True)
    (ROOT/'evidence'/'07_assistant_clean_rerun.txt').write_text(result.stdout,encoding='utf-8')
    other=pd.read_csv(target/'comparison.csv')
    cols=[c for c in table.columns if c!='fit_seconds']
    pd.testing.assert_frame_equal(table[cols],other[cols],check_exact=False,atol=1e-12,rtol=1e-12)
    for row in table.itertuples():
        a=pd.read_csv(OUT/f'{row.model}_{row.phase}_predictions.csv')
        b=pd.read_csv(target/f'{row.model}_{row.phase}_predictions.csv')
        pd.testing.assert_frame_equal(a,b,check_exact=False,atol=1e-12,rtol=1e-12)
    print('PASS: fresh-process rerun matches all 11 model configurations; timings excluded.')
print('ALL VALIDATION CHECKS PASSED')
