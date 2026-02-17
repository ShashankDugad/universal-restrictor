"""
Smart quality fix - handles context for nuanced cases.
"""
import json
import random
from collections import Counter
from pathlib import Path

print("=" * 70)
print("SMART QUALITY FIX")
print("=" * 70)

final_dir = Path("../datasets/curated/final")
with open(final_dir / "all.jsonl") as f:
    data = [json.loads(line) for line in f]

print(f"Loaded {len(data)} samples")

# ALWAYS toxic - no context needed
always_toxic = [
    'nigger',  # Hard-R is always toxic
    'faggot', 'fag ',  # Slurs
    'kike', 'chink', 'spic', 'wetback', 'tranny',
    # Hindi slurs
    'chutiya', 'bhenchod', 'madarchod', 'bhosdike', 'randi', 
    'gandu', 'kamina', 'harami', 'lodu',
    # Violent
    'kill you', 'murder you', 'beat the shit', 'rape you',
]

# Context-dependent - need additional signals
context_dependent = {
    'nigga': ['shoot', 'kill', 'beat', 'fuck', 'hate', 'die', 'dead'],
    'bitch': ['kill', 'beat', 'rape', 'die', 'hate you', 'fuck you'],
    'cunt': ['kill', 'beat', 'rape', 'die', 'hate you'],
    'retard': ['kill', 'die', 'hate', 'worst'],
    'rape': ['will rape', 'gonna rape', 'should rape', 'deserves rape'],
}

# Words that indicate discussion ABOUT topic (not perpetrating)
discussion_indicators = [
    'victims of', 'speaking out', 'against', 'stop', 'report', 
    'awareness', 'survivor', 'assault is', 'is wrong',
]

fixed_count = 0
fixes_log = []

for item in data:
    if item['label'] != 'safe':
        continue
    
    text_lower = item['text'].lower()
    should_fix = False
    reason = ""
    
    # Check always-toxic words
    for toxic in always_toxic:
        if toxic in text_lower:
            should_fix = True
            reason = f"contains '{toxic}'"
            break
    
    # Check context-dependent words
    if not should_fix:
        for word, bad_contexts in context_dependent.items():
            if word in text_lower:
                # Check if discussing vs perpetrating
                is_discussion = any(ind in text_lower for ind in discussion_indicators)
                has_bad_context = any(ctx in text_lower for ctx in bad_contexts)
                
                if has_bad_context and not is_discussion:
                    should_fix = True
                    reason = f"'{word}' with violent context"
                    break
    
    if should_fix:
        item['label'] = 'toxic'
        item['category'] = 'harassment'
        item['fix_reason'] = reason
        fixed_count += 1
        fixes_log.append({
            'text': item['text'][:80],
            'reason': reason
        })

print(f"\n✅ Fixed {fixed_count} samples")

# Show some fixes
print(f"\nSample fixes:")
for fix in fixes_log[:15]:
    print(f"  [{fix['reason']:30}] {fix['text'][:45]}...")

# Save
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

# New stats
print(f"\n{'='*70}")
print("FINAL DATASET STATS")
print(f"{'='*70}")

label_counts = Counter(d['label'] for d in data)
for label, count in label_counts.most_common():
    pct = count * 100 // len(data)
    print(f"  {label:10}: {count:6} ({pct}%)")

cat_counts = Counter(d['category'] for d in data)
print(f"\nBy category:")
for cat, count in cat_counts.most_common():
    print(f"  {cat}: {count}")

print(f"\n✅ Saved fixed dataset to {final_dir}")
