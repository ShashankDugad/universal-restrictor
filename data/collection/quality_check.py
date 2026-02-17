"""
Quality check: Find mislabeled samples in the dataset.
"""
import json
import random
from collections import Counter
from pathlib import Path

print("=" * 70)
print("QUALITY CHECK: Finding Mislabeled Samples")
print("=" * 70)

# Load final dataset
final_dir = Path("../datasets/curated/final")
with open(final_dir / "all.jsonl") as f:
    data = [json.loads(line) for line in f]

print(f"Loaded {len(data)} samples")

# Words that should NEVER be in "safe" category
toxic_indicators = [
    # Slurs
    'nigger', 'nigga', 'faggot', 'fag', 'retard', 'cunt', 'kike', 'chink',
    'tranny', 'spic', 'wetback',
    # Hindi slurs
    'chutiya', 'bhenchod', 'madarchod', 'bhosdike', 'randi', 'gandu', 
    'kamina', 'harami', 'lodu',
    # Sexual explicit
    'eat that bitch', 'fuck her', 'rape', 'molest',
    # Violence
    'kill you', 'murder', 'beat the shit', 'kick your ass',
]

# Words that are often safe but flagged as toxic
safe_indicators = [
    'frustrated', 'frustrating', 'this is hard', 'hate mondays',
    'so tired', 'exhausted', 'annoying', 'disappointed',
]

# Find mislabeled "safe" samples
mislabeled_safe = []
for item in data:
    if item['label'] == 'safe':
        text_lower = item['text'].lower()
        for indicator in toxic_indicators:
            if indicator in text_lower:
                mislabeled_safe.append({
                    'text': item['text'][:100],
                    'indicator': indicator,
                    'source': item.get('source', 'unknown')
                })
                break

print(f"\n❌ SAFE samples with toxic indicators: {len(mislabeled_safe)}")
print("\nExamples:")
for item in mislabeled_safe[:20]:
    print(f"  [{item['source']:12}] '{item['indicator']}' in: {item['text'][:50]}...")

# Find potentially mislabeled "toxic" samples
mislabeled_toxic = []
for item in data:
    if item['label'] == 'toxic':
        text_lower = item['text'].lower()
        # Check if it's just frustration
        is_short = len(item['text'].split()) < 10
        has_safe_indicator = any(ind in text_lower for ind in safe_indicators)
        has_no_toxic = not any(ind in text_lower for ind in toxic_indicators)
        
        if is_short and has_safe_indicator and has_no_toxic:
            mislabeled_toxic.append({
                'text': item['text'][:100],
                'source': item.get('source', 'unknown')
            })

print(f"\n⚠️ TOXIC samples that might be safe: {len(mislabeled_toxic)}")
for item in mislabeled_toxic[:10]:
    print(f"  [{item['source']:12}] {item['text'][:60]}...")

# Summary
print(f"\n{'='*70}")
print("QUALITY SUMMARY")
print(f"{'='*70}")
print(f"Total samples: {len(data)}")
print(f"Likely mislabeled 'safe' → should be toxic: {len(mislabeled_safe)}")
print(f"Likely mislabeled 'toxic' → might be safe: {len(mislabeled_toxic)}")
print(f"Estimated error rate: {(len(mislabeled_safe) + len(mislabeled_toxic)) * 100 / len(data):.1f}%")

# Ask to fix
print(f"\n{'='*70}")
proceed = input("Fix mislabeled samples? (y/n): ")

if proceed.lower() == 'y':
    fixed_count = 0
    
    for item in data:
        text_lower = item['text'].lower()
        
        # Fix safe → toxic
        if item['label'] == 'safe':
            for indicator in toxic_indicators:
                if indicator in text_lower:
                    item['label'] = 'toxic'
                    item['category'] = 'harassment'
                    item['fixed'] = True
                    fixed_count += 1
                    break
    
    # Save fixed dataset
    with open(final_dir / "all.jsonl", 'w') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Recalculate splits
    random.seed(42)
    random.shuffle(data)
    n = len(data)
    train_end = int(n * 0.8)
    val_end = int(n * 0.9)
    
    with open(final_dir / "train.jsonl", 'w') as f:
        for item in data[:train_end]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    with open(final_dir / "val.jsonl", 'w') as f:
        for item in data[train_end:val_end]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    with open(final_dir / "test.jsonl", 'w') as f:
        for item in data[val_end:]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Fixed {fixed_count} mislabeled samples")
    
    # New stats
    label_counts = Counter(d['label'] for d in data)
    print(f"\nNew label distribution:")
    for label, count in label_counts.most_common():
        print(f"  {label}: {count}")
