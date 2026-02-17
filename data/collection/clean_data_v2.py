"""
Aggressive data cleaning - fix mislabeled samples.
"""
import json
import random
from collections import Counter
from pathlib import Path

print("=" * 70)
print("AGGRESSIVE DATA CLEANING v2")
print("=" * 70)

final_dir = Path("../datasets/curated/final")

# Load all data
with open(final_dir / "all.jsonl") as f:
    data = [json.loads(line) for line in f]

print(f"Original: {len(data)} samples")

# Words that indicate toxicity (if present, likely toxic)
STRONG_TOXIC = [
    # Slurs - always toxic
    'nigger', 'faggot', 'kike', 'chink', 'spic', 'wetback', 'tranny',
    # Hindi slurs - always toxic
    'chutiya', 'bhenchod', 'madarchod', 'bhosdike', 'randi', 'gandu',
    'kamina', 'harami', 'lodu', 'gaandu',
    # Threats
    'kill you', 'murder you', 'rape you',
]

# Words that are context-dependent
CONTEXT_TOXIC = ['fuck', 'shit', 'bitch', 'cunt', 'hate', 'die', 'stupid', 'idiot', 'nigga']

# Words that make context toxic
BAD_CONTEXT = ['you', 'your', 'u ', "u'", 'ur ', 'die', 'kill', 'hate you', 'fuck you']

# Fix mislabeled samples
fixed = 0
removed = 0
cleaned = []

for item in data:
    text = item['text']
    text_lower = text.lower()
    label = item['label']
    
    # Skip very short texts (< 5 words) - too ambiguous
    if len(text.split()) < 4:
        removed += 1
        continue
    
    # Check for strong toxic indicators
    has_strong_toxic = any(t in text_lower for t in STRONG_TOXIC)
    
    # If labeled safe but has strong toxic words -> fix to toxic
    if label == 'safe' and has_strong_toxic:
        item['label'] = 'toxic'
        item['category'] = 'harassment'
        item['fixed'] = 'strong_toxic'
        fixed += 1
    
    # Check context-dependent words
    elif label == 'safe':
        has_context_word = any(t in text_lower for t in CONTEXT_TOXIC)
        has_bad_context = any(t in text_lower for t in BAD_CONTEXT)
        
        # If has profanity + directed at someone -> toxic
        if has_context_word and has_bad_context:
            # Double check - is it really directed?
            directed_patterns = [
                'you are', 'you\'re', 'ur ', 'u are', 'your ', 
                'fuck you', 'hate you', 'kill you', 'die ', 
                'go back', 'get out', 'shut up'
            ]
            is_directed = any(p in text_lower for p in directed_patterns)
            
            if is_directed:
                item['label'] = 'toxic'
                item['category'] = 'harassment'
                item['fixed'] = 'directed_toxic'
                fixed += 1
    
    cleaned.append(item)

print(f"Fixed: {fixed} mislabeled samples")
print(f"Removed: {removed} too-short samples")
print(f"Final: {len(cleaned)} samples")

# Stats after cleaning
print(f"\nAfter cleaning:")
label_counts = Counter(d['label'] for d in cleaned)
for label, count in label_counts.items():
    pct = count * 100 // len(cleaned)
    print(f"  {label}: {count} ({pct}%)")

# Balance the dataset - undersample safe to match toxic
toxic_samples = [d for d in cleaned if d['label'] == 'toxic']
safe_samples = [d for d in cleaned if d['label'] == 'safe']

print(f"\nBefore balancing: {len(toxic_samples)} toxic, {len(safe_samples)} safe")

# Target: slight safe majority (1.1:1)
target_safe = int(len(toxic_samples) * 1.1)
if len(safe_samples) > target_safe:
    random.seed(42)
    safe_samples = random.sample(safe_samples, target_safe)

balanced = toxic_samples + safe_samples
random.shuffle(balanced)

print(f"After balancing: {len([d for d in balanced if d['label']=='toxic'])} toxic, {len([d for d in balanced if d['label']=='safe'])} safe")
print(f"Total: {len(balanced)}")

# Split
n = len(balanced)
train_end = int(n * 0.8)
val_end = int(n * 0.9)

train = balanced[:train_end]
val = balanced[train_end:val_end]
test = balanced[val_end:]

print(f"\nSplits: Train {len(train)}, Val {len(val)}, Test {len(test)}")

# Save
with open(final_dir / "train.jsonl", 'w') as f:
    for item in train:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

with open(final_dir / "val.jsonl", 'w') as f:
    for item in val:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

with open(final_dir / "test.jsonl", 'w') as f:
    for item in test:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

with open(final_dir / "all.jsonl", 'w') as f:
    for item in balanced:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f"\n✅ Saved cleaned & balanced dataset")

# Verify - check for remaining issues
print("\n" + "=" * 70)
print("VERIFICATION - checking for remaining issues")
print("=" * 70)

safe_with_issues = []
for d in balanced:
    if d['label'] == 'safe':
        text_lower = d['text'].lower()
        issues = [w for w in STRONG_TOXIC if w in text_lower]
        if issues:
            safe_with_issues.append((d['text'][:50], issues))

print(f"Safe samples with strong toxic words: {len(safe_with_issues)}")
if safe_with_issues:
    for text, issues in safe_with_issues[:5]:
        print(f"  [{issues}] {text}...")

# Show samples
print("\n" + "=" * 70)
print("SAMPLE VERIFICATION")
print("=" * 70)

print("\nTOXIC samples:")
for d in random.sample([d for d in balanced if d['label']=='toxic'], 5):
    print(f"  [{d['category']:12}] {d['text'][:60]}...")

print("\nSAFE samples:")
for d in random.sample([d for d in balanced if d['label']=='safe'], 5):
    print(f"  [{d.get('source','?'):12}] {d['text'][:60]}...")
