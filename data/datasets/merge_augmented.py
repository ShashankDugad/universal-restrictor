"""
Merge augmented data with original MoE data.
"""
import json
import os
from collections import defaultdict

MOE_DIR = "data/datasets/moe"
AUGMENT_DIR = "data/datasets/moe_augment"

print("=" * 60)
print("MERGING AUGMENTED DATA")
print("=" * 60)

# Load original MoE data
categories = defaultdict(list)
for filename in os.listdir(MOE_DIR):
    if filename.endswith(".jsonl") and filename != "router_train.jsonl":
        cat = filename.replace(".jsonl", "")
        with open(f"{MOE_DIR}/{filename}", "r") as f:
            for line in f:
                categories[cat].append(json.loads(line))

print("\nOriginal counts:")
for cat in sorted(categories.keys()):
    print(f"   {cat}: {len(categories[cat])}")

# Load and merge augmented data
print("\nMerging augmented data...")
for filename in os.listdir(AUGMENT_DIR):
    if filename.endswith(".jsonl"):
        with open(f"{AUGMENT_DIR}/{filename}", "r") as f:
            for line in f:
                d = json.loads(line)
                cat = d.get("category", "harassment")
                categories[cat].append(d)
        print(f"   Merged {filename}")

# Deduplicate per category
print("\nDeduplicating...")
for cat in categories:
    seen = set()
    unique = []
    for ex in categories[cat]:
        text_lower = ex["text"].lower().strip()
        if text_lower and len(text_lower) > 3 and text_lower not in seen:
            seen.add(text_lower)
            unique.append(ex)
    categories[cat] = unique

# Save updated category files
print("\nSaving updated category files...")
for cat, examples in categories.items():
    output_file = f"{MOE_DIR}/{cat}.jsonl"
    with open(output_file, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(f"   {cat}: {len(examples)} examples")

# Recreate router training data
print("\nRecreating router training data...")
router_data = []
for cat, examples in categories.items():
    for ex in examples:
        router_data.append({
            "text": ex["text"],
            "label": cat
        })

router_file = f"{MOE_DIR}/router_train.jsonl"
with open(router_file, "w") as f:
    for ex in router_data:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"   Router: {len(router_data)} examples")

# Summary
print("\n" + "=" * 60)
print("FINAL CATEGORY COUNTS")
print("=" * 60)
print(f"{'Category':<15} | {'Count':>8} | Status")
print("-" * 45)
for cat in sorted(categories.keys(), key=lambda x: len(categories[x]), reverse=True):
    count = len(categories[cat])
    if count >= 2000:
        status = "✅ Ready"
    elif count >= 500:
        status = "⚠️ OK (marginal)"
    else:
        status = "❌ Still low"
    print(f"{cat:<15} | {count:>8} | {status}")
