"""
Analyze MoE dataset quality.
"""
import json
import os
from collections import defaultdict, Counter

MOE_DIR = "data/datasets/moe"

print("=" * 70)
print("MOE DATASET QUALITY ANALYSIS")
print("=" * 70)

# Load all category files
categories = {}
for filename in os.listdir(MOE_DIR):
    if filename.endswith(".jsonl") and filename != "router_train.jsonl":
        cat = filename.replace(".jsonl", "")
        categories[cat] = []
        with open(f"{MOE_DIR}/{filename}", "r") as f:
            for line in f:
                categories[cat].append(json.loads(line))

# 1. Category size analysis
print("\n📊 1. CATEGORY SIZE ANALYSIS")
print("-" * 70)
print(f"{'Category':<15} | {'Count':>8} | {'%':>6} | Status")
print("-" * 70)

total = sum(len(v) for v in categories.values())
for cat in sorted(categories.keys(), key=lambda x: len(categories[x]), reverse=True):
    count = len(categories[cat])
    pct = 100 * count / total
    
    if count < 100:
        status = "❌ CRITICAL - Need 5000+ examples"
    elif count < 500:
        status = "⚠️ LOW - Need more data"
    elif count < 2000:
        status = "⚠️ MEDIUM - Could use more"
    else:
        status = "✅ OK"
    
    print(f"{cat:<15} | {count:>8} | {pct:>5.1f}% | {status}")

# 2. Sample examples per category
print("\n📝 2. SAMPLE EXAMPLES PER CATEGORY")
print("-" * 70)
for cat in sorted(categories.keys()):
    print(f"\n[{cat.upper()}] ({len(categories[cat])} examples)")
    for ex in categories[cat][:3]:
        text = ex["text"][:60].replace("\n", " ")
        print(f"   • {text}...")

# 3. Text length analysis
print("\n📏 3. TEXT LENGTH ANALYSIS")
print("-" * 70)
print(f"{'Category':<15} | {'Min':>5} | {'Max':>6} | {'Avg':>6} | {'< 10 chars':>10}")
print("-" * 70)
for cat in sorted(categories.keys()):
    lengths = [len(ex["text"]) for ex in categories[cat]]
    short = sum(1 for l in lengths if l < 10)
    print(f"{cat:<15} | {min(lengths):>5} | {max(lengths):>6} | {sum(lengths)//len(lengths):>6} | {short:>10}")

# 4. Source distribution per category
print("\n📦 4. SOURCE DISTRIBUTION PER CATEGORY")
print("-" * 70)
for cat in sorted(categories.keys()):
    sources = Counter(ex.get("source", "unknown") for ex in categories[cat])
    top_sources = sources.most_common(3)
    source_str = ", ".join(f"{s}:{c}" for s, c in top_sources)
    print(f"{cat:<15} | {source_str}")

# 5. Potential misclassifications (spot check)
print("\n🔍 5. POTENTIAL MISCLASSIFICATION CHECK")
print("-" * 70)

# Check safe examples that might be toxic
safe_suspicious = []
toxic_keywords = ["kill", "hate", "die", "murder", "attack", "idiot", "stupid"]
for ex in categories.get("safe", []):
    text_lower = ex["text"].lower()
    for kw in toxic_keywords:
        if kw in text_lower:
            safe_suspicious.append(ex["text"][:60])
            break

print(f"\nSafe examples with toxic keywords ({len(safe_suspicious)} found):")
for text in safe_suspicious[:5]:
    print(f"   ⚠️ {text}...")

# Check if hindi_abuse has non-Hindi
hindi_non_hindi = []
hindi_indicators = ["chod", "maa", "behen", "gandu", "kutt", "sala", "bhosdi", "lodu", "randi", "harami"]
for ex in categories.get("hindi_abuse", []):
    text_lower = ex["text"].lower()
    if not any(ind in text_lower for ind in hindi_indicators):
        hindi_non_hindi.append(ex["text"][:60])

print(f"\nHindi abuse without Hindi indicators ({len(hindi_non_hindi)} found):")
for text in hindi_non_hindi[:5]:
    print(f"   ⚠️ {text}...")

# 6. Class balance for binary experts
print("\n⚖️ 6. EXPERT MODEL TRAINING READINESS")
print("-" * 70)
print(f"{'Expert':<15} | {'Toxic':>8} | {'Safe Needed':>12} | {'Status'}")
print("-" * 70)

safe_pool = len(categories.get("safe", []))
for cat in sorted(categories.keys()):
    if cat == "safe":
        continue
    toxic_count = len(categories[cat])
    safe_needed = int(toxic_count * 1.5)  # 40/60 balance
    
    if toxic_count < 100:
        status = "❌ NOT ENOUGH DATA"
    elif safe_needed > safe_pool:
        status = "⚠️ Limited safe examples"
    else:
        status = "✅ Ready"
    
    print(f"{cat:<15} | {toxic_count:>8} | {safe_needed:>12} | {status}")

# 7. Summary and recommendations
print("\n" + "=" * 70)
print("📋 SUMMARY & RECOMMENDATIONS")
print("=" * 70)

issues = []
if len(categories.get("dangerous", [])) < 500:
    issues.append("• DANGEROUS: Only 74 examples. Need 5000+ for good model.")
if len(categories.get("self_harm", [])) < 500:
    issues.append("• SELF_HARM: Only 12 examples. Need 5000+ for good model.")
if len(categories.get("hindi_abuse", [])) < 500:
    issues.append("• HINDI_ABUSE: Only 234 examples. Need 5000+ for good model.")

if issues:
    print("\n❌ CRITICAL ISSUES:")
    for issue in issues:
        print(f"   {issue}")

print("\n✅ READY FOR TRAINING:")
ready = [cat for cat in categories if len(categories[cat]) >= 2000]
for cat in ready:
    print(f"   • {cat}: {len(categories[cat])} examples")

print("\n📌 RECOMMENDED ACTIONS:")
print("   1. Augment DANGEROUS with more examples (weapon/drug/hacking)")
print("   2. Augment SELF_HARM with more examples")
print("   3. Augment HINDI_ABUSE with more Hindi slurs")
print("   4. Consider merging small categories into HARASSMENT")
print("   5. Or use rule-based detection for small categories")
