"""
Combine custom labels with original dataset and balance classes.
"""
import json
import random

ORIGINAL = "data/datasets/train_unified.jsonl"
CUSTOM = "data/datasets/custom_labeled.jsonl"
OUTPUT = "data/datasets/train_balanced.jsonl"

# Load original
original = []
with open(ORIGINAL, "r") as f:
    for line in f:
        original.append(json.loads(line))

# Load custom
custom = []
with open(CUSTOM, "r") as f:
    for line in f:
        custom.append(json.loads(line))

print(f"Original dataset: {len(original)}")
print(f"Custom labeled: {len(custom)}")

# Separate by class
toxic_orig = [d for d in original if d["label"] == "toxic"]
safe_orig = [d for d in original if d["label"] == "safe"]
toxic_custom = [d for d in custom if d["label"] == "toxic"]
safe_custom = [d for d in custom if d["label"] == "safe"]

print(f"\nOriginal - Toxic: {len(toxic_orig)}, Safe: {len(safe_orig)}")
print(f"Custom - Toxic: {len(toxic_custom)}, Safe: {len(safe_custom)}")

# Combine
all_toxic = toxic_orig + toxic_custom
all_safe = safe_orig + safe_custom

print(f"\nCombined - Toxic: {len(all_toxic)}, Safe: {len(all_safe)}")

# Balance: undersample safe to match toxic ratio better
# Target: 60% safe, 40% toxic (better than 85/15)
target_safe = int(len(all_toxic) * 1.5)  # 1.5x toxic count
if target_safe < len(all_safe):
    all_safe = random.sample(all_safe, target_safe)

print(f"Balanced - Toxic: {len(all_toxic)}, Safe: {len(all_safe)}")

# Combine and shuffle
final = all_toxic + all_safe
random.shuffle(final)

# Save
with open(OUTPUT, "w") as f:
    for d in final:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")

toxic_pct = 100 * len(all_toxic) / len(final)
safe_pct = 100 * len(all_safe) / len(final)

print(f"\n{'='*50}")
print(f"Saved: {OUTPUT}")
print(f"Total: {len(final)} examples")
print(f"Toxic: {len(all_toxic)} ({toxic_pct:.1f}%)")
print(f"Safe: {len(all_safe)} ({safe_pct:.1f}%)")
print(f"{'='*50}")
