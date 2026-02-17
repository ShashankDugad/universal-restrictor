"""
Download Hindi/Hinglish hate speech datasets from HuggingFace.
"""
import json
from collections import Counter

print("=" * 70)
print("DOWNLOADING: Hindi Datasets from HuggingFace")
print("=" * 70)

all_data = []

# Try multiple Hindi datasets
datasets_to_try = [
    ("Hate-speech-CNERG/derogatory-detection-hindi", None),
    ("Siki-77/hindi_sexism_dataset", None),
    ("hindi_offensive", None),
]

try:
    from datasets import load_dataset
    
    # 1. Try HASOC 2021 (Hindi)
    print("\n1. Trying CONSTRAINT Hindi Hostility...")
    try:
        ds = load_dataset("Hate-speech-CNERG/hindi-constraint-2021")
        for split in ds:
            for item in ds[split]:
                all_data.append({
                    'text': item.get('text', item.get('tweet', '')),
                    'label': item.get('label', ''),
                    'source': 'hindi_constraint_2021'
                })
        print(f"   ✅ Loaded {len(all_data)} samples")
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:60]}")
    
    # 2. Try TRAC dataset
    print("\n2. Trying TRAC Aggression...")
    try:
        ds = load_dataset("trac2020", "hin")
        before = len(all_data)
        for split in ds:
            for item in ds[split]:
                all_data.append({
                    'text': item.get('Text', ''),
                    'label': item.get('Sub-task A', ''),
                    'source': 'trac2020_hindi'
                })
        print(f"   ✅ Loaded {len(all_data) - before} samples")
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:60]}")
    
    # 3. Try Multilingual hate speech
    print("\n3. Trying Multilingual Twitter...")
    try:
        ds = load_dataset("cardiffnlp/tweet_eval", "hate")
        before = len(all_data)
        for split in ds:
            for item in ds[split]:
                all_data.append({
                    'text': item.get('text', ''),
                    'label': 'hate' if item.get('label', 0) == 1 else 'not_hate',
                    'source': 'tweet_eval_hate'
                })
        print(f"   ✅ Loaded {len(all_data) - before} samples")
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:60]}")

    # 4. Try OffComBR-2 (offensive comments)
    print("\n4. Trying Civil Comments (subset)...")
    try:
        ds = load_dataset("civil_comments", split="train[:5000]")
        before = len(all_data)
        for item in ds:
            if item['toxicity'] > 0.5:
                label = 'toxic'
            else:
                label = 'safe'
            all_data.append({
                'text': item['text'][:500],
                'label': label,
                'toxicity_score': item['toxicity'],
                'source': 'civil_comments'
            })
        print(f"   ✅ Loaded {len(all_data) - before} samples")
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:60]}")

except ImportError:
    print("datasets library not available")

print(f"\n" + "=" * 70)
print(f"TOTAL FROM HUGGINGFACE: {len(all_data)} samples")
print("=" * 70)

if len(all_data) > 0:
    # Stats
    source_counts = Counter(d['source'] for d in all_data)
    label_counts = Counter(d['label'] for d in all_data)
    
    print(f"\nBy Source:")
    for src, count in source_counts.most_common():
        print(f"  {src}: {count}")
    
    print(f"\nBy Label:")
    for label, count in label_counts.most_common(10):
        print(f"  {label}: {count}")
    
    # Save
    with open('hf_datasets_raw.jsonl', 'w') as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Saved to: hf_datasets_raw.jsonl")
    
    # Show samples
    print(f"\n" + "=" * 70)
    print("SAMPLE TEXTS")
    print("=" * 70)
    
    import random
    random.seed(42)
    for src in source_counts.keys():
        samples = [d for d in all_data if d['source'] == src]
        print(f"\n--- {src} ---")
        for item in random.sample(samples, min(3, len(samples))):
            text = item['text'][:70]
            label = item['label']
            print(f"  [{label}] {text}...")

else:
    print("\nNo HuggingFace datasets loaded. Using existing manual Hindi data.")

print("\n" + "=" * 70)
