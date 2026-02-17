"""
Download HateXplain dataset directly from GitHub.
Source: https://github.com/hate-alert/HateXplain
"""
import json
import os
import urllib.request
from collections import Counter

print("=" * 70)
print("DOWNLOADING: HateXplain from GitHub")
print("=" * 70)

# Download raw JSON from GitHub
url = "https://raw.githubusercontent.com/hate-alert/HateXplain/master/Data/dataset.json"
print(f"Fetching from: {url}")

with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode())

print(f"Downloaded {len(data)} examples")

# Parse the data
label_map = {'hatespeech': 'hate', 'normal': 'normal', 'offensive': 'offensive'}

output = []
label_counts = Counter()
target_counts = Counter()

for post_id, item in data.items():
    # Reconstruct text from tokens
    text = ' '.join(item['post_tokens'])
    
    # Get annotator labels
    annotators = item['annotators']
    annotator_labels = [a['label'] for a in annotators]
    
    # Majority vote
    majority = Counter(annotator_labels).most_common(1)[0][0]
    label = label_map.get(majority, majority)
    label_counts[label] += 1
    
    # Agreement score
    agreement = max(Counter(annotator_labels).values()) / len(annotator_labels)
    
    # Target groups
    targets = []
    for a in annotators:
        if 'target' in a:
            targets.extend(a['target'])
    main_target = Counter(targets).most_common(1)[0][0] if targets else 'none'
    
    if label == 'hate':
        target_counts[main_target] += 1
    
    output.append({
        'text': text,
        'label': label,
        'agreement': round(agreement, 2),
        'target': main_target,
        'annotator_count': len(annotators),
        'source': 'hatexplain'
    })

# Save
with open('hatexplain_raw.jsonl', 'w') as f:
    for item in output:
        f.write(json.dumps(item) + '\n')

print(f"\n✅ Saved to: hatexplain_raw.jsonl")

# Stats
print(f"\n" + "=" * 70)
print("DATASET STATISTICS")
print("=" * 70)

print(f"\nTotal examples: {len(output)}")

print(f"\nLabel Distribution:")
for label, count in sorted(label_counts.items()):
    pct = count * 100 // len(output)
    bar = "█" * (pct // 2)
    print(f"  {label:12} {count:5} ({pct:2}%) {bar}")

# Agreement
agreements = [item['agreement'] for item in output]
print(f"\nAnnotator Agreement:")
print(f"  100% agree (3/3): {sum(1 for a in agreements if a == 1.0):5} examples")
print(f"   67% agree (2/3): {sum(1 for a in agreements if a >= 0.66 and a < 1.0):5} examples")

print(f"\nHate Speech Targets (top 10):")
for target, count in target_counts.most_common(10):
    print(f"  {target:20} {count:4}")

print(f"\n" + "=" * 70)
print("READY FOR DEEP ANALYSIS")
print("=" * 70)
