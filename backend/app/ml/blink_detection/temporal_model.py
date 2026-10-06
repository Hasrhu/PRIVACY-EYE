"""
Privacy Eye — Stage B: 1D Temporal Convolutional Network (1D-TCN) for Blink Event Modeling
Lightweight, vectorized neural architecture processing rolling temporal eye telemetry.
Evaluates biological eye dynamics across multi-frame sliding windows.
"""
import os
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class TemporalBlinkClassifier:
    """
    Lightweight 1D Temporal Convolutional Network for sequential ocular state classification
    and blink event confidence prediction.
    Features per frame (D=12):
    [left_ear, right_ear, mean_ear, ear_delta, ear_velocity, ear_accel,
     overall_quality, left_quality, right_quality, vert_energy, head_yaw, head_pitch]
    """

    def __init__(self, in_features: int = 12, seq_len: int = 16, num_classes: int = 4, seed: int = 42):
        self.in_features = in_features
        self.seq_len = seq_len
        self.num_classes = num_classes
        self.rng = np.random.default_rng(seed)

        # ── Network Architecture Weights ─────────────────────────────────────────
        # Conv1D Layer 1: in_features -> 24 filters, kernel size 3
        # Conv1D Layer 2: 24 -> 32 filters, kernel size 3
        # Global Max Pooling -> Dense 32 -> 16 -> Output Heads
        k_init_1 = np.sqrt(2.0 / (3 * in_features))
        self.w_conv1 = self.rng.normal(0, k_init_1, (24, in_features, 3)).astype(np.float32)
        self.b_conv1 = np.zeros((24,), dtype=np.float32)

        k_init_2 = np.sqrt(2.0 / (3 * 24))
        self.w_conv2 = self.rng.normal(0, k_init_2, (32, 24, 3)).astype(np.float32)
        self.b_conv2 = np.zeros((32,), dtype=np.float32)

        k_init_fc = np.sqrt(2.0 / 32)
        self.w_fc1 = self.rng.normal(0, k_init_fc, (32, 16)).astype(np.float32)
        self.b_fc1 = np.zeros((16,), dtype=np.float32)

        # Head 1: Ocular State (0: OPEN, 1: CLOSING, 2: CLOSED, 3: OPENING)
        self.w_state = self.rng.normal(0, 0.1, (16, num_classes)).astype(np.float32)
        self.b_state = np.zeros((num_classes,), dtype=np.float32)

        # Head 2: Blink Event Confidence (Scalar 0.0 to 1.0)
        self.w_conf = self.rng.normal(0, 0.1, (16, 1)).astype(np.float32)
        self.b_conf = np.zeros((1,), dtype=np.float32)

        # Attempt to load trained checkpoint if available
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.normpath(os.path.join(base_dir, "..", "..", "..", "..", "ml", "models", "blink_temporal_model.npz")),
            os.path.normpath(os.path.join(base_dir, "..", "..", "weights", "blink_temporal_model.npz")),
        ]
        for p in candidates:
            if os.path.exists(p):
                self.load_weights(p)
                break

    def _conv1d(self, x: np.ndarray, w: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        1D Convolution with 'same' zero-padding.
        x: (batch, in_channels, seq_len)
        w: (out_channels, in_channels, kernel_size)
        b: (out_channels,)
        """
        batch, in_c, seq = x.shape
        out_c, _, k_size = w.shape
        pad = k_size // 2
        x_padded = np.pad(x, ((0, 0), (0, 0), (pad, pad)), mode="constant")

        out = np.zeros((batch, out_c, seq), dtype=np.float32)
        for i in range(seq):
            window = x_padded[:, :, i : i + k_size]  # (batch, in_channels, k_size)
            # Tensor dot over in_channels and k_size
            out[:, :, i] = np.tensordot(window, w, axes=([1, 2], [1, 2])) + b
        return out

    def forward(self, x_seq: np.ndarray) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        """
        Forward pass over sequence.
        x_seq: (batch, seq_len, in_features) or (seq_len, in_features)
        Returns:
            state_probs: (batch, num_classes)
            blink_conf: (batch, 1)
            cache: intermediate activations for backprop
        """
        is_single = (x_seq.ndim == 2)
        if is_single:
            x_seq = np.expand_dims(x_seq, 0)

        # Transpose to (batch, in_features, seq_len)
        x_t = np.transpose(x_seq, (0, 2, 1)).astype(np.float32)

        # Layer 1: Conv1D + ReLU
        z1 = self._conv1d(x_t, self.w_conv1, self.b_conv1)
        a1 = np.maximum(0.0, z1)

        # Layer 2: Conv1D + ReLU
        z2 = self._conv1d(a1, self.w_conv2, self.b_conv2)
        a2 = np.maximum(0.0, z2)

        # Global Max Pooling over temporal sequence dimension
        pooled = np.max(a2, axis=2)  # (batch, 32)

        # FC 1 + ReLU
        z_fc = np.dot(pooled, self.w_fc1) + self.b_fc1
        a_fc = np.maximum(0.0, z_fc)  # (batch, 16)

        # State Head (Softmax)
        logits_state = np.dot(a_fc, self.w_state) + self.b_state
        exp_state = np.exp(logits_state - np.max(logits_state, axis=-1, keepdims=True))
        state_probs = exp_state / np.sum(exp_state, axis=-1, keepdims=True)

        # Confidence Head (Sigmoid)
        logits_conf = np.dot(a_fc, self.w_conf) + self.b_conf
        blink_conf = 1.0 / (1.0 + np.exp(-np.clip(logits_conf, -15.0, 15.0)))

        cache = {
            "x_t": x_t,
            "a1": a1,
            "a2": a2,
            "pooled": pooled,
            "a_fc": a_fc,
            "state_probs": state_probs,
            "blink_conf": blink_conf,
        }

        if is_single:
            return state_probs[0], blink_conf[0], cache
        return state_probs, blink_conf, cache

    def train_step(
        self,
        x_batch: np.ndarray,
        y_state: np.ndarray,
        y_conf: np.ndarray,
        lr: float = 0.005,
    ) -> float:
        """
        Executes one SGD / Adam optimization step with categorical cross-entropy and BCE.
        """
        batch_size = x_batch.shape[0]
        state_probs, blink_conf, cache = self.forward(x_batch)

        # Losses
        # Cross-Entropy for state
        eps = 1e-7
        one_hot = np.eye(self.num_classes)[y_state]
        ce_loss = -np.mean(np.sum(one_hot * np.log(state_probs + eps), axis=-1))

        # Binary Cross-Entropy for blink confidence
        y_c = y_conf.reshape(-1, 1)
        bce_loss = -np.mean(y_c * np.log(blink_conf + eps) + (1.0 - y_c) * np.log(1.0 - blink_conf + eps))

        total_loss = float(ce_loss + bce_loss)

        # Backward gradients
        d_logits_state = (state_probs - one_hot) / batch_size  # (batch, num_classes)
        d_logits_conf = (blink_conf - y_c) / batch_size        # (batch, 1)

        # Gradients for output heads
        a_fc = cache["a_fc"]
        grad_w_state = np.dot(a_fc.T, d_logits_state)
        grad_b_state = np.sum(d_logits_state, axis=0)

        grad_w_conf = np.dot(a_fc.T, d_logits_conf)
        grad_b_conf = np.sum(d_logits_conf, axis=0)

        # Backprop through a_fc
        d_a_fc = np.dot(d_logits_state, self.w_state.T) + np.dot(d_logits_conf, self.w_conf.T)
        d_z_fc = d_a_fc * (a_fc > 0.0)

        grad_w_fc1 = np.dot(cache["pooled"].T, d_z_fc)
        grad_b_fc1 = np.sum(d_z_fc, axis=0)

        # Gradient clipping to prevent exploding gradients
        for grad in [grad_w_state, grad_b_state, grad_w_conf, grad_b_conf, grad_w_fc1, grad_b_fc1]:
            np.clip(grad, -1.0, 1.0, out=grad)

        # Apply updates
        self.w_state -= lr * grad_w_state
        self.b_state -= lr * grad_b_state
        self.w_conf -= lr * grad_w_conf
        self.b_conf -= lr * grad_b_conf
        self.w_fc1 -= lr * grad_w_fc1
        self.b_fc1 -= lr * grad_b_fc1

        return total_loss

    def save_weights(self, path: str):
        """Saves model parameters to .npz file."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        np.savez_compressed(
            path,
            w_conv1=self.w_conv1,
            b_conv1=self.b_conv1,
            w_conv2=self.w_conv2,
            b_conv2=self.b_conv2,
            w_fc1=self.w_fc1,
            b_fc1=self.b_fc1,
            w_state=self.w_state,
            b_state=self.b_state,
            w_conf=self.w_conf,
            b_conf=self.b_conf,
        )

    def load_weights(self, path: str) -> bool:
        """Loads model parameters from .npz file if exists."""
        if not os.path.exists(path):
            return False
        try:
            data = np.load(path)
            self.w_conv1 = data["w_conv1"]
            self.b_conv1 = data["b_conv1"]
            self.w_conv2 = data["w_conv2"]
            self.b_conv2 = data["b_conv2"]
            self.w_fc1 = data["w_fc1"]
            self.b_fc1 = data["b_fc1"]
            self.w_state = data["w_state"]
            self.b_state = data["b_state"]
            self.w_conf = data["w_conf"]
            self.b_conf = data["b_conf"]
            return True
        except Exception:
            return False
