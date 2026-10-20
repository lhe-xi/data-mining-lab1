# 实验一 数据预处理

数据挖掘与数据仓库课程实验，使用 Scikit-learn 内置的 Wine 数据集，完成探索性分析、缺失值处理、异常值检测与盖帽、规范化和编码。

## 实验材料

- [实验 Notebook](lab1.ipynb)：包含代码、步骤说明及实际运行输出。
- [Word 实验报告](2410311413_何霖洁_实验一数据预处理报告.docx)：包含图表、结果分析、思考题和仓库链接。
- [依赖版本](requirements.txt)：本次 Python 环境的包版本快照。
- [图表](figures/)及[统计表](tables/)：来自实际运行结果。
- [从头运行的文本输出](evidence/24_clean_run_streams.txt)。
- [报告补充统计的复现记录](evidence/28_report_statistics_reproduction.txt)。

## 运行方法

本次环境为 Python 3.11、conda 的 `dm-labs` 环境和 VS Code Jupyter 扩展。克隆后在仓库根目录执行：

```powershell
git clone https://github.com/lhe-xi/data-mining-lab1.git
cd data-mining-lab1
python -m conda create -n dm-labs python=3.11 pip -y
conda activate dm-labs
python -m pip install -r requirements.txt
```

已有环境可以直接安装依赖。打开 `lab1.ipynb`，选择对应的 Python 内核，重启内核后运行全部单元并保存。Wine 由 `sklearn.datasets.load_wine` 加载，无需另行下载数据。`requirements.txt` 是当前 Windows 环境快照，其他平台安装时需要实际检查兼容性。

如需重新导出报告的统计表，可在完整运行 Notebook 后，或直接在该环境运行：

```powershell
python export_statistics.py
```

该脚本在独立进程内使用 Notebook 中已有的计算代码，核对关键结果后导出缺失及缩放统计，不修改 Notebook。

## 主要结果

| 检查项 | 实际结果 |
| --- | --- |
| 原始数据 | 178 个样本、13 个特征、3 个类别 |
| 人工缺失 | 种子 42，单元格独立缺失概率 0.07；实际缺失 156 个，约 6.74% |
| 删除缺失行 | 由 178 行减少为 78 行 |
| 均值及中位数填充 | 各保留 178 行，处理后无缺失 |
| 人工异常 | 第 0 行 magnesium 从 127 改为 1000 |
| IQR / Z-score 检测 | 分别标记 42 / 13 个单元格，涉及 38 / 12 行，两者均检出注入点 |
| IQR 盖帽 | 修改 42 个单元格，注入点变为 131.5，形状保持 178×13 |
| 两种规范化 | Min-Max 范围约 [0,1]；Z-score 均值约 0、总体标准差约 1，四项检查通过 |
| 目标独热编码 | 178×3，每行之和为 1，索引对齐 |

缺失方法对比使用样本标准差（`ddof=1`）；Z-score 检测、StandardScaler 和缩放前后对比使用总体标准差（`ddof=0`）。

## 结果的适用范围

缺失和异常是为教学人为加入的。规则标记不等于测量错误，填补空缺也不等于恢复真实值。本实验没有训练下游模型，不能据此认定预测效果提高。KNN 插补、离散化和特征选择只作概念学习，没有将其写成已执行的实验结果。目标类别始终与特征分开保存，不参与插补或缩放。

原始代码由学生逐步运行并解释，报告整理和纠错过程中使用了 AI 辅助。旧草稿、临时渲染文件和报告修改前备份没有纳入仓库。
