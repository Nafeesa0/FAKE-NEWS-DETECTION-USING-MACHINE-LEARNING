"""
NLP Utilities — text preprocessing for the BiLSTM fake news model.
"""

import re
import pickle
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Download required NLTK data on first import
for _pkg in ('stopwords', 'punkt', 'punkt_tab', 'wordnet', 'omw-1.4'):
    try:
        nltk.data.find(f'corpora/{_pkg}' if _pkg not in ('punkt', 'punkt_tab') else f'tokenizers/{_pkg}')
    except LookupError:
        nltk.download(_pkg, quiet=True)


class TextPreprocessor:
    """Cleans and vectorises raw news text for the BiLSTM model."""

    def __init__(self, tokenizer_path='models/tokenizer.pkl', max_length=500):
        self.max_length = max_length
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))

        try:
            with open(tokenizer_path, 'rb') as f:
                self.tokenizer = pickle.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Tokenizer not found at '{tokenizer_path}'. "
                "Run ml_pipeline/train_model.py first."
            )

    def clean_text(self, text):
        """Lowercase, strip URLs, mentions, special chars and extra whitespace."""
        if not isinstance(text, str):
            return ""
        text = text.lower()
        text = re.sub(r'https?\S+|www\.\S+', '', text)
        text = re.sub(r'[@#]\w+', '', text)
        text = re.sub(r'[^a-z\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def tokenize_and_lemmatize(self, text):
        """Tokenize, remove stopwords, lemmatize."""
        tokens = word_tokenize(text)
        tokens = [w for w in tokens if w not in self.stop_words and len(w) > 2]
        tokens = [self.lemmatizer.lemmatize(w) for w in tokens]
        return ' '.join(tokens)

    def preprocess(self, text):
        """Full pipeline: clean → tokenize → lemmatize."""
        return self.tokenize_and_lemmatize(self.clean_text(text))

    def prepare_for_model(self, text):
        """Preprocess text and return a padded integer sequence (1 × max_length)."""
        processed = self.preprocess(text)
        sequence  = self.tokenizer.texts_to_sequences([processed])
        return pad_sequences(sequence, maxlen=self.max_length, padding='post', truncating='post')
