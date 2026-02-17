"""
Create final training dataset by combining all sources.
"""
import json
import random
from collections import Counter
from pathlib import Path

print("=" * 70)
print("CREATING FINAL TRAINING DATASET")
print("=" * 70)

# Paths
curated_dir = Path("../datasets/curated")

all_data = []

# 1. HateXplain (already labeled)
hatexplain_path = curated_dir / "clean" / "hatexplain_clean.jsonl"
if hatexplain_path.exists():
    with open(hatexplain_path) as f:
        for line in f:
            item = json.loads(line)
            # Normalize labels
            if item.get('category') == 'hate_speech':
                label = 'toxic_hate_speech'
            elif item.get('category') == 'harassment':
                label = 'toxic_harassment'
            elif item.get('label') == 'safe':
                label = 'safe'
            else:
                label = 'toxic_harassment'  # Default toxic
            
            all_data.append({
                'text': item['text'],
                'label': label,
                'source': 'hatexplain'
            })
    print(f"✅ HateXplain: {len([d for d in all_data if d['source']=='hatexplain'])}")

# 2. Claude-annotated (Reddit + YouTube)
annotated_path = Path("annotated_by_claude.jsonl")
if annotated_path.exists():
    with open(annotated_path) as f:
        for line in f:
            item = json.loads(line)
            all_data.append({
                'text': item['text'],
                'label': item['label'],
                'source': item.get('dataset', 'unknown')
            })
    print(f"✅ Claude-annotated: {len([d for d in all_data if d['source'] in ['reddit', 'youtube']])}")

# 3. Tweet Eval (already labeled)
hf_path = curated_dir / "raw" / "hf_datasets_raw.jsonl"
if hf_path.exists():
    with open(hf_path) as f:
        for line in f:
            item = json.loads(line)
            if item.get('source') == 'tweet_eval_hate':
                label = 'toxic_hate_speech' if item.get('label') == 'hate' else 'safe'
                all_data.append({
                    'text': item['text'],
                    'label': label,
                    'source': 'tweet_eval'
                })
    print(f"✅ Tweet Eval: {len([d for d in all_data if d['source']=='tweet_eval'])}")

print(f"\n{'='*70}")
print(f"TOTAL: {len(all_data)} samples")
print(f"{'='*70}")

# Stats before cleaning
print("\n📊 BY SOURCE:")
source_counts = Counter(d['source'] for d in all_data)
for src, count in source_counts.most_common():
    print(f"  {src}: {count}")

print("\n📊 BY LABEL (raw):")
label_counts = Counter(d['label'] for d in all_data)
for label, count in label_counts.most_common():
    print(f"  {label}: {count}")

# Normalize labels to binary + category
def normalize_label(label):
    """Normalize to: safe, toxic_harassment, toxic_hate_speech, toxic_threat, toxic_sexual"""
    label = label.lower()
    if label in ['safe', 'not_hate', 'normal']:
        return 'safe', 'safe'
    elif 'harassment' in label:
        return 'toxic', 'harassment'
    elif 'hate' in label:
        return 'toxic', 'hate_speech'
    elif 'threat' in label or 'violence' in label:
        return 'toxic', 'violence'
    elif 'sexual' in label:
        return 'toxic', 'sexual'
    else:
        return 'toxic', 'harassment'

# Clean and normalize
cleaned = []
seen_texts = set()

for item in all_data:
    text = item['text'].strip()
    
    # Skip duplicates
    text_hash = hash(text[:200].lower())
    if text_hash in seen_texts:
        continue
    seen_texts.add(text_hash)
    
    # Skip too short
    if len(text) < 10:
        continue
    
    # Skip too long
    if len(text) > 1000:
        text = text[:1000]
    
    # Normalize label
    binary_label, category = normalize_label(item['label'])
    
    cleaned.append({
        'text': text,
        'label': binary_label,
        'category': category,
        'source': item['source']
    })

print(f"\n{'='*70}")
print(f"AFTER CLEANING: {len(cleaned)} samples")
print(f"{'='*70}")

print("\n📊 BY LABEL (final):")
label_counts = Counter(d['label'] for d in cleaned)
for label, count in label_counts.most_common():
    pct = count * 100 // len(cleaned)
    bar = "█" * (pct // 2)
    print(f"  {label:10}: {count:6} ({pct:2}%) {bar}")

print("\n📊 BY CATEGORY:")
cat_counts = Counter(d['category'] for d in cleaned)
for cat, count in cat_counts.most_common():
    print(f"  {cat}: {count}")

# Balance check
toxic_count = len([d for d in cleaned if d['label'] == 'toxic'])
safe_count = len([d for d in cleaned if d['label'] == 'safe'])
print(f"\n⚖️ BALANCE: {toxic_count} toxic vs {safe_count} safe")
print(f"   Ratio: {toxic_count/safe_count:.2f}:1" if safe_count > 0 else "")

# Split into train/val/test
random.seed(42)
random.shuffle(cleaned)

n = len(cleaned)
train_end = int(n * 0.8)
val_end = int(n * 0.9)

train = cleaned[:train_end]
val = cleaned[train_end:val_end]
test = cleaned[val_end:]

print(f"\n📦 SPLITS:")
print(f"  Train: {len(train)}")
print(f"  Val:   {len(val)}")
print(f"  Test:  {len(test)}")

# Save
output_dir = Path("../datasets/curated/final")
output_dir.mkdir(exist_ok=True)

with open(output_dir / "train.jsonl", 'w') as f:
    for item in train:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

with open(output_dir / "val.jsonl", 'w') as f:
    for item in val:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

with open(output_dir / "test.jsonl", 'w') as f:
    for item in test:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

with open(output_dir / "all.jsonl", 'w') as f:
    for item in cleaned:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f"\n✅ Saved to: {output_dir}")
print(f"   - train.jsonl ({len(train)} samples)")
print(f"   - val.jsonl ({len(val)} samples)")
print(f"   - test.jsonl ({len(test)} samples)")
print(f"   - all.jsonl ({len(cleaned)} samples)")

# Show samples
print(f"\n{'='*70}")
print("SAMPLE VERIFICATION")
print(f"{'='*70}")

for label in ['safe', 'toxic']:
    samples = [d for d in cleaned if d['label'] == label]
    print(f"\n--- {label.upper()} ---")
    for s in random.sample(samples, min(5, len(samples))):
        print(f"  [{s['category']:12}] {s['text'][:60]}...")
