"""
Download free public datasets for content moderation.
"""
import os
from datasets import load_dataset

OUTPUT_DIR = "data/datasets"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 50)
print("Downloading Free Training Datasets")
print("=" * 50)

# 1. Tweet Eval - Hate Speech (English) - 10K examples
print("\n1. Downloading Tweet Eval Hate Speech...")
try:
    hate = load_dataset("cardiffnlp/tweet_eval", "hate", split="train")
    hate.to_json(f"{OUTPUT_DIR}/tweet_hate.jsonl")
    print(f"   ✅ Saved {len(hate)} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. Tweet Eval - Offensive (English) - 12K examples
print("\n2. Downloading Tweet Eval Offensive...")
try:
    offensive = load_dataset("cardiffnlp/tweet_eval", "offensive", split="train")
    offensive.to_json(f"{OUTPUT_DIR}/tweet_offensive.jsonl")
    print(f"   ✅ Saved {len(offensive)} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Toxic Conversations (English) - 50K examples
print("\n3. Downloading Toxic Conversations...")
try:
    toxic = load_dataset("SetFit/toxic_conversations", split="train[:20000]")
    toxic.to_json(f"{OUTPUT_DIR}/toxic_conversations.jsonl")
    print(f"   ✅ Saved {len(toxic)} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. Hate Speech 18 (English)
print("\n4. Downloading Hate Speech 18...")
try:
    hs18 = load_dataset("hate_speech18", split="train")
    hs18.to_json(f"{OUTPUT_DIR}/hate_speech18.jsonl")
    print(f"   ✅ Saved {len(hs18)} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 5. Civil Comments (English) - Large dataset
print("\n5. Downloading Civil Comments...")
try:
    civil = load_dataset("google/civil_comments", split="train[:30000]")
    civil.to_json(f"{OUTPUT_DIR}/civil_comments.jsonl")
    print(f"   ✅ Saved {len(civil)} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 50)
print("Download complete! Check data/datasets/")
print("=" * 50)
