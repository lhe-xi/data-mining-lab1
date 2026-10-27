"""学生运行的第一步：数据划分和标准化检查，不训练分类器。"""

import sys

import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


print("Python:", sys.executable)
data = load_breast_cancer()
X, y = data.data, data.target
print("X shape:", X.shape, "y shape:", y.shape)
print("Label mapping:", dict(enumerate(data.target_names)))

# 保留原始行号，便于检查训练集与测试集是否重叠。
train_idx, test_idx = train_test_split(
    np.arange(len(y)), test_size=0.3, random_state=42, stratify=y
)
X_train, X_test = X[train_idx], X[test_idx]
y_train, y_test = y[train_idx], y[test_idx]
print("Train shape:", X_train.shape, "Test shape:", X_test.shape)
for name, labels in [("All", y), ("Train", y_train), ("Test", y_test)]:
    counts = np.bincount(labels, minlength=2)
    print(f"{name} class counts [0, 1]:", counts)
    print(f"{name} class proportions [0, 1]:", np.round(counts / len(labels), 4))

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
print("First 3 features:", data.feature_names[:3])
print("Train scaled means (first 3):", np.round(X_train_scaled.mean(axis=0)[:3], 6))
print("Test scaled means (first 3):", np.round(X_test_scaled.mean(axis=0)[:3], 6))
print("Train scaled std (first 3, ddof=0):", np.round(X_train_scaled.std(axis=0)[:3], 6))

assert len(np.intersect1d(train_idx, test_idx)) == 0
assert len(train_idx) + len(test_idx) == len(y)
assert np.isfinite(X_train_scaled).all() and np.isfinite(X_test_scaled).all()
assert np.allclose(scaler.mean_, X_train.mean(axis=0))
assert np.allclose(X_train_scaled.mean(axis=0), 0, atol=1e-10)
assert np.allclose(X_train_scaled.std(axis=0), 1, atol=1e-10)
print("PASS: disjoint split, finite values, train-only scaling, train mean/std.")
