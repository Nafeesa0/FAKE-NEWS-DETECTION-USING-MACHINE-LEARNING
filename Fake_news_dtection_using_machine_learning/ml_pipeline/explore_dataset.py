import pandas as pd
import numpy as np

# Load datasets
print("Loading datasets...")
fake_df = pd.read_csv('dataset/Fake.csv')
true_df = pd.read_csv('dataset/True.csv')

# Add labels
fake_df['label'] = 0  # Fake news
true_df['label'] = 1  # True news

print("\n=== FAKE NEWS DATASET ===")
print(f"Shape: {fake_df.shape}")
print(f"\nColumns: {fake_df.columns.tolist()}")
print(f"\nFirst few rows:")
print(fake_df.head(2))
print(f"\nData types:")
print(fake_df.dtypes)
print(f"\nMissing values:")
print(fake_df.isnull().sum())
print(f"\nSubject distribution:")
print(fake_df['subject'].value_counts())

print("\n\n=== TRUE NEWS DATASET ===")
print(f"Shape: {true_df.shape}")
print(f"\nColumns: {true_df.columns.tolist()}")
print(f"\nFirst few rows:")
print(true_df.head(2))
print(f"\nData types:")
print(true_df.dtypes)
print(f"\nMissing values:")
print(true_df.isnull().sum())
print(f"\nSubject distribution:")
print(true_df['subject'].value_counts())

# Combine datasets
combined_df = pd.concat([fake_df, true_df], axis=0, ignore_index=True)
print("\n\n=== COMBINED DATASET ===")
print(f"Total samples: {len(combined_df)}")
print(f"Fake news: {len(fake_df)} ({len(fake_df)/len(combined_df)*100:.2f}%)")
print(f"True news: {len(true_df)} ({len(true_df)/len(combined_df)*100:.2f}%)")
print(f"\nLabel distribution:")
print(combined_df['label'].value_counts())
