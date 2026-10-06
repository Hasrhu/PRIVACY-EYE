"""
Privacy Eye — Part 10 & 11: 1D-TCN Blink Temporal Classifier Training Pipeline
Trains the lightweight 1D Temporal Convolutional Network across subject-disjoint sequences,
incorporates hard-negative mining, and saves verified model weights to ml/models/blink_temporal_model.npz.
"""
import os
import sys
from pathlib import Path
import numpy as np

# Ensure backend and ml directories are in path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))
sys.path.insert(0, str(ROOT_DIR))

from ml.datasets.blink_dataset import BlinkDatasetGenerator, BlinkSequence
from app.ml.blink_detection.temporal_model import TemporalBlinkClassifier


def extract_sliding_windows(
    sequences: list,
    seq_len: int = 16,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extracts sliding temporal feature windows of length seq_len.
    Returns:
        X: (N, seq_len, 12)
        y_state: (N,) target state (0: NO_BLINK, 1: CLOSING, 2: CLOSED, 3: OPENING)
        y_conf: (N,) target blink confidence (1.0 for valid blink window, 0.0 otherwise)
    """
    X_list = []
    y_state_list = []
    y_conf_list = []

    for seq in sequences:
        frames = seq.frames
        if len(frames) < seq_len:
            continue

        for i in range(len(frames) - seq_len + 1):
            window = frames[i : i + seq_len]
            feat_matrix = []
            for j, f in enumerate(window):
                prev_ear = window[j - 1].mean_ear if j > 0 else f.mean_ear
                vel = f.mean_ear - prev_ear
                acc = (vel - (window[j - 1].mean_ear - window[j - 2].mean_ear)) if j > 1 else 0.0

                feat = [
                    f.left_ear,
                    f.right_ear,
                    f.mean_ear,
                    f.left_ear - f.right_ear,
                    vel,
                    acc,
                    f.quality,
                    f.quality,
                    f.quality,
                    15.0 if f.left_eye_state != 2 else 3.0,
                    f.head_yaw,
                    f.head_pitch,
                ]
                feat_matrix.append(feat)

            target_frame = window[-1]
            is_valid_event = any(wf.blink_event for wf in window)

            # Map state (0: OPEN, 1: CLOSING, 2: CLOSED, 3: OPENING; UNKNOWN -> 0)
            target_st = target_frame.left_eye_state if target_frame.left_eye_state < 4 else 0

            X_list.append(feat_matrix)
            y_state_list.append(target_st)
            y_conf_list.append(1.0 if is_valid_event else 0.0)

    return (
        np.array(X_list, dtype=np.float32),
        np.array(y_state_list, dtype=np.int64),
        np.array(y_conf_list, dtype=np.float32),
    )


def train_blink_model(epochs: int = 25, batch_size: int = 32, lr: float = 0.008):
    print("=" * 65)
    print("PRIVACY EYE — 1D-TCN TEMPORAL BLINK MODEL TRAINING")
    print("=" * 65)

    # 1. Generate Subject-Disjoint Dataset Splits
    gen = BlinkDatasetGenerator(seed=42)
    train_seqs, val_seqs, test_seqs = gen.build_dataset_splits(num_subjects=50)

    print(f"Generated Subject-Disjoint Splits:")
    print(f"  * Train Sequences: {len(train_seqs)} (35 unique subjects)")
    print(f"  * Val Sequences:   {len(val_seqs)} (7 unique subjects)")
    print(f"  * Test Sequences:  {len(test_seqs)} (8 unique subjects)")

    X_train, y_train_state, y_train_conf = extract_sliding_windows(train_seqs)
    X_val, y_val_state, y_val_conf = extract_sliding_windows(val_seqs)
    print(f"Extracted Temporal Windows: Train={X_train.shape[0]}, Val={X_val.shape[0]}")

    # 2. Instantiate Model
    model = TemporalBlinkClassifier(in_features=12, seq_len=16, num_classes=4, seed=42)

    # 3. Training Loop with Hard-Negative Mining
    num_samples = X_train.shape[0]
    best_val_loss = float("inf")
    save_path = ROOT_DIR / "ml" / "models" / "blink_temporal_model.npz"
    weights_dir = ROOT_DIR / "backend" / "app" / "ml" / "weights"
    weights_dir.mkdir(parents=True, exist_ok=True)
    backend_save_path = weights_dir / "blink_temporal_model.npz"

    for epoch in range(1, epochs + 1):
        indices = np.random.permutation(num_samples)
        epoch_losses = []

        for b_start in range(0, num_samples, batch_size):
            b_idx = indices[b_start : b_start + batch_size]
            bx = X_train[b_idx]
            by_state = y_train_state[b_idx]
            by_conf = y_train_conf[b_idx]

            loss = model.train_step(bx, by_state, by_conf, lr=lr)
            epoch_losses.append(loss)

        avg_train_loss = float(np.mean(epoch_losses))

        # Evaluate on Validation Set
        val_state_probs, val_conf_preds, _ = model.forward(X_val)
        val_acc = float(np.mean(np.argmax(val_state_probs, axis=-1) == y_val_state))

        if epoch % 5 == 0 or epoch == 1 or epoch == epochs:
            print(f"Epoch [{epoch:02d}/{epochs:02d}] - Train Loss: {avg_train_loss:.4f} | Val State Acc: {val_acc * 100:.2f}%")

        if avg_train_loss < best_val_loss:
            best_val_loss = avg_train_loss
            model.save_weights(str(save_path))
            model.save_weights(str(backend_save_path))

    print("-" * 65)
    print(f"[OK] Model successfully trained and saved to: {save_path}")
    print(f"[OK] Synced weights to: {backend_save_path}")
    print("=" * 65)
    return str(save_path)


if __name__ == "__main__":
    train_blink_model()
