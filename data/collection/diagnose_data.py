"""
Diagnose why model performance is poor.
"""
import json
from collections import Counter
from pathlib import Path

print("=" * 70)
print("DIAGNOSING TRAINING DATA")
print("=" * 70)

final_dir = Path("../datasets/curated/final")

# Load data
with open(final_dir / "train.jsonl") as f:
    train = [json.loads(line) for line in f]

with open(final_dir / "val.jsonl") as f:
    val = [json.loads(line) for line in f]

# 1. Check class balance
print("\n1. CLASS BALANCE:")
train_labels = Counter(d['label'] for d in train)
val_labels = Counter(d['label'] for d in val)

print(f"   Train: {dict(train_labels)}")
print(f"   Val:   {dict(val_labels)}")
print(f"   Ratio: {train_labels['toxic']/train_labels['safe']:.2f}:1 toxic:safe")

# 2. Check text length distribution
print("\n2. TEXT LENGTH:")
toxic_lens = [len(d['text'].split()) for d in train if d['label'] == 'toxic']
safe_lens = [len(d['text'].split()) for d in train if d['label'] == 'safe']

print(f"   Toxic avg: {sum(toxic_lens)/len(toxic_lens):.1f} words")
print(f"   Safe avg:  {sum(safe_lens)/len(safe_lens):.1f} words")

# 3. Check for duplicates or near-duplicates
print("\n3. DUPLICATE CHECK:")
texts = [d['text'][:100].lower() for d in train]
unique = len(set(texts))
print(f"   Total: {len(texts)}, Unique: {unique}, Duplicates: {len(texts)-unique}")

# 4. Check source distribution
print("\n4. SOURCE DISTRIBUTION:")
for label in ['toxic', 'safe']:
    print(f"\n   {label.upper()}:")
    sources = Counter(d.get('source', 'unknown') for d in train if d['label'] == label)
    for src, count in sources.most_common():
        print(f"      {src}: {count}")

# 5. Check category distribution for toxic
print("\n5. TOXIC CATEGORY DISTRIBUTION:")
cats = Counter(d['category'] for d in train if d['label'] == 'toxic')
for cat, count in cats.most_common():
    print(f"   {cat}: {count}")

# 6. Sample problematic cases
print("\n6. SAMPLE TEXTS:")
print("\n   TOXIC samples:")
toxic_samples = [d for d in train if d['label'] == 'toxic'][:5]
for d in toxic_samples:
    print(f"      [{d['category']:15}] {d['text'][:60]}...")

print("\n   SAFE samples:")
safe_samples = [d for d in train if d['label'] == 'safe'][:5]
for d in safe_samples:
    print(f"      [{d['source']:15}] {d['text'][:60]}...")

# 7. Check for mislabels
print("\n7. POTENTIAL MISLABELS:")
toxic_words = ['kill', 'hate', 'die', 'fuck', 'shit', 'stupid', 'idiot', 
               'chutiya', 'bhenchod', 'madarchod', 'bc', 'mc']

mislabeled_safe = []
for d in train:
    if d['label'] == 'safe':
        text_lower = d['text'].lower()
        found = [w for w in toxic_words if w in text_lower]
        if found and len(d['text']) < 100:
            mislabeled_safe.append((d['text'][:60], found))

print(f"   Safe texts with toxic words: {len(mislabeled_safe)}")
for text, words in mislabeled_safe[:10]:
    print(f"      [{words}] {text}...")

print("\n" + "=" * 70)
