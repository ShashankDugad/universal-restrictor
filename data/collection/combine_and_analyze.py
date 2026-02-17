"""
Combine all collected data and do deep analysis.
"""
import json
from collections import Counter
from pathlib import Path

print("=" * 70)
print("COMBINING ALL COLLECTED DATA")
print("=" * 70)

# Paths
curated_dir = Path("../datasets/curated")
collection_dir = Path(".")

all_data = []

# 1. Load HateXplain clean
hatexplain_path = curated_dir / "clean" / "hatexplain_clean.jsonl"
if hatexplain_path.exists():
    with open(hatexplain_path) as f:
        for line in f:
            item = json.loads(line)
            item['dataset'] = 'hatexplain'
            all_data.append(item)
    print(f"✅ HateXplain: {len([d for d in all_data if d['dataset']=='hatexplain'])} samples")
else:
    print(f"❌ HateXplain not found at {hatexplain_path}")

# 2. Load Reddit
reddit_path = collection_dir / "reddit_raw.jsonl"
if reddit_path.exists():
    with open(reddit_path) as f:
        for line in f:
            item = json.loads(line)
            item['dataset'] = 'reddit'
            item['label'] = 'unknown'  # Needs annotation
            all_data.append(item)
    print(f"✅ Reddit: {len([d for d in all_data if d['dataset']=='reddit'])} samples")

# 3. Load YouTube
youtube_path = collection_dir / "youtube_raw.jsonl"
if youtube_path.exists():
    with open(youtube_path) as f:
        for line in f:
            item = json.loads(line)
            item['dataset'] = 'youtube'
            item['label'] = 'unknown'  # Needs annotation
            all_data.append(item)
    print(f"✅ YouTube: {len([d for d in all_data if d['dataset']=='youtube'])} samples")

# 4. Load HF datasets (Tweet Eval, Civil Comments)
hf_path = curated_dir / "raw" / "hf_datasets_raw.jsonl"
if hf_path.exists():
    with open(hf_path) as f:
        for line in f:
            item = json.loads(line)
            item['dataset'] = item.get('source', 'hf_unknown')
            all_data.append(item)
    print(f"✅ HuggingFace datasets: {len([d for d in all_data if 'tweet_eval' in d['dataset'] or 'civil' in d['dataset']])} samples")

print(f"\n{'='*70}")
print(f"TOTAL: {len(all_data)} samples")
print(f"{'='*70}")

# Analysis
print("\n📊 BY DATASET:")
dataset_counts = Counter(d['dataset'] for d in all_data)
for ds, count in dataset_counts.most_common():
    print(f"  {ds}: {count}")

print("\n📊 BY LABEL:")
label_counts = Counter(d.get('label', 'unknown') for d in all_data)
for label, count in label_counts.most_common():
    print(f"  {label}: {count}")

# Check what needs annotation
needs_annotation = [d for d in all_data if d.get('label') == 'unknown']
print(f"\n⚠️ NEEDS ANNOTATION: {len(needs_annotation)} samples")
print(f"  Reddit: {len([d for d in needs_annotation if d['dataset']=='reddit'])}")
print(f"  YouTube: {len([d for d in needs_annotation if d['dataset']=='youtube'])}")

# Check language distribution
def detect_script(text):
    has_devanagari = any('\u0900' <= c <= '\u097F' for c in text)
    has_latin = any(c.isalpha() and c.isascii() for c in text)
    if has_devanagari and has_latin:
        return 'mixed'
    elif has_devanagari:
        return 'hindi'
    else:
        return 'english'

script_counts = Counter(detect_script(d.get('text', '')) for d in all_data)
print(f"\n📊 BY SCRIPT:")
for script, count in script_counts.most_common():
    print(f"  {script}: {count}")

# Sample from each dataset
print(f"\n{'='*70}")
print("SAMPLES FROM EACH DATASET")
print(f"{'='*70}")

import random
random.seed(42)

for ds in ['hatexplain', 'reddit', 'youtube']:
    samples = [d for d in all_data if d['dataset'] == ds]
    if samples:
        print(f"\n--- {ds.upper()} ---")
        for s in random.sample(samples, min(3, len(samples))):
            text = s.get('text', '')[:70]
            label = s.get('label', 'unknown')
            print(f"  [{label:10}] {text}...")

# Save combined
with open('combined_raw.jsonl', 'w') as f:
    for item in all_data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f"\n✅ Saved combined data to: combined_raw.jsonl")

# Save what needs annotation separately
with open('needs_annotation.jsonl', 'w') as f:
    for item in needs_annotation:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f"✅ Saved {len(needs_annotation)} items needing annotation to: needs_annotation.jsonl")
