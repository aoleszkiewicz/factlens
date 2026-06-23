"""TF-IDF -> MLP fake-news classifier, trained from scratch in PyTorch.

A genuine neural network built from the ground up — no pretrained weights, no
fine-tuning, no feature-tuning. The text representation is a non-parametric
TF-IDF vector (the same vectorizer as the logistic-regression baseline, see
``src.model.baseline.make_tfidf_vectorizer``); every weight of the network is
learned from random initialization via back-propagation. This satisfies the
"build a network from scratch" constraint of the SSN course while being a step
up from the baseline (logistic regression == a single linear layer).

Label convention matches the rest of the project: 1 = Real, 0 = Fake. The
``evaluate_mlp`` return value mirrors ``src.model.baseline.evaluate`` so metric
tables and plots are interchangeable between the two models.

Responsibilities are kept separate and small:
    * ``TfidfDataset``   — feed sparse TF-IDF rows to PyTorch, densified lazily.
    * ``MLPClassifier``  — the network itself (logits out, no sigmoid).
    * ``train_mlp``      — training loop with early stopping on validation F1.
    * ``predict_proba``  — inference, returns probabilities.
    * ``evaluate_mlp``   — vectorize -> predict -> metrics dict.
    * ``set_seed`` / ``resolve_device`` — reproducibility and device handling.
"""

import numpy as np
import pandas as pd
import torch
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from torch import nn
from torch.utils.data import DataLoader, Dataset

from src.config import RANDOM_STATE

# Probability threshold for turning sigmoid outputs into a 0/1 decision.
DECISION_THRESHOLD = 0.5


def set_seed(seed: int = RANDOM_STATE) -> None:
    """Seed NumPy and PyTorch (CPU + CUDA/ROCm) for reproducible runs.

    Call once before constructing the model and training so weight
    initialization and batch shuffling are deterministic.
    """
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def resolve_device(device: str | torch.device | None = None) -> torch.device:
    """Resolve the compute device, preferring an available GPU.

    Passing ``None`` auto-selects ``cuda`` when a GPU is visible (ROCm/HIP
    exposes the same ``cuda`` API, so AMD GPUs are picked up here too) and
    falls back to ``cpu`` otherwise. An explicit value is honoured as-is.
    """
    if device is not None:
        return torch.device(device)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


class TfidfDataset(Dataset):
    """Wrap a sparse TF-IDF matrix and its labels as a PyTorch ``Dataset``.

    The full feature matrix stays sparse in memory; each row is densified to a
    ``float32`` vector only when requested, so the whole corpus is never
    materialized densely at once.
    """

    def __init__(self, features: csr_matrix, labels: pd.Series | np.ndarray) -> None:
        """Store features and labels.

        Args:
            features: TF-IDF matrix of shape ``(n_samples, vocab_size)``.
            labels: Binary labels (1 = Real, 0 = Fake), length ``n_samples``.
        """
        self.features: csr_matrix = features.tocsr()
        self.labels: torch.Tensor = torch.as_tensor(
            np.asarray(labels, dtype=np.float32)
        )

    def __len__(self) -> int:
        return self.features.shape[0]

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        row = self.features[index].toarray().ravel().astype(np.float32, copy=False)
        return torch.from_numpy(row), self.labels[index]


class MLPClassifier(nn.Module):
    """Feed-forward network over TF-IDF features.

    Architecture: a stack of ``Linear -> ReLU -> Dropout`` blocks followed by a
    single linear output. ``forward`` returns raw **logits** (one per sample);
    pair it with ``BCEWithLogitsLoss`` for training and ``torch.sigmoid`` for
    probabilities at inference time.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dims: tuple[int, ...] = (256,),
        dropout: float = 0.3,
    ) -> None:
        """Build the network.

        Args:
            input_dim: Size of the TF-IDF vocabulary (input features).
            hidden_dims: Width of each hidden layer, in order. Defaults to a
                single 256-unit hidden layer.
            dropout: Dropout probability applied after every hidden layer.
        """
        super().__init__()
        layers: list[nn.Module] = []
        in_features = input_dim
        for width in hidden_dims:
            layers.append(nn.Linear(in_features, width))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            in_features = width
        layers.append(nn.Linear(in_features, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Map a batch of TF-IDF vectors to logits of shape ``(batch, 1)``."""
        return self.net(x)


def _train_one_epoch(
    model: MLPClassifier,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    """Run a single training pass; return the mean batch loss."""
    model.train()
    total_loss = 0.0
    n_samples = 0
    for batch_features, batch_labels in loader:
        features = batch_features.to(device)
        labels = batch_labels.to(device)

        optimizer.zero_grad()
        logits = model(features).squeeze(1)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * features.size(0)
        n_samples += features.size(0)
    return total_loss / n_samples


def _validate(
    model: MLPClassifier,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float]:
    """Evaluate on a validation loader; return ``(mean_loss, f1)``."""
    model.eval()
    total_loss = 0.0
    n_samples = 0
    all_targets: list[np.ndarray] = []
    all_preds: list[np.ndarray] = []
    with torch.no_grad():
        for batch_features, batch_labels in loader:
            features = batch_features.to(device)
            labels = batch_labels.to(device)

            logits = model(features).squeeze(1)
            total_loss += criterion(logits, labels).item() * features.size(0)
            n_samples += features.size(0)

            preds = (torch.sigmoid(logits) >= DECISION_THRESHOLD).int()
            all_targets.append(labels.cpu().numpy())
            all_preds.append(preds.cpu().numpy())

    y_true = np.concatenate(all_targets)
    y_pred = np.concatenate(all_preds)
    return total_loss / n_samples, float(f1_score(y_true, y_pred))


def train_mlp(
    model: MLPClassifier,
    train_dataset: TfidfDataset,
    val_dataset: TfidfDataset,
    *,
    epochs: int = 20,
    batch_size: int = 256,
    lr: float = 1e-3,
    weight_decay: float = 0.0,
    patience: int = 3,
    device: str | torch.device | None = None,
) -> dict[str, list[float]]:
    """Train the MLP with Adam and early stopping on validation F1.

    The weights from the epoch with the best validation F1 are restored into
    ``model`` before returning, so the caller ends up with the best checkpoint
    rather than the last one. Call ``set_seed`` beforehand for reproducibility.

    Args:
        model: An unfitted ``MLPClassifier``.
        train_dataset: Training data.
        val_dataset: Validation data (drives early stopping).
        epochs: Maximum number of epochs.
        batch_size: Mini-batch size for both loaders.
        lr: Adam learning rate.
        weight_decay: L2 regularization strength for Adam.
        patience: Stop after this many epochs without val-F1 improvement.
        device: Compute device; ``None`` auto-selects GPU when available.

    Returns:
        Training history with per-epoch lists: ``train_loss``, ``val_loss``,
        ``val_f1``.
    """
    resolved_device = resolve_device(device)
    model.to(resolved_device)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    criterion = nn.BCEWithLogitsLoss()

    history: dict[str, list[float]] = {"train_loss": [], "val_loss": [], "val_f1": []}
    best_val_f1 = -1.0
    best_state: dict[str, torch.Tensor] = {}
    epochs_without_improvement = 0

    for _ in range(epochs):
        train_loss = _train_one_epoch(
            model, train_loader, optimizer, criterion, resolved_device
        )
        val_loss, val_f1 = _validate(model, val_loader, criterion, resolved_device)

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_f1"].append(val_f1)

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_state = {
                name: tensor.detach().cpu().clone()
                for name, tensor in model.state_dict().items()
            }
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= patience:
                break

    if best_state:
        model.load_state_dict(best_state)
    return history


def predict_proba(
    model: MLPClassifier,
    dataset: TfidfDataset,
    *,
    batch_size: int = 256,
    device: str | torch.device | None = None,
) -> np.ndarray:
    """Return P(Real) for every sample in ``dataset`` as a 1-D array."""
    resolved_device = resolve_device(device)
    model.to(resolved_device)
    model.eval()

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    probabilities: list[np.ndarray] = []
    with torch.no_grad():
        for features, _ in loader:
            logits = model(features.to(resolved_device)).squeeze(1)
            probabilities.append(torch.sigmoid(logits).cpu().numpy())
    return np.concatenate(probabilities)


def evaluate_mlp(
    model: MLPClassifier,
    vectorizer: TfidfVectorizer,
    X: pd.Series,  # noqa: N803 — matches src.model.baseline.evaluate
    y: pd.Series,
    *,
    batch_size: int = 256,
    device: str | torch.device | None = None,
) -> dict[str, object]:
    """Evaluate a trained MLP on a labelled set.

    Mirrors ``src.model.baseline.evaluate``: the returned dict has identical
    keys and rounding, so results from both models drop into the same tables.

    Args:
        model: A trained ``MLPClassifier``.
        vectorizer: The **fitted** TF-IDF vectorizer used during training.
        X: Series of document strings.
        y: Series of binary labels (1 = Real, 0 = Fake).
        batch_size: Inference batch size.
        device: Compute device; ``None`` auto-selects GPU when available.

    Returns:
        Dict with accuracy, precision, recall, f1, roc_auc and the 2x2
        confusion matrix (nested list, rows = true, cols = predicted).
    """
    features = vectorizer.transform(X)
    dataset = TfidfDataset(features, y)
    y_proba = predict_proba(model, dataset, batch_size=batch_size, device=device)
    y_pred = (y_proba >= DECISION_THRESHOLD).astype(int)
    return {
        "accuracy": round(float(accuracy_score(y, y_pred)), 4),
        "precision": round(float(precision_score(y, y_pred)), 4),
        "recall": round(float(recall_score(y, y_pred)), 4),
        "f1": round(float(f1_score(y, y_pred)), 4),
        "roc_auc": round(float(roc_auc_score(y, y_proba)), 4),
        "confusion_matrix": confusion_matrix(y, y_pred).tolist(),
    }
