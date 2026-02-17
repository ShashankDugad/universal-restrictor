"""
Create clean training data from HateXplain.
Strategy:
1. Use only high-agreement (100%) samples for reliability
2. Map labels to our categories
3. Handle edge cases
"""
import json
import random
from collections import Counter

print("=" * 70)
print("CREATING CLEAN HATEXPLAIN DATASET")
print("=" * 70)

# Load raw data
with open('hatexplain_raw.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

# Filter to high agreement only
high_agreement = [d for d in data if d['agreement'] == 1.0]
print(f"\nUsing high-agreement samples only: {len(high_agreement)}")

# Map to our categories
# hate → hate_speech
# offensive → harassment  
# normal → safe

clean_data = {
    'hate_speech': [],
    'harassment': [],
    'safe': []
}

for item in high_agreement:
    text = item['text'].strip()
    
    # Skip very short ambiguous text (≤3 words)
    if len(text.split()) <= 3:
        continue
    
    # Skip texts that are mostly usernames/mentions
    if text.count('<user>') > 3:
        continue
    
    if item['label'] == 'hate':
        clean_data['hate_speech'].append({
            'text': text,
            'label': 'toxic',
            'category': 'hate_speech',
            'target': item['target'],
            'source': 'hatexplain',
            'agreement': item['agreement']
        })
    elif item['label'] == 'offensive':
        clean_data['harassment'].append({
            'text': text,
            'label': 'toxic',
            'category': 'harassment',
            'target': item['target'],
            'source': 'hatexplain',
            'agreement': item['agreement']
        })
    elif item['label'] == 'normal':
        clean_data['safe'].append({
            'text': text,
            'label': 'safe',
            'category': 'safe',
            'target': 'none',
            'source': 'hatexplain',
            'agreement': item['agreement']
        })

# Stats
print(f"\nCleaned data distribution:")
for cat, items in clean_data.items():
    print(f"  {cat}: {len(items)}")

# Save each category
for cat, items in clean_data.items():
    filename = f'hatexplain_{cat}.jsonl'
    with open(filename, 'w') as f:
        for item in items:
            f.write(json.dumps(item) + '\n')
    print(f"  Saved: {filename}")

# Also save combined
all_clean = []
for items in clean_data.values():
    all_clean.extend(items)

with open('hatexplain_clean.jsonl', 'w') as f:
    for item in all_clean:
        f.write(json.dumps(item) + '\n')

print(f"\n✅ Saved combined: hatexplain_clean.jsonl ({len(all_clean)} samples)")

# Show samples from each category
print("\n" + "=" * 70)
print("SAMPLE VERIFICATION")
print("=" * 70)

random.seed(42)
for cat, items in clean_data.items():
    print(f"\n--- {cat.upper()} ---")
    for item in random.sample(items, min(3, len(items))):
        print(f"  {item['text'][:70]}...")

print("\n" + "=" * 70)
print(f"HATEXPLAIN COMPLETE: {len(all_clean)} clean samples ready")
print("=" * 70)
