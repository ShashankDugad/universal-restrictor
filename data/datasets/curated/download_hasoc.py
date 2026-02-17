"""
Download and analyze HASOC dataset (Hindi Hate Speech).
Source: https://hasocfire.github.io/hasoc/2019/
This is the key dataset for Hindi/Hinglish content.
"""
import json
import os
import urllib.request
import csv
from collections import Counter
from io import StringIO

print("=" * 70)
print("DOWNLOADING: HASOC Hindi Dataset")
print("=" * 70)

# HASOC 2019 Hindi dataset from GitHub mirror
urls = {
    'train': 'https://raw.githubusercontent.com/hate-alert/DE-LIMIT/main/Data/HASOC/hindi_train.tsv',
    'test': 'https://raw.githubusercontent.com/hate-alert/DE-LIMIT/main/Data/HASOC/hindi_test.tsv'
}

all_data = []

for split, url in urls.items():
    print(f"\nFetching {split}...")
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read().decode('utf-8')
        
        reader = csv.DictReader(StringIO(content), delimiter='\t')
        count = 0
        for row in reader:
            all_data.append({
                'text': row.get('text', row.get('tweet', '')),
                'task1': row.get('task1', row.get('task_1', '')),  # HOF/NOT
                'task2': row.get('task2', row.get('task_2', '')),  # HATE/OFFN/PRFN
                'split': split
            })
            count += 1
        print(f"  Loaded {count} samples from {split}")
    except Exception as e:
        print(f"  Error loading {split}: {e}")

# If direct URLs fail, try alternative
if len(all_data) == 0:
    print("\nTrying alternative source...")
    # Try Hugging Face datasets
    try:
        from datasets import load_dataset
        dataset = load_dataset("hasoc19", "hindi", trust_remote_code=True)
        for split in dataset:
            for item in dataset[split]:
                all_data.append({
                    'text': item['text'],
                    'task1': item.get('task_1', item.get('label', '')),
                    'task2': item.get('task_2', ''),
                    'split': split
                })
    except:
        print("  HuggingFace also failed")

if len(all_data) == 0:
    print("\nFalling back to manual sample data for Hindi...")
    # Create sample Hindi hate speech data for demonstration
    # In production, you'd download the actual dataset
    hindi_samples = [
        {"text": "तुम बहुत अच्छे हो", "task1": "NOT", "task2": "NONE"},
        {"text": "नमस्ते, कैसे हो?", "task1": "NOT", "task2": "NONE"},
        {"text": "यह फिल्म बहुत बढ़िया है", "task1": "NOT", "task2": "NONE"},
        {"text": "साले कमीने", "task1": "HOF", "task2": "OFFN"},
        {"text": "बहुत बुरा इंसान है", "task1": "HOF", "task2": "OFFN"},
    ]
    all_data = hindi_samples
    print(f"  Using {len(all_data)} sample Hindi entries")

print(f"\nTotal loaded: {len(all_data)}")

if len(all_data) > 0:
    # Analyze
    task1_counts = Counter(d['task1'] for d in all_data)
    task2_counts = Counter(d['task2'] for d in all_data if d['task2'])
    
    print(f"\nTask 1 (Hate/Offensive or Not):")
    for label, count in task1_counts.most_common():
        pct = count * 100 // len(all_data)
        print(f"  {label}: {count} ({pct}%)")
    
    print(f"\nTask 2 (Type - for HOF only):")
    for label, count in task2_counts.most_common():
        print(f"  {label}: {count}")
    
    # Save
    with open('hasoc_hindi_raw.jsonl', 'w') as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Saved to: hasoc_hindi_raw.jsonl")
    
    # Show samples
    print(f"\n" + "=" * 70)
    print("SAMPLE TEXTS")
    print("=" * 70)
    
    import random
    random.seed(42)
    
    for label in ['HOF', 'NOT']:
        samples = [d for d in all_data if d['task1'] == label]
        if samples:
            print(f"\n--- {label} ---")
            for item in random.sample(samples, min(5, len(samples))):
                text = item['text'][:80] if len(item['text']) > 80 else item['text']
                print(f"  {text}")

print("\n" + "=" * 70)
