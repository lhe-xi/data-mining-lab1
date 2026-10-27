"""实验二完整复现。保留原标签 0=恶性；输出写入 final_results。"""
from pathlib import Path
from datetime import datetime
from time import perf_counter
import hashlib
import json
import platform
import sys

import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, Binarizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier, plot_tree, export_text
from sklearn.naive_bayes import GaussianNB, MultinomialNB, BernoulliNB
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report, ConfusionMatrixDisplay)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'final_results'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})

def savefig(fig, name):
    fig.savefig(OUT / name, dpi=180, bbox_inches='tight')
    plt.close(fig)

def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2,
        default=lambda x: x.item() if isinstance(x,np.generic) else str(x)), encoding='utf-8')

def main():
    data = load_breast_cancer()
    X, y = data.data, data.target  # 不能在拆分前改标签，以保持学生的拆分不变。
    train_idx, test_idx = train_test_split(np.arange(len(y)), test_size=.3,
        random_state=42, stratify=y)
    Xt, Xv, yt, yv = X[train_idx], X[test_idx], y[train_idx], y[test_idx]
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    print('Execution:', datetime.now().astimezone().isoformat())
    print('Python:', sys.executable)
    print('Labels: 0=malignant, 1=benign; positive class=malignant (0)')
    print('Shape:', X.shape, 'train/test:', Xt.shape, Xv.shape)
    print('Class counts all/train/test:', np.bincount(y), np.bincount(yt), np.bincount(yv))
    assert X.shape == (569, 30) and len(train_idx) == 398 and len(test_idx) == 171
    assert not np.intersect1d(train_idx, test_idx).size
    assert np.isfinite(X).all()
    scaler = StandardScaler().fit(Xt)
    train_scaled, test_scaled = scaler.transform(Xt), scaler.transform(Xv)
    assert np.allclose(train_scaled.mean(0), 0, atol=1e-10)
    assert np.allclose(train_scaled.std(0), 1, atol=1e-10)
    pd.DataFrame({'row_index': np.r_[train_idx, test_idx],
        'subset': ['train']*len(train_idx)+['test']*len(test_idx),
        'original_label': np.r_[yt, yv]}).to_csv(OUT/'split_indices.csv', index=False)
    pd.DataFrame({'feature': data.feature_names, 'train_mean': scaler.mean_,
        'train_std_ddof0': scaler.scale_, 'scaled_train_mean': train_scaled.mean(0),
        'scaled_test_mean': test_scaled.mean(0)}).to_csv(OUT/'scaling.csv', index=False)

    models = {
        'KNN': Pipeline([('scale', StandardScaler()), ('model', KNeighborsClassifier())]),
        'Tree': DecisionTreeClassifier(random_state=42),
        'GaussianNB': GaussianNB(),
    }
    # 搜索范围、评分与折数在查看本次测试结果前固定；无测试集参与选参。
    grids = {
        'KNN': {'model__n_neighbors': [1,3,5,7,9,11,15],
                'model__metric': ['euclidean','manhattan']},
        'Tree': {'max_depth': [None,3,5,7], 'min_samples_split': [2,5,10],
                 'min_samples_leaf': [1,2,5]},
        'GaussianNB': {'var_smoothing': np.logspace(-12,-6,7).tolist()},
    }
    fitted, searches, rows, search_meta = {}, {}, [], {}

    def evaluate(name, phase, est, fit_time):
        pred = est.predict(Xv)
        proba = est.predict_proba(Xv)[:, list(est.classes_).index(0)]
        cm = confusion_matrix(yv, pred, labels=[0,1])
        metrics = dict(model=name, phase=phase,
            accuracy=float(accuracy_score(yv,pred)),
            precision=float(precision_score(yv,pred,pos_label=0,zero_division=0)),
            recall=float(recall_score(yv,pred,pos_label=0,zero_division=0)),
            f1=float(f1_score(yv,pred,pos_label=0,zero_division=0)),
            auc=float(roc_auc_score(yv==0,proba)),
            fit_seconds=float(fit_time),train_accuracy=float(est.score(Xt,yt)),
            TP=int(cm[0,0]),FN=int(cm[0,1]),FP=int(cm[1,0]),TN=int(cm[1,1]))
        report = classification_report(yv,pred,labels=[0,1],
            target_names=['malignant (0)','benign (1)'],digits=6,zero_division=0)
        (OUT/f'{name}_{phase}_report.txt').write_text(
            'rows=true, cols=predicted, order=[malignant (0), benign (1)]\n'+str(cm)+'\n'+report,
            encoding='utf-8')
        pd.DataFrame({'row_index': test_idx,'y_true':yv,'y_pred':pred,
            'prob_malignant':proba}).to_csv(OUT/f'{name}_{phase}_predictions.csv',index=False)
        rows.append(metrics)
        fitted[(name,phase)] = est
        print(f'\n{name} {phase}\n{cm}\n{report}')
        assert cm.sum() == 171 and np.array_equal(cm.sum(1), [64,107])
        return metrics

    # 先完成所有搜索，再绘制按老师要求的测试集 K 曲线，不据该曲线改选参数。
    for name, est in models.items():
        start=perf_counter(); est.fit(Xt,yt); elapsed=perf_counter()-start
        evaluate(name,'base',est,elapsed)
        search=GridSearchCV(est,grids[name],scoring='accuracy',cv=cv,n_jobs=1,
            return_train_score=True,error_score='raise')
        start=perf_counter(); search.fit(Xt,yt); search_elapsed=perf_counter()-start
        searches[name]=search
        pd.DataFrame(search.cv_results_).to_csv(OUT/f'{name}_cv.csv',index=False)
        # GridSearchCV 的 refit_time_ 在此系统可能舍入为 0；独立高精度计时重拟合。
        tuned=clone(search.best_estimator_)
        start=perf_counter();tuned.fit(Xt,yt);tuned_elapsed=perf_counter()-start
        evaluate(name,'tuned',tuned,tuned_elapsed)
        best=search.best_index_
        search_meta[name]={'params':search.best_params_, 'cv_mean':float(search.best_score_),
            'cv_std':float(search.cv_results_['std_test_score'][best]),
            'candidate_count':len(search.cv_results_['params']),
            'search_seconds':search_elapsed,'refit_seconds':float(search.refit_time_)}

    variants = {
        'MultinomialNB': MultinomialNB(),
        'BernoulliNB': Pipeline([('scale',StandardScaler()),('binary',Binarizer(threshold=0)),
                                ('model',BernoulliNB(binarize=None))]),
    }
    variant_meta={}
    for name,est in variants.items():
        # 单候选 GridSearchCV 记录相同五折验证；非负原值输入多项式模型。
        search=GridSearchCV(est,{},cv=cv,scoring='accuracy',n_jobs=1,error_score='raise')
        search.fit(Xt,yt)
        pd.DataFrame(search.cv_results_).to_csv(OUT/f'{name}_cv.csv',index=False)
        est=clone(search.best_estimator_)
        start=perf_counter();est.fit(Xt,yt);elapsed=perf_counter()-start
        evaluate(name,'variant',est,elapsed)
        variant_meta[name]={'cv_mean':float(search.best_score_),
            'cv_std':float(search.cv_results_['std_test_score'][0])}

    # 标准化影响对照，只有 KNN / Tree 输入表示不同，其余设置相同。
    for name,est in {
        'KNN_raw':KNeighborsClassifier(),
        'Tree_scaled':Pipeline([('scale',StandardScaler()),
                               ('model',DecisionTreeClassifier(random_state=42))]),
    }.items():
        start=perf_counter();est.fit(Xt,yt);elapsed=perf_counter()-start
        evaluate(name,'scale_check',est,elapsed)

    # 后剪枝附加验证，固定 alpha 网格，仍只用训练集 CV。
    pruning=GridSearchCV(DecisionTreeClassifier(random_state=42),
        {'ccp_alpha':[0,.001,.005,.01,.02]},cv=cv,scoring='accuracy',n_jobs=1,
        return_train_score=True,error_score='raise')
    pruning.fit(Xt,yt)
    pd.DataFrame(pruning.cv_results_).to_csv(OUT/'Tree_postprune_cv.csv',index=False)
    pruned=clone(pruning.best_estimator_)
    start=perf_counter();pruned.fit(Xt,yt);elapsed=perf_counter()-start
    evaluate('Tree_postprune','extra',pruned,elapsed)

    krows=[]
    for k in [1,3,5,7,9,11,15]:
        res=searches['KNN'].cv_results_
        j=next(i for i,p in enumerate(res['params']) if p['model__n_neighbors']==k
               and p['model__metric']=='euclidean')
        est=Pipeline([('scale',StandardScaler()),('model',KNeighborsClassifier(n_neighbors=k))])
        est.fit(Xt,yt)
        krows.append({'k':k,'test_accuracy':float(est.score(Xv,yv)),
            'train_accuracy':float(est.score(Xt,yt)),
            'cv_mean':float(res['mean_test_score'][j]),'cv_std':float(res['std_test_score'][j])})
    kt=pd.DataFrame(krows);kt.to_csv(OUT/'k_curve.csv',index=False)
    fig,axs=plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
    axs[0].plot(kt.k,kt.test_accuracy,'o-',label='Test (descriptive only)')
    axs[0].plot(kt.k,kt.train_accuracy,'s--',label='Train')
    axs[1].errorbar(kt.k,kt.cv_mean,yerr=kt.cv_std,fmt='o-',capsize=4,label='5-fold CV mean +/- std')
    for ax in axs:ax.set(xlabel='K',ylabel='Accuracy',xticks=kt.k);ax.grid(alpha=.2);ax.legend(fontsize=8)
    savefig(fig,'k_curve.png')

    for phase in ['base','tuned']:
        fig,axs=plt.subplots(1,3,figsize=(10,3.5),layout='constrained')
        fig2,ax2=plt.subplots(figsize=(6.6,4.5),layout='constrained')
        for ax,name in zip(axs,models):
            est=fitted[(name,phase)];pred=est.predict(Xv)
            ConfusionMatrixDisplay(confusion_matrix(yv,pred,labels=[0,1]),
                display_labels=['malignant','benign']).plot(ax=ax,cmap='Blues',colorbar=False,values_format='d')
            ax.set_title(f'{name} {phase}')
            p=est.predict_proba(Xv)[:,list(est.classes_).index(0)]
            fpr,tpr,_=roc_curve(yv==0,p)
            ax2.plot(fpr,tpr,label=f'{name} AUC={roc_auc_score(yv==0,p):.4f}')
        ax2.plot([0,1],[0,1],'--',color='gray')
        ax2.set(xlabel='False positive rate',ylabel='True positive rate',title=f'Test ROC ({phase}), positive=malignant')
        ax2.legend();ax2.grid(alpha=.2)
        savefig(fig,f'confusion_{phase}.png');savefig(fig2,f'roc_{phase}.png')

    tree=fitted[('Tree','base')]
    tuned_tree=fitted[('Tree','tuned')]
    fig,ax=plt.subplots(figsize=(17,10),layout='constrained')
    plot_tree(tree,feature_names=list(data.feature_names),class_names=['malignant','benign'],
              filled=True,rounded=True,fontsize=7,ax=ax)
    savefig(fig,'tree_full.png')
    fig,ax=plt.subplots(figsize=(11,5.5),layout='constrained')
    plot_tree(tree,feature_names=list(data.feature_names),class_names=['malignant','benign'],
              filled=True,max_depth=2,fontsize=9,ax=ax)
    savefig(fig,'tree_top.png')
    (OUT/'tree_rules.txt').write_text(export_text(tree,feature_names=list(data.feature_names)),encoding='utf-8')
    importance=pd.DataFrame({'feature':data.feature_names,'importance':tree.feature_importances_}).sort_values('importance',ascending=False)
    importance.to_csv(OUT/'tree_importance.csv',index=False)
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
    ax.barh(importance.head(10).feature[::-1],importance.head(10).importance[::-1])
    ax.set(xlabel='Impurity-based importance',title='Default decision tree: top 10 features')
    savefig(fig,'tree_importance.png')
    path=[]
    for node in tree.decision_path(Xv[:1]).indices:
        f=int(tree.tree_.feature[node])
        if f>=0:
            value=float(Xv[0,f]);threshold=float(tree.tree_.threshold[node])
            path.append({'feature':str(data.feature_names[f]),'value':value,'threshold':threshold,
                         'branch':'left (<=)' if value<=threshold else 'right (>)'})

    corr=pd.DataFrame(Xt,columns=data.feature_names).corr()
    corr.to_csv(OUT/'train_correlations.csv')
    pairs=sorted([(str(corr.index[i]),str(corr.columns[j]),float(corr.iloc[i,j]))
        for i in range(30) for j in range(i+1,30)],key=lambda x:abs(x[2]),reverse=True)
    pd.DataFrame(pairs,columns=['feature_a','feature_b','pearson_r']).to_csv(OUT/'correlation_pairs.csv',index=False)
    selected=list(data.feature_names[:10]); sub=corr.loc[selected,selected]
    fig,ax=plt.subplots(figsize=(8,6.5),layout='constrained')
    im=ax.imshow(sub,vmin=-1,vmax=1,cmap='coolwarm')
    ax.set_xticks(range(10),selected,rotation=65,ha='right',fontsize=8)
    ax.set_yticks(range(10),selected,fontsize=8)
    for i in range(10):
        for j in range(10):ax.text(j,i,f'{sub.iloc[i,j]:.2f}',ha='center',va='center',fontsize=7)
    fig.colorbar(im,ax=ax,shrink=.7);ax.set_title('Training data: correlations among first 10 features')
    savefig(fig,'train_correlations.png')
    fig,axs=plt.subplots(1,3,figsize=(10,3.5),layout='constrained')
    for j,ax in enumerate(axs):
        f=[0,1,3][j]
        for label in [0,1]:ax.hist(Xt[yt==label,f],bins=16,density=True,alpha=.5,label=str(data.target_names[label]))
        ax.set(xlabel=str(data.feature_names[f]),ylabel='Density');ax.legend(fontsize=8)
    savefig(fig,'feature_distributions.png')

    comparison=pd.DataFrame(rows);comparison.to_csv(OUT/'comparison.csv',index=False)
    metadata={
        'execution_time':datetime.now().astimezone().isoformat(),'executor':'assistant at user request',
        'python':platform.python_version(),'executable':sys.executable,'platform':platform.platform(),
        'versions':{'numpy':np.__version__,'pandas':pd.__version__,'scikit-learn':sklearn.__version__,'matplotlib':matplotlib.__version__},
        'data_sha256':hashlib.sha256(X.tobytes()+y.tobytes()).hexdigest(),
        'shape':list(X.shape),'label_mapping':{'0':'malignant','1':'benign'},'positive_label':0,
        'counts':np.bincount(y).tolist(),'train_counts':np.bincount(yt).tolist(),'test_counts':np.bincount(yv).tolist(),
        'split':{'test_size':.3,'random_state':42,'stratify':True},
        'cv':{'folds':5,'shuffle':True,'random_state':42,'scoring':'accuracy'},
        'search':search_meta,'variants':variant_meta,
        'postprune':{'params':pruning.best_params_,'cv_mean':float(pruning.best_score_)},
        'tree':{'base_depth':tree.get_depth(),'base_leaves':tree.get_n_leaves(),
                'tuned_depth':tuned_tree.get_depth(),'tuned_leaves':tuned_tree.get_n_leaves(),
                'postprune_depth':pruning.best_estimator_.get_depth(),
                'sample_row_index':int(test_idx[0]),'sample_true_label':int(yv[0]),
                'sample_predicted_label':int(tree.predict(Xv[:1])[0]),'sample_path':path},
        'scaling_check':{'same_tree_predictions':bool(np.array_equal(tree.predict(Xv),fitted[('Tree_scaled','scale_check')].predict(Xv)))},
        'timing':'Base/refit includes pipeline scaling if present; search total reported separately. Single-run timings vary.',
    }
    write_json('metadata.json',metadata)
    print('\nFINAL COMPARISON\n',comparison.to_string(index=False))
    print('\nK CURVE\n',kt.to_string(index=False))
    print('\nSEARCH\n',json.dumps(search_meta,ensure_ascii=False,indent=2))
    print('PASS: complete experiment executed and outputs saved to',OUT)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args()
    OUT=args.output.resolve()
    OUT.mkdir(parents=True,exist_ok=True)
    main()
