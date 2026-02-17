"""
Final dataset summary.
"""
import json
from collections import Counter
from pathlib import Path

print("=" * 70)
print("FINAL DATASET SUMMARY")
print("=" * 70)

final_dir = Path("../datasets/curated/final")

# Load all data
with open(final_dir / "all.jsonl") as f:
    data = [json.loads(line) for line in f]

with open(final_dir / "train.jsonl") as f:
    train = [json.loads(line) for line in f]

with open(final_dir / "val.jsonl") as f:
    val = [json.loads(line) for line in f]

with open(final_dir / "test.jsonl") as f:
    test = [json.loads(line) for line in f]

print(f"\n📊 SPLITS:")
print(f"  Train: {len(train)}")
print(f"  Val:   {len(val)}")
print(f"  Test:  {len(test)}")
print(f"  Total: {len(data)}")

print(f"\n📊 BY LABEL:")
label_counts = Counter(d['label'] for d in data)
for label, count in label_counts.most_common():
    pct = count * 100 // len(data)
    bar = "█" * (pct // 2)
    print(f"  {label:10}: {count:6} ({pct:2}%) {bar}")

print(f"\n📊 BY CATEGORY:")
cat_counts = Counter(d['category'] for d in data)
for cat, count in cat_counts.most_common():
    print(f"  {cat:15}: {count}")

print(f"\n📊 BY SOURCE:")
source_counts = Counter(d.get('source', 'unknown') for d in data)
for src, count in source_counts.most_common():
    print(f"  {src:20}: {count}")

# Language check
def has_hindi(text):
    # Devanagari
    if any('\u0900' <= c <= '\u097F' for c in text):
        return True
    # Hinglish words
    hinglish = ['bhai', 'yaar', 'kya', 'hai', 'nahi', 'kaise', 'accha', 'bahut', 'sala', 'pagal']
    return sum(1 for w in hinglish if w in text.lower()) >= 2

hindi_count = sum(1 for d in data if has_hindi(d['text']))
print(f"\n📊 LANGUAGE:")
print(f"  Hindi/Hinglish: {hindi_count}")
print(f"  English: {len(data) - hindi_count}")

print(f"\n" + "=" * 70)
print("DATASET READY FOR TRAINING")
print(f"=" * 70)
print(f"""
Files:
  {final_dir}/train.jsonl ({len(train)} samples)
  {final_dir}/val.jsonl ({len(val)} samples)  
  {final_dir}/test.jsonl ({len(test)} samples)
  {final_dir}/all.jsonl ({len(data)} samples)

To train:
  1. Upload to Google Colab
  2. Use train_moe_2stage_muril.ipynb
  3. Or fine-tune with Hugging Face Trainer

Balance: {label_counts['toxic']} toxic vs {label_counts['safe']} safe
Ratio: {label_counts['toxic']/label_counts['safe']:.2f}:1
""")
