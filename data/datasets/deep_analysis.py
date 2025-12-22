"""
Deep data analysis for MoE training readiness.
"""
import json
import os
import re
from collections import Counter, defaultdict

MOE_DIR = "data/datasets/moe"

print("=" * 70)
print("DEEP DATA ANALYSIS FOR MoE TRAINING")
print("=" * 70)

# Load all data
categories = {}
for filename in os.listdir(MOE_DIR):
    if filename.endswith(".jsonl") and filename != "router_train.jsonl":
        cat = filename.replace(".jsonl", "")
        categories[cat] = []
        with open(f"{MOE_DIR}/{filename}", "r") as f:
            for line in f:
                categories[cat].append(json.loads(line))

# ============================================================
# 1. CATEGORY BALANCE ANALYSIS
# ============================================================
print("\n📊 1. CATEGORY BALANCE ANALYSIS")
print("-" * 70)

total = sum(len(v) for v in categories.values())
print(f"{'Category':<15} | {'Count':>8} | {'%':>7} | {'Bar':<30}")
print("-" * 70)

for cat in sorted(categories.keys(), key=lambda x: len(categories[x]), reverse=True):
    count = len(categories[cat])
    pct = 100 * count / total
    bar = "█" * int(pct / 2)
    print(f"{cat:<15} | {count:>8} | {pct:>6.1f}% | {bar}")

# ============================================================
# 2. TEXT LENGTH DISTRIBUTION
# ============================================================
print("\n📏 2. TEXT LENGTH DISTRIBUTION")
print("-" * 70)
print(f"{'Category':<15} | {'Min':>5} | {'Max':>6} | {'Avg':>6} | {'Median':>7} | {'<20ch':>6} | {'>500ch':>7}")
print("-" * 70)

for cat in sorted(categories.keys()):
    lengths = sorted([len(ex["text"]) for ex in categories[cat]])
    short = sum(1 for l in lengths if l < 20)
    long_text = sum(1 for l in lengths if l > 500)
    median = lengths[len(lengths)//2] if lengths else 0
    avg = sum(lengths) // len(lengths) if lengths else 0
    print(f"{cat:<15} | {min(lengths):>5} | {max(lengths):>6} | {avg:>6} | {median:>7} | {short:>6} | {long_text:>7}")

# ============================================================
# 3. SOURCE DISTRIBUTION
# ============================================================
print("\n📦 3. SOURCE DISTRIBUTION PER CATEGORY")
print("-" * 70)

for cat in sorted(categories.keys()):
    sources = Counter(ex.get("source", "unknown") for ex in categories[cat])
    print(f"\n[{cat.upper()}]")
    for source, count in sources.most_common(5):
        pct = 100 * count / len(categories[cat])
        print(f"   {source:<30} | {count:>6} ({pct:>5.1f}%)")

# ============================================================
# 4. LABEL DISTRIBUTION (should all be toxic except safe)
# ============================================================
print("\n\n🏷️ 4. LABEL DISTRIBUTION CHECK")
print("-" * 70)

issues = []
for cat in sorted(categories.keys()):
    labels = Counter(ex.get("label", "unknown") for ex in categories[cat])
    if cat == "safe":
        toxic_count = labels.get("toxic", 0)
        if toxic_count > 0:
            issues.append(f"   ❌ {cat}: {toxic_count} toxic examples in safe category!")
    else:
        safe_count = labels.get("safe", 0)
        if safe_count > 0:
            issues.append(f"   ⚠️ {cat}: {safe_count} safe examples in toxic category")
    
    print(f"{cat:<15} | " + ", ".join(f"{l}:{c}" for l, c in labels.items()))

if issues:
    print("\n⚠️ LABEL ISSUES FOUND:")
    for issue in issues:
        print(issue)

# ============================================================
# 5. DUPLICATE ANALYSIS
# ============================================================
print("\n\n🔄 5. DUPLICATE ANALYSIS")
print("-" * 70)

for cat in sorted(categories.keys()):
    texts = [ex["text"].lower().strip() for ex in categories[cat]]
    unique = len(set(texts))
    dups = len(texts) - unique
    dup_pct = 100 * dups / len(texts) if texts else 0
    status = "✅" if dup_pct < 5 else "⚠️" if dup_pct < 15 else "❌"
    print(f"{cat:<15} | Total: {len(texts):>6} | Unique: {unique:>6} | Dups: {dups:>5} ({dup_pct:>4.1f}%) {status}")

# ============================================================
# 6. CROSS-CATEGORY CONTAMINATION CHECK
# ============================================================
print("\n\n🔀 6. CROSS-CATEGORY CONTAMINATION CHECK")
print("-" * 70)

# Build text-to-category mapping
text_to_cats = defaultdict(set)
for cat, examples in categories.items():
    for ex in examples:
        text_lower = ex["text"].lower().strip()
        text_to_cats[text_lower].add(cat)

# Find texts in multiple categories
multi_cat = {t: cats for t, cats in text_to_cats.items() if len(cats) > 1}
print(f"Texts appearing in multiple categories: {len(multi_cat)}")
if multi_cat:
    print("Examples:")
    for text, cats in list(multi_cat.items())[:5]:
        print(f"   '{text[:50]}...' → {cats}")

# ============================================================
# 7. CATEGORY-SPECIFIC QUALITY CHECKS
# ============================================================
print("\n\n🔍 7. CATEGORY-SPECIFIC QUALITY CHECKS")
print("-" * 70)

# Check hindi_abuse for actual Hindi content
print("\n[HINDI_ABUSE] - Checking for actual Hindi content...")
hindi_indicators = [
    "chod", "maa", "behen", "gandu", "kutt", "sala", "bhosdi", "lodu", 
    "randi", "harami", "mc", "bc", "bsdk", "tmkc", "gaand", "lund", "chut",
    "teri", "tere", "tujhe", "aukaat", "nikal", "bhag", "maar", "kamina"
]
hindi_examples = categories.get("hindi_abuse", [])
has_hindi = sum(1 for ex in hindi_examples if any(ind in ex["text"].lower() for ind in hindi_indicators))
no_hindi = len(hindi_examples) - has_hindi
print(f"   With Hindi indicators: {has_hindi} ({100*has_hindi/len(hindi_examples):.1f}%)")
print(f"   Without Hindi indicators: {no_hindi} ({100*no_hindi/len(hindi_examples):.1f}%)")

if no_hindi > 0:
    print("   Examples without Hindi:")
    for ex in hindi_examples:
        if not any(ind in ex["text"].lower() for ind in hindi_indicators):
            print(f"      '{ex['text'][:60]}...'")
            no_hindi -= 1
            if no_hindi <= 3:
                break

# Check dangerous for actual dangerous content
print("\n[DANGEROUS] - Checking for actual dangerous content...")
dangerous_indicators = [
    "bomb", "explosive", "weapon", "gun", "poison", "kill", "murder",
    "hack", "drug", "cocaine", "meth", "kidnap", "attack", "make", "how to"
]
dangerous_examples = categories.get("dangerous", [])
has_dangerous = sum(1 for ex in dangerous_examples if any(ind in ex["text"].lower() for ind in dangerous_indicators))
no_dangerous = len(dangerous_examples) - has_dangerous
print(f"   With dangerous indicators: {has_dangerous} ({100*has_dangerous/len(dangerous_examples):.1f}%)")
print(f"   Without dangerous indicators: {no_dangerous} ({100*no_dangerous/len(dangerous_examples):.1f}%)")

# Check self_harm for actual self-harm content
print("\n[SELF_HARM] - Checking for actual self-harm content...")
self_harm_indicators = [
    "suicide", "kill myself", "end my life", "want to die", "cut myself",
    "self harm", "kys", "kill yourself", "better off dead", "hurt myself",
    "fear", "grief", "sad", "depressed", "anxiety", "pain"
]
self_harm_examples = categories.get("self_harm", [])
has_self_harm = sum(1 for ex in self_harm_examples if any(ind in ex["text"].lower() for ind in self_harm_indicators))
no_self_harm = len(self_harm_examples) - has_self_harm
print(f"   With self-harm indicators: {has_self_harm} ({100*has_self_harm/len(self_harm_examples):.1f}%)")
print(f"   Without self-harm indicators: {no_self_harm} ({100*no_self_harm/len(self_harm_examples):.1f}%)")

# ============================================================
# 8. SAMPLE REVIEW PER CATEGORY
# ============================================================
print("\n\n📝 8. RANDOM SAMPLE REVIEW (5 per category)")
print("-" * 70)

import random
for cat in sorted(categories.keys()):
    print(f"\n[{cat.upper()}]")
    samples = random.sample(categories[cat], min(5, len(categories[cat])))
    for ex in samples:
        text = ex["text"][:70].replace("\n", " ")
        source = ex.get("source", "?")[:15]
        print(f"   [{source:<15}] {text}...")

# ============================================================
# 9. TRAINING READINESS SCORE
# ============================================================
print("\n\n" + "=" * 70)
print("📋 TRAINING READINESS SCORE")
print("=" * 70)

scores = {}
for cat in sorted(categories.keys()):
    if cat == "safe":
        continue
    
    score = 0
    issues_cat = []
    
    # Count score (0-25)
    count = len(categories[cat])
    if count >= 5000: score += 25
    elif count >= 2000: score += 20
    elif count >= 1000: score += 15
    elif count >= 500: score += 10
    else: 
        score += 5
        issues_cat.append(f"Low count ({count})")
    
    # Duplicate score (0-25)
    texts = [ex["text"].lower().strip() for ex in categories[cat]]
    dup_pct = 100 * (len(texts) - len(set(texts))) / len(texts)
    if dup_pct < 5: score += 25
    elif dup_pct < 10: score += 20
    elif dup_pct < 20: score += 15
    else: 
        score += 10
        issues_cat.append(f"High duplicates ({dup_pct:.1f}%)")
    
    # Length diversity (0-25)
    lengths = [len(ex["text"]) for ex in categories[cat]]
    length_std = (sum((l - sum(lengths)/len(lengths))**2 for l in lengths) / len(lengths)) ** 0.5
    if length_std > 100: score += 25
    elif length_std > 50: score += 20
    elif length_std > 20: score += 15
    else: 
        score += 10
        issues_cat.append("Low length diversity")
    
    # Source diversity (0-25)
    sources = Counter(ex.get("source", "unknown") for ex in categories[cat])
    if len(sources) >= 5: score += 25
    elif len(sources) >= 3: score += 20
    elif len(sources) >= 2: score += 15
    else: 
        score += 10
        issues_cat.append("Low source diversity")
    
    scores[cat] = (score, issues_cat)

print(f"\n{'Category':<15} | {'Score':>6} | {'Grade':<5} | Issues")
print("-" * 70)
for cat, (score, issues_cat) in sorted(scores.items(), key=lambda x: x[1][0], reverse=True):
    if score >= 90: grade = "A+"
    elif score >= 80: grade = "A"
    elif score >= 70: grade = "B"
    elif score >= 60: grade = "C"
    else: grade = "D"
    issues_str = ", ".join(issues_cat) if issues_cat else "None"
    print(f"{cat:<15} | {score:>6} | {grade:<5} | {issues_str}")

print("\n" + "=" * 70)
print("OVERALL ASSESSMENT")
print("=" * 70)
avg_score = sum(s[0] for s in scores.values()) / len(scores)
print(f"Average Score: {avg_score:.1f}/100")
if avg_score >= 80:
    print("✅ READY FOR MoE TRAINING")
elif avg_score >= 60:
    print("⚠️ ACCEPTABLE - Some categories need improvement")
else:
    print("❌ NOT READY - Significant data quality issues")
