"""
Deep analysis of HateXplain dataset.
Goal: Verify data quality before using for training.
"""
import json
import random
from collections import Counter

print("=" * 70)
print("DEEP ANALYSIS: HateXplain")
print("=" * 70)

# Load data
with open('hatexplain_raw.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

# ============================================================
# 1. HIGH AGREEMENT SAMPLES (most reliable)
# ============================================================
print("\n" + "=" * 70)
print("1. HIGH AGREEMENT SAMPLES (100% annotator agreement)")
print("=" * 70)

high_agreement = [d for d in data if d['agreement'] == 1.0]
print(f"\nTotal high-agreement samples: {len(high_agreement)}")

for label in ['hate', 'offensive', 'normal']:
    samples = [d for d in high_agreement if d['label'] == label]
    print(f"\n--- {label.upper()} ({len(samples)} samples) ---")
    random.seed(42)
    for item in random.sample(samples, min(5, len(samples))):
        text = item['text'][:80]
        target = item['target']
        print(f"  [{target:12}] {text}...")

# ============================================================
# 2. LOW AGREEMENT SAMPLES (potentially mislabeled)
# ============================================================
print("\n" + "=" * 70)
print("2. LOW AGREEMENT SAMPLES (67% agreement - controversial)")
print("=" * 70)

low_agreement = [d for d in data if d['agreement'] < 1.0]
print(f"\nTotal low-agreement samples: {len(low_agreement)}")

for label in ['hate', 'offensive', 'normal']:
    samples = [d for d in low_agreement if d['label'] == label]
    print(f"\n--- {label.upper()} ({len(samples)} samples) ---")
    random.seed(43)
    for item in random.sample(samples, min(5, len(samples))):
        text = item['text'][:80]
        target = item['target']
        print(f"  [{target:12}] {text}...")

# ============================================================
# 3. CHECK FOR PROBLEMATIC PATTERNS
# ============================================================
print("\n" + "=" * 70)
print("3. PROBLEMATIC PATTERN CHECK")
print("=" * 70)

# Check "normal" samples for slurs (potential mislabels)
slurs = ['nigga', 'nigger', 'faggot', 'fag', 'retard', 'cunt', 'kike', 'chink']
normal_with_slurs = []
for item in data:
    if item['label'] == 'normal':
        text_lower = item['text'].lower()
        found_slurs = [s for s in slurs if s in text_lower]
        if found_slurs:
            normal_with_slurs.append((item['text'][:60], found_slurs, item['agreement']))

print(f"\n'Normal' samples containing slurs: {len(normal_with_slurs)}")
if normal_with_slurs:
    print("Examples (may be reclaimed usage or context-dependent):")
    for text, found, agree in normal_with_slurs[:10]:
        print(f"  [{agree}] {text}... (contains: {found})")

# Check "hate" samples that might be safe
safe_indicators = ['just kidding', 'jk', 'satire', 'sarcasm', '/s']
hate_maybe_safe = []
for item in data:
    if item['label'] == 'hate':
        text_lower = item['text'].lower()
        found = [s for s in safe_indicators if s in text_lower]
        if found:
            hate_maybe_safe.append((item['text'][:60], found))

print(f"\n'Hate' samples with satire indicators: {len(hate_maybe_safe)}")
for text, found in hate_maybe_safe[:5]:
    print(f"  {text}... (contains: {found})")

# ============================================================
# 4. TEXT LENGTH ANALYSIS
# ============================================================
print("\n" + "=" * 70)
print("4. TEXT LENGTH ANALYSIS")
print("=" * 70)

for label in ['hate', 'offensive', 'normal']:
    samples = [d for d in data if d['label'] == label]
    lengths = [len(d['text'].split()) for d in samples]
    avg_len = sum(lengths) / len(lengths)
    min_len = min(lengths)
    max_len = max(lengths)
    print(f"{label:12}: avg={avg_len:.1f} words, min={min_len}, max={max_len}")

# Very short samples (might be context-dependent)
short_samples = [d for d in data if len(d['text'].split()) <= 3]
print(f"\nVery short samples (≤3 words): {len(short_samples)}")
for item in random.sample(short_samples, min(10, len(short_samples))):
    print(f"  [{item['label']:10}] {item['text']}")

# ============================================================
# 5. QUALITY VERDICT
# ============================================================
print("\n" + "=" * 70)
print("5. QUALITY VERDICT")
print("=" * 70)

total = len(data)
high_quality = len([d for d in data if d['agreement'] == 1.0])
medium_quality = len([d for d in data if d['agreement'] >= 0.67 and d['agreement'] < 1.0])

print(f"""
Dataset: HateXplain
Total samples: {total}
High quality (100% agreement): {high_quality} ({high_quality*100//total}%)
Medium quality (67% agreement): {medium_quality} ({medium_quality*100//total}%)
Normal with slurs: {len(normal_with_slurs)} (needs review)

RECOMMENDATION:
- USE high-agreement samples (100%): {high_quality} samples ✅
- REVIEW low-agreement samples before using
- FILTER 'normal' samples with slurs (keep only if contextually safe)

Categories for your use case:
- hate → toxic (harassment/hate_speech)
- offensive → toxic (harassment) 
- normal → safe
""")

print("=" * 70)
