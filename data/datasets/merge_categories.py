"""
Merge violence + dangerous into harmful_content.
"""
import json
import os

MOE_DIR = "data/datasets/moe"

print("=" * 60)
print("MERGING: violence + dangerous → harmful_content")
print("=" * 60)

# Load violence and dangerous
violence = []
dangerous = []

with open(f"{MOE_DIR}/violence.jsonl", "r") as f:
    for line in f:
        violence.append(json.loads(line))

with open(f"{MOE_DIR}/dangerous.jsonl", "r") as f:
    for line in f:
        dangerous.append(json.loads(line))

print(f"Violence: {len(violence)}")
print(f"Dangerous: {len(dangerous)}")

# Merge into harmful_content
harmful_content = []
seen = set()

for ex in violence + dangerous:
    text_lower = ex["text"].lower().strip()
    if text_lower not in seen:
        seen.add(text_lower)
        harmful_content.append({
            "text": ex["text"],
            "label": "toxic",
            "category": "harmful_content",
            "source": ex.get("source", "merged"),
            "original_category": ex.get("category", "unknown")
        })

print(f"Harmful content (merged): {len(harmful_content)}")

# Save harmful_content
with open(f"{MOE_DIR}/harmful_content.jsonl", "w") as f:
    for ex in harmful_content:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

# Recreate router_train.jsonl with new categories
print("\nRecreating router training data...")

categories_to_load = [
    "safe", "harassment", "hate_speech", "sexual", 
    "hindi_abuse", "self_harm", "harmful_content"
]

router_data = []
for cat in categories_to_load:
    filepath = f"{MOE_DIR}/{cat}.jsonl"
    with open(filepath, "r") as f:
        for line in f:
            ex = json.loads(line)
            router_data.append({
                "text": ex["text"],
                "label": cat
            })

# Save new router data
with open(f"{MOE_DIR}/router_train_v2.jsonl", "w") as f:
    for ex in router_data:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Router data: {len(router_data)} examples")

# Summary
print("\n" + "=" * 60)
print("NEW CATEGORY STRUCTURE")
print("=" * 60)
from collections import Counter
cat_counts = Counter(ex["label"] for ex in router_data)
for cat, count in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {cat:<20} | {count:>8}")

print(f"\n  Total: {len(router_data)}")
print(f"  Categories: {len(cat_counts)}")
