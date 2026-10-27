# 实验二 分类算法

使用 Scikit-learn 内置 Breast Cancer Wisconsin 数据，完成 KNN、CART 决策树、高斯朴素贝叶斯、贝叶斯变体、五折交叉验证与网格搜索。完整运行日期为 2026-10-27。

- [Word 报告](2410311413_何霖洁_实验二分类算法报告.docx)：沿用实验一版式，包含真实结果分析和六道思考题。
- [可直接阅读的报告](实验报告.md)。
- [完整代码](run_all.py)、[结果验证](validate_results.py)、[依赖快照](requirements.txt)。
- [最终输出](final_results/)：分类报告、CV 明细、逐样本预测、拆分索引、参数、图表。
- [最终运行日志](evidence/06_assistant_final_run.txt)、[独立复跑日志](evidence/07_assistant_clean_rerun.txt)、[验证结果](evidence/08_validation.txt)。
- [提交检查](提交前检查.md)、[复现与来源记录](复现与证据.md)。

## 从头运行

在仓库根目录进入 `lab2`；推荐 Python 3.11。已有 dm-labs 环境可以继续使用。

```powershell
cd lab2
python -m pip install -r requirements.txt
python run_all.py
python validate_results.py --rerun
```

运行前可用 `python -c "import sys; print(sys.executable)"` 检查解释器。`requirements.txt` 是本次 Windows 环境的完整快照；本实验直接使用 numpy、pandas、scikit-learn、matplotlib，无需下载数据。验证器的独立复跑结果写入仓库 `tmp/lab2-report/recheck/`，不覆盖报告对应的最终结果；单次计时允许变化。

## 方法与口径

保留原标签 0=恶性、1=良性。报告中的精确率、召回率、F1 与 ROC/AUC 均以恶性为正类；分类报告保留两类。混淆矩阵行=真实、列=预测，顺序 [恶性,良性]。

训练/测试比例 70%/30%，`random_state=42, stratify=y`，实际为 398/171 条。五折使用 `StratifiedKFold(5, shuffle=True, random_state=42)`；选参评分为 accuracy。KNN 的缩放及伯努利模型的二值化在 Pipeline 内进行，只拟合训练部分。树和 GaussianNB 基线使用原始连续特征；多项式变体直接使用非负原值，不能把这种输入解释成真实计数。表中的变体对比也包含输入表示差异。

KNN 搜索 K 和两种距离，树搜索深度/分裂数/叶节点数，GaussianNB 搜索方差平滑参数；另做尺度对照与后剪枝。网格固定，不根据测试曲线反复修改。测试 K 曲线仅按指导书要求描述，不用于选参。全部搜索明细保存在最终输出目录。

## 本次真实结果

| 模型 | 阶段 | 准确率 | 恶性召回率 | 恶性 F1 | AUC |
| --- | --- | --- | --- | --- | --- |
| KNN | 基线 | 0.9591 | 0.8906 | 0.9421 | 0.9827 |
| KNN | 调优 | 0.9591 | 0.8906 | 0.9421 | 0.9856 |
| 决策树 | 基线 | 0.9181 | 0.8906 | 0.8906 | 0.9126 |
| 决策树 | 调优 | 0.9181 | 0.9063 | 0.8923 | 0.9433 |
| GaussianNB | 基线 | 0.9474 | 0.8906 | 0.9268 | 0.9901 |
| GaussianNB | 调优 | 0.9357 | 0.8594 | 0.9091 | 0.9835 |

KNN 最优为 K=7、曼哈顿距离；树为深度5、最小分裂数5、最小叶节点数2；GaussianNB 的 var_smoothing=10^-7。CV 选参未保证测试性能上升，报告保留了下降结果。本实验是教学比较，没有临床部署。

## 文件来源与报告生成

学生完成了前期数据检查与 KNN 基线；后续在学生明确请求下由助手完整运行、复跑核验、整理报告。原先脚本与保存日志继续保留，最终 KNN 基线与学生的拆分、预测、概率一致。

`results/`、`run_examples.py` 等本地前期教学材料不作为最终报告证据，未纳入本次提交。最终证据只使用 `final_results/` 与明确列出的日志。报告按实验一文档的措辞与版式整理，新增思考题为辅助撰写，未声称学生已经独立作答。

`build_report.py` 用本次 CSV/JSON 构建报告。它需要原始实验一参考 DOCX，SHA-256 为 `50521d9d8e7711b3c9cda30a650a9ce2ca71829ca2bc49f6c8994d9860b5abb3`；参考文件在本地有未提交修改，本次未连带上传。若使用其他版本，版式可能变化。数值实验复现不依赖参考 DOCX 或 Word。文档构建需 python-docx、lxml 及 pandas；本次使用 Codex 文档运行时。最终 DOCX 通过 Word 只读导出、Poppler 渲染检查，未回存改写参考文件。

[返回课程实验首页](../README.md)
