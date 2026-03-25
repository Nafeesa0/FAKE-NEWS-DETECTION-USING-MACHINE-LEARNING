"""
Generate visualization graphs and training summary from trained model
"""
import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, auc
from sklearn.metrics import precision_recall_curve, average_precision_score
from tensorflow.keras.models import load_model

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.facecolor'] = 'white'

# Create directories
os.makedirs('graphs', exist_ok=True)
os.makedirs('outputs', exist_ok=True)

print("Loading dataset...")
# Load and prepare data (same as training)
fake_df = pd.read_csv('dataset/Fake.csv')
true_df = pd.read_csv('dataset/True.csv')

fake_df['label'] = 0  # Fake news
true_df['label'] = 1  # True news

# Combine datasets
df = pd.concat([fake_df, true_df], ignore_index=True)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Combine title and text
df['content'] = df['title'] + ' ' + df['text']

# Split data
from sklearn.model_selection import train_test_split
train_data, temp_data = train_test_split(df, test_size=0.3, random_state=42, stratify=df['label'])
val_data, test_data = train_test_split(temp_data, test_size=0.5, random_state=42, stratify=temp_data['label'])

print(f"Training samples: {len(train_data)}")
print(f"Validation samples: {len(val_data)}")
print(f"Test samples: {len(test_data)}")

# Text preprocessing
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Download NLTK data
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\@\w+|\#', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word not in stop_words and len(word) > 2]
    tokens = [lemmatizer.lemmatize(word) for word in tokens]

    return ' '.join(tokens)

print("Preprocessing text...")
test_data['processed_content'] = test_data['content'].apply(preprocess_text)

# Load tokenizer and prepare sequences
print("Loading tokenizer...")
with open('models/tokenizer.pkl', 'rb') as f:
    tokenizer = pickle.load(f)

from tensorflow.keras.preprocessing.sequence import pad_sequences
MAX_SEQUENCE_LENGTH = 500

test_sequences = tokenizer.texts_to_sequences(test_data['processed_content'])
X_test = pad_sequences(test_sequences, maxlen=MAX_SEQUENCE_LENGTH, padding='post', truncating='post')
y_test = test_data['label'].values

# Load model
print("Loading trained model...")
model = load_model('models/fake_news_lstm_model.h5')

# Make predictions
print("Generating predictions...")
y_pred_proba = model.predict(X_test, verbose=0)
y_pred = (y_pred_proba > 0.5).astype(int).flatten()

# Calculate metrics
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
roc_auc = roc_auc_score(y_test, y_pred_proba)

print("\n" + "="*80)
print("MODEL EVALUATION RESULTS")
print("="*80)
print(f"Accuracy:  {accuracy*100:.2f}%")
print(f"Precision: {precision*100:.2f}%")
print(f"Recall:    {recall*100:.2f}%")
print(f"F1-Score:  {f1*100:.2f}%")
print(f"ROC AUC:   {roc_auc:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Fake', 'True']))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
print("\nConfusion Matrix:")
print(cm)

# Generate graphs
print("\nGenerating visualization graphs...")

# Graph 1: Confusion Matrix Heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=True,
            xticklabels=['Fake', 'True'], yticklabels=['Fake', 'True'],
            annot_kws={'size': 16}, linewidths=2, linecolor='black')
plt.title('Confusion Matrix - Fake News Detection', fontsize=16, fontweight='bold', pad=20)
plt.ylabel('Actual Label', fontsize=13)
plt.xlabel('Predicted Label', fontsize=13)
plt.savefig('graphs/confusion_matrix.png', dpi=300, bbox_inches='tight')
print("[OK] Confusion matrix saved: graphs/confusion_matrix.png")
plt.close()

# Graph 2: ROC Curve
fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
roc_auc_score_value = auc(fpr, tpr)

plt.figure(figsize=(10, 8))
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc_score_value:.4f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate', fontsize=12)
plt.ylabel('True Positive Rate', fontsize=12)
plt.title('Receiver Operating Characteristic (ROC) Curve', fontsize=14, fontweight='bold')
plt.legend(loc="lower right", fontsize=11)
plt.grid(True, alpha=0.3)
plt.savefig('graphs/roc_curve.png', dpi=300, bbox_inches='tight')
print("[OK] ROC curve saved: graphs/roc_curve.png")
plt.close()

# Graph 3: Precision-Recall Curve
precision_curve, recall_curve, _ = precision_recall_curve(y_test, y_pred_proba)
avg_precision = average_precision_score(y_test, y_pred_proba)

plt.figure(figsize=(10, 8))
plt.plot(recall_curve, precision_curve, color='blue', lw=2, label=f'PR curve (AP = {avg_precision:.4f})')
plt.xlabel('Recall', fontsize=12)
plt.ylabel('Precision', fontsize=12)
plt.title('Precision-Recall Curve', fontsize=14, fontweight='bold')
plt.legend(loc="lower left", fontsize=11)
plt.grid(True, alpha=0.3)
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.savefig('graphs/precision_recall_curve.png', dpi=300, bbox_inches='tight')
print("[OK] Precision-Recall curve saved: graphs/precision_recall_curve.png")
plt.close()

# Graph 4: Metrics Comparison Bar Chart
metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
metrics_values = [accuracy, precision, recall, f1]
colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12']

plt.figure(figsize=(10, 6))
bars = plt.bar(metrics_names, metrics_values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
plt.ylim([0, 1.1])
plt.ylabel('Score', fontsize=12)
plt.title('Model Performance Metrics Comparison', fontsize=14, fontweight='bold', pad=20)
plt.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bar, value in zip(bars, metrics_values):
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
             f'{value:.4f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('graphs/metrics_comparison.png', dpi=300, bbox_inches='tight')
print("[OK] Metrics comparison saved: graphs/metrics_comparison.png")
plt.close()

# Graph 5: Class Distribution in Dataset
class_counts = df['label'].value_counts().sort_index()
class_labels = ['Fake News', 'True News']
colors_pie = ['#e74c3c', '#2ecc71']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Pie chart
wedges, texts, autotexts = ax1.pie(class_counts, labels=class_labels, autopct='%1.1f%%',
                                     colors=colors_pie, startangle=90,
                                     explode=(0.05, 0.05), shadow=True,
                                     textprops={'fontsize': 11, 'weight': 'bold'})
ax1.set_title('Class Distribution in Dataset', fontsize=13, fontweight='bold', pad=20)

# Bar chart
ax2.bar(class_labels, class_counts.values, color=colors_pie, alpha=0.8, edgecolor='black', linewidth=1.5)
ax2.set_ylabel('Number of Articles', fontsize=11)
ax2.set_title('Article Count by Class', fontsize=13, fontweight='bold', pad=20)
ax2.grid(axis='y', alpha=0.3)

# Add count labels on bars
for i, (label, count) in enumerate(zip(class_labels, class_counts.values)):
    ax2.text(i, count + 500, str(count), ha='center', va='bottom',
             fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('graphs/class_distribution.png', dpi=300, bbox_inches='tight')
print("[OK] Class distribution saved: graphs/class_distribution.png")
plt.close()

# Graph 6: Prediction Distribution
pred_dist = pd.Series(y_pred).value_counts().sort_index()
pred_labels = ['Predicted Fake', 'Predicted True']

plt.figure(figsize=(10, 6))
bars = plt.bar(pred_labels, pred_dist.values, color=['#e74c3c', '#2ecc71'],
               alpha=0.8, edgecolor='black', linewidth=1.5)
plt.ylabel('Number of Predictions', fontsize=12)
plt.title('Test Set Prediction Distribution', fontsize=14, fontweight='bold', pad=20)
plt.grid(axis='y', alpha=0.3)

# Add count labels
for bar, count in zip(bars, pred_dist.values):
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 50,
             str(count), ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('graphs/prediction_distribution.png', dpi=300, bbox_inches='tight')
print("[OK] Prediction distribution saved: graphs/prediction_distribution.png")
plt.close()

# Generate Training Summary Report
summary_file = 'outputs/training_summary.txt'
with open(summary_file, 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("FAKE NEWS DETECTION MODEL - TRAINING SUMMARY\n")
    f.write("="*80 + "\n\n")

    f.write("DATASET INFORMATION:\n")
    f.write("-" * 40 + "\n")
    f.write(f"Total articles: {len(df):,}\n")
    f.write(f"Fake news articles: {len(fake_df):,}\n")
    f.write(f"True news articles: {len(true_df):,}\n")
    f.write(f"Training samples: {len(train_data):,}\n")
    f.write(f"Validation samples: {len(val_data):,}\n")
    f.write(f"Test samples: {len(test_data):,}\n\n")

    f.write("MODEL ARCHITECTURE:\n")
    f.write("-" * 40 + "\n")
    f.write("- Embedding Layer (128 dimensions)\n")
    f.write("- Spatial Dropout (0.2)\n")
    f.write("- Bidirectional LSTM (128 units)\n")
    f.write("- Bidirectional LSTM (64 units)\n")
    f.write("- Dense Layer (64 units, ReLU)\n")
    f.write("- Dropout (0.5)\n")
    f.write("- Dense Layer (32 units, ReLU)\n")
    f.write("- Dropout (0.3)\n")
    f.write("- Output Layer (1 unit, Sigmoid)\n\n")

    f.write("FINAL MODEL PERFORMANCE:\n")
    f.write("-" * 40 + "\n")
    f.write(f"Accuracy:  {accuracy*100:.2f}%\n")
    f.write(f"Precision: {precision*100:.2f}%\n")
    f.write(f"Recall:    {recall*100:.2f}%\n")
    f.write(f"F1-Score:  {f1*100:.2f}%\n")
    f.write(f"ROC AUC:   {roc_auc:.4f}\n\n")

    f.write("CONFUSION MATRIX:\n")
    f.write("-" * 40 + "\n")
    f.write(f"True Negatives:  {cm[0][0]:,}\n")
    f.write(f"False Positives: {cm[0][1]:,}\n")
    f.write(f"False Negatives: {cm[1][0]:,}\n")
    f.write(f"True Positives:  {cm[1][1]:,}\n\n")

    f.write("CLASSIFICATION REPORT:\n")
    f.write("-" * 40 + "\n")
    f.write(classification_report(y_test, y_pred, target_names=['Fake', 'True']))
    f.write("\n")

    f.write("GENERATED FILES:\n")
    f.write("-" * 40 + "\n")
    f.write("Models:\n")
    f.write("  - models/fake_news_lstm_model.h5\n")
    f.write("  - models/best_model.h5\n")
    f.write("  - models/tokenizer.pkl\n\n")
    f.write("Graphs:\n")
    f.write("  - graphs/training_history.png\n")
    f.write("  - graphs/confusion_matrix.png\n")
    f.write("  - graphs/roc_curve.png\n")
    f.write("  - graphs/precision_recall_curve.png\n")
    f.write("  - graphs/metrics_comparison.png\n")
    f.write("  - graphs/class_distribution.png\n")
    f.write("  - graphs/prediction_distribution.png\n\n")

    f.write("="*80 + "\n")
    f.write("Training completed successfully!\n")
    f.write("="*80 + "\n")

print(f"\n[OK] Training summary saved: {summary_file}")
print("\n" + "="*80)
print("ALL VISUALIZATION GRAPHS AND SUMMARY GENERATED SUCCESSFULLY!")
print("="*80)
print("\nGenerated files:")
print("  - graphs/confusion_matrix.png")
print("  - graphs/roc_curve.png")
print("  - graphs/precision_recall_curve.png")
print("  - graphs/metrics_comparison.png")
print("  - graphs/class_distribution.png")
print("  - graphs/prediction_distribution.png")
print("  - outputs/training_summary.txt")
