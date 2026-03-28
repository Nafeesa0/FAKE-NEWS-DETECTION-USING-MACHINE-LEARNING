"""
Model Predictor — loads the trained BiLSTM model and scores news articles.

TF 2.x / BiLSTM note:
  The model uses recurrent_dropout > 0 on stacked Bidirectional LSTM layers.
  Calling model.predict() at inference time triggers TF's internal RNN dropout
  path which tries to concatenate hidden states from different-sized LSTM units
  (64 and 128), producing:
      INVALID_ARGUMENT: Shapes of all inputs must match: [64] != [128]

  Fix: call the model directly as model(input, training=False) so Keras
  explicitly disables all dropout masks rather than relying on the internal
  inference path that mishandles the stacked BiLSTM state shapes.
"""

import os
import logging
import numpy as np
import tensorflow as tf
from tensorflow import keras
from .nlp_utils import TextPreprocessor

logger = logging.getLogger(__name__)


class FakeNewsPredictor:
    """Singleton-friendly wrapper around the Keras BiLSTM model."""

    def __init__(
        self,
        model_path='ml_pipeline/models/fake_news_lstm_model.h5',
        tokenizer_path='ml_pipeline/models/tokenizer.pkl',
    ):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at '{model_path}'. "
                "Run ml_pipeline/train_model.py first."
            )

        # compile=False avoids re-building the optimizer state, which is not
        # needed for inference and can surface version-compatibility warnings.
        self.model = keras.models.load_model(model_path, compile=False)
        logger.info(f"BiLSTM model loaded from {model_path}")

        self.preprocessor = TextPreprocessor(tokenizer_path, max_length=500)
        logger.info("TextPreprocessor ready")

    def predict(self, text, title=''):
        """
        Score a news article.

        Returns a dict with:
            prediction            – 'real' or 'fake'
            confidence            – float 0–1
            confidence_percentage – formatted string e.g. '94.21%'
            probability_real      – float 0–1
            probability_fake      – float 0–1
        """
        full_text = f"{title} {text}".strip()
        sequence  = self.preprocessor.prepare_for_model(full_text)

        # Use direct model call with training=False instead of model.predict().
        # This explicitly disables recurrent_dropout masks, avoiding the
        # stacked BiLSTM hidden-state shape mismatch in TF 2.x.
        tensor    = tf.constant(sequence, dtype=tf.int32)
        output    = self.model(tensor, training=False)
        prob_real = float(output.numpy()[0][0])

        is_real    = prob_real > 0.5
        confidence = prob_real if is_real else (1.0 - prob_real)

        return {
            'prediction':            'real' if is_real else 'fake',
            'confidence':            confidence,
            'confidence_percentage': f"{confidence * 100:.2f}%",
            'probability_real':      prob_real,
            'probability_fake':      1.0 - prob_real,
        }


# ── Singleton ─────────────────────────────────────────────────────────────
_predictor_instance = None


def get_predictor():
    """Return the shared FakeNewsPredictor, initialising it on first call."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = FakeNewsPredictor()
    return _predictor_instance
  """""""""""""""""""""""""""""""""""""""'
