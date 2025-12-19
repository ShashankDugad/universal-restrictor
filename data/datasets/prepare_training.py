"""
Prepare unified training dataset from downloaded sources.
"""
import json
import os

OUTPUT_DIR = "data/datasets"
TRAIN_FILE = f"{OUTPUT_DIR}/train_unified.jsonl"

unified_data = []

# 1. Process Tweet Hate
print("Processing Tweet Hate...")
with open(f"{OUTPUT_DIR}/tweet_hate.jsonl", "r") as f:
    for line in f:
        item = json.loads(line)
        unified_data.append({
            "text": item.get("text", ""),
            "label": "toxic" if item.get("label", 0) == 1 else "safe",
            "category": "hate_speech",
            "source": "tweet_hate"
        })
print(f"  Added {len(unified_data)} examples")

# 2. Process Tweet Offensive
print("Processing Tweet Offensive...")
count_before = len(unified_data)
with open(f"{OUTPUT_DIR}/tweet_offensive.jsonl", "r") as f:
    for line in f:
        item = json.loads(line)
        unified_data.append({
            "text": item.get("text", ""),
            "label": "toxic" if item.get("label", 0) == 1 else "safe",
            "category": "offensive",
            "source": "tweet_offensive"
        })
print(f"  Added {len(unified_data) - count_before} examples")

# 3. Process Toxic Conversations
print("Processing Toxic Conversations...")
count_before = len(unified_data)
with open(f"{OUTPUT_DIR}/toxic_conversations.jsonl", "r") as f:
    for line in f:
        item = json.loads(line)
        unified_data.append({
            "text": item.get("text", ""),
            "label": "toxic" if item.get("label", 0) == 1 else "safe",
            "category": "toxic",
            "source": "toxic_conversations"
        })
print(f"  Added {len(unified_data) - count_before} examples")

# 4. Process Civil Comments
print("Processing Civil Comments...")
count_before = len(unified_data)
with open(f"{OUTPUT_DIR}/civil_comments.jsonl", "r") as f:
    for line in f:
        item = json.loads(line)
        toxicity = item.get("toxicity", 0)
        unified_data.append({
            "text": item.get("text", ""),
            "label": "toxic" if toxicity > 0.5 else "safe",
            "category": "civil_toxic" if toxicity > 0.5 else "civil_safe",
            "source": "civil_comments"
        })
print(f"  Added {len(unified_data) - count_before} examples")

# Save unified dataset
print(f"\nSaving {len(unified_data)} total examples...")
with open(TRAIN_FILE, "w") as f:
    for item in unified_data:
        f.write(json.dumps(item) + "\n")

# Stats
toxic_count = sum(1 for d in unified_data if d["label"] == "toxic")
safe_count = sum(1 for d in unified_data if d["label"] == "safe")

print(f"\n{'='*50}")
print(f"Unified dataset created: {TRAIN_FILE}")
print(f"{'='*50}")
print(f"Total examples: {len(unified_data)}")
print(f"Toxic: {toxic_count} ({100*toxic_count/len(unified_data):.1f}%)")
print(f"Safe: {safe_count} ({100*safe_count/len(unified_data):.1f}%)")
