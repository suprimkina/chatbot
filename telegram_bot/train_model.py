import pandas as pd
import numpy as np
import pickle
import re

# -------------------------------------------------------------
# 1. Загрузка и предобработка данных
# -------------------------------------------------------------
df = pd.read_csv("error_dataset.csv")
print(f"Загружено {len(df)} примеров")

def tokenize(code):
    code = str(code).lower()
    # убираем всё, кроме букв/цифр и базовых символов
    code = re.sub(r'[^a-z0-9\s\[\]{}()<>=+\-*/%]', ' ', code)
    return code

df['user_tok'] = df['user_code'].apply(tokenize)
df['ref_tok'] = df['reference_code'].apply(tokenize)

# Строим словарь токенов (TF-IDF вручную)
X_text = df['user_tok'] + " [SEP] " + df['ref_tok']

# Простейшая векторизация: Bag-of-Words на 500 самых частых слов
from collections import Counter
word_counts = Counter(" ".join(X_text).split())
vocab = [w for w, _ in word_counts.most_common(500)]
word2idx = {w: i for i, w in enumerate(vocab)}

def bow_vector(text, vocab, word2idx):
    vec = np.zeros(len(vocab))
    for word in text.split():
        if word in word2idx:
            vec[word2idx[word]] += 1
    # Нормализация
    if vec.sum() > 0:
        vec = vec / vec.sum()
    return vec

X = np.array([bow_vector(t, vocab, word2idx) for t in X_text])

# Метки
labels = df['label'].values
label_names = ['correct', 'logic_error', 'style_issue', 'syntax_error']
label2id = {l: i for i, l in enumerate(label_names)}
y = np.array([label2id[l] for l in labels])

# Разделение
np.random.seed(42)
indices = np.random.permutation(len(X))
split = int(0.8 * len(X))
train_idx, test_idx = indices[:split], indices[split:]
X_train, X_test = X[train_idx], X[test_idx]
y_train, y_test = y[train_idx], y[test_idx]

# -------------------------------------------------------------
# 2. Нейросеть (MLP с одним скрытым слоем) на numpy
# -------------------------------------------------------------
class SimpleMLP:
    def __init__(self, input_size, hidden_size, output_size, lr=0.01):
        self.W1 = np.random.randn(input_size, hidden_size) * 0.01
        self.b1 = np.zeros(hidden_size)
        self.W2 = np.random.randn(hidden_size, output_size) * 0.01
        self.b2 = np.zeros(output_size)
        self.lr = lr

    def softmax(self, x):
        e = np.exp(x - np.max(x, axis=1, keepdims=True))
        return e / e.sum(axis=1, keepdims=True)

    def forward(self, X):
        self.z1 = X @ self.W1 + self.b1
        self.a1 = np.maximum(0, self.z1)  # ReLU
        self.z2 = self.a1 @ self.W2 + self.b2
        self.probs = self.softmax(self.z2)
        return self.probs

    def cross_entropy(self, probs, y):
        m = y.shape[0]
        log_likelihood = -np.log(probs[range(m), y] + 1e-9)
        return np.sum(log_likelihood) / m

    def backward(self, X, y):
        m = X.shape[0]
        # градиент z2
        dz2 = self.probs.copy()
        dz2[range(m), y] -= 1
        dz2 /= m

        dW2 = self.a1.T @ dz2
        db2 = dz2.sum(axis=0)

        da1 = dz2 @ self.W2.T
        dz1 = da1 * (self.z1 > 0)  # производная ReLU
        dW1 = X.T @ dz1
        db1 = dz1.sum(axis=0)

        # обновление
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1

    def fit(self, X, y, epochs=500, verbose=True):
        for i in range(epochs):
            probs = self.forward(X)
            loss = self.cross_entropy(probs, y)
            if verbose and i % 100 == 0:
                acc = (probs.argmax(axis=1) == y).mean()
                print(f"Epoch {i:4d}  loss: {loss:.4f}  accuracy: {acc:.4f}")
            self.backward(X, y)

    def predict(self, X):
        probs = self.forward(X)
        return probs.argmax(axis=1), probs

# -------------------------------------------------------------
# 3. Обучение
# -------------------------------------------------------------
input_size = X_train.shape[1]
hidden_size = 64
output_size = len(label_names)

mlp = SimpleMLP(input_size, hidden_size, output_size, lr=0.1)
mlp.fit(X_train, y_train, epochs=800)

# Оценка
y_pred, _ = mlp.predict(X_test)
acc = (y_pred == y_test).mean()
print(f"\nTest accuracy: {acc:.4f}")

# Сохранение модели и векторизатора
with open("model_numpy.pkl", "wb") as f:
    pickle.dump({
        'W1': mlp.W1, 'b1': mlp.b1,
        'W2': mlp.W2, 'b2': mlp.b2,
        'vocab': vocab, 'word2idx': word2idx,
        'label_names': label_names
    }, f)

print("Модель сохранена в model_numpy.pkl")