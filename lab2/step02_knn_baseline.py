"""K=5 基线；由学生运行。不会进行选参或搜索。"""

import json
from pathlib import Path
import sys
from time import perf_counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.metrics import (
    ConfusionMatrixDisplay, accuracy_score, classification_report,
    confusion_matrix, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler


root = Path(__file__).resolve().parent
for folder in ["evidence", "figures", "tables"]:
    (root / folder).mkdir(exist_ok=True)

data = load_breast_cancer()
X, y = data.data, data.target
train_idx, test_idx = train_test_split(
    np.arange(len(y)), test_size=0.3, random_state=42, stratify=y
)
X_train, X_test = X[train_idx], X[test_idx]
y_train, y_test = y[train_idx], y[test_idx]
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = KNeighborsClassifier(n_neighbors=5)
start = perf_counter()
model.fit(X_train_scaled, y_train)
fit_seconds = perf_counter() - start
pred = model.predict(X_test_scaled)

# predict_proba 的列由 classes_ 决定；本实验取恶性（原标签 0）概率。
malignant_col = list(model.classes_).index(0)
malignant_proba = model.predict_proba(X_test_scaled)[:, malignant_col]
y_malignant = (y_test == 0).astype(int)
cm = confusion_matrix(y_test, pred, labels=[0, 1])
report = classification_report(
    y_test, pred, labels=[0, 1], target_names=["malignant (0)", "benign (1)"],
    digits=4, zero_division=0,
)
metrics = {
    "accuracy": accuracy_score(y_test, pred),
    "precision_malignant": precision_score(y_test, pred, pos_label=0, zero_division=0),
    "recall_malignant": recall_score(y_test, pred, pos_label=0, zero_division=0),
    "f1_malignant": f1_score(y_test, pred, pos_label=0, zero_division=0),
    "auc_malignant": roc_auc_score(y_malignant, malignant_proba),
    "fit_seconds_model_only": fit_seconds,
}

print("Python:", sys.executable)
print("Train/Test samples:", len(train_idx), len(test_idx))
print("Model:", model)
print("Confusion matrix: rows=true, columns=predicted; order=[0 malignant, 1 benign]")
print(cm)
print("Classification report:\n" + report)
print("Summary: positive class = malignant (original label 0)")
for key, value in metrics.items():
    print(f"{key}: {value:.6f}")

fig, ax = plt.subplots(figsize=(6, 5), layout="constrained")
ConfusionMatrixDisplay(cm, display_labels=["malignant (0)", "benign (1)"]).plot(
    ax=ax, colorbar=False, cmap="Blues", values_format="d"
)
ax.set_title("KNN (K=5): test confusion matrix")
fig.savefig(root / "figures" / "knn_k5_confusion.png", dpi=180)
plt.close(fig)

fpr, tpr, thresholds = roc_curve(y_malignant, malignant_proba)
fig, ax = plt.subplots(figsize=(6, 5), layout="constrained")
ax.plot(fpr, tpr, label=f"KNN (K=5), AUC={metrics['auc_malignant']:.4f}")
ax.plot([0, 1], [0, 1], "--", color="gray", label="Chance")
ax.set(xlabel="False positive rate", ylabel="True positive rate",
       title="Test ROC: malignant as positive", xlim=(0, 1), ylim=(0, 1.02))
ax.legend(loc="lower right")
ax.grid(alpha=0.2)
fig.savefig(root / "figures" / "knn_k5_roc.png", dpi=180)
plt.close(fig)

payload = {
    "model": "KNeighborsClassifier", "params": model.get_params(),
    "split": {"test_size": 0.3, "random_state": 42, "stratify": True,
              "train_indices": train_idx.tolist(), "test_indices": test_idx.tolist()},
    "positive_original_label": 0, "metrics": metrics,
    "confusion_matrix_label_order": [0, 1], "confusion_matrix": cm.tolist(),
    "classification_report": report,
    "y_test": y_test.tolist(), "y_pred": pred.tolist(),
    "malignant_probability": malignant_proba.tolist(),
    "roc": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
    "timing_scope": "model.fit only; excludes scaling, prediction and search",
}
(root / "tables" / "knn_k5_results.json").write_text(
    json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
)
assert cm.sum() == len(y_test)
assert np.array_equal(cm.sum(axis=1), np.bincount(y_test, minlength=2))
assert 0 <= metrics["auc_malignant"] <= 1
print("PASS: confusion matrix sample counts and AUC range checked.")
print("Saved figures:", root / "figures" / "knn_k5_confusion.png")
print("Saved figures:", root / "figures" / "knn_k5_roc.png")
print("Saved results:", root / "tables" / "knn_k5_results.json")
