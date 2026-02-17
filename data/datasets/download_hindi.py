"""
Download Hindi/Indian toxic content datasets.
"""
import os
from datasets import load_dataset

OUTPUT_DIR = "data/datasets"

print("=" * 50)
print("Downloading Hindi/Indian Toxic Datasets")
print("=" * 50)

# 1. HASOC 2019 - Hindi Hate Speech
print("\n1. HASOC Hindi Hate Speech...")
try:
    hasoc = load_dataset("Hate-speech-CNERG/hatexplain", split="train")
    hasoc.to_json(f"{OUTPUT_DIR}/hatexplain.jsonl")
    print(f"   ✅ Saved {len(hasoc)} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. Hindi Abuse Dataset
print("\n2. Hindi Abuse Dataset...")
try:
    hindi_abuse = load_dataset("cardiffnlp/tweet_topic_multi", split="train")
    # Filter for relevant content
    hindi_abuse.to_json(f"{OUTPUT_DIR}/hindi_abuse.jsonl")
    print(f"   ✅ Saved {len(hindi_abuse)} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. TRAC Aggression Dataset (Hindi-English)
print("\n3. TRAC Aggression (Hindi-English)...")
try:
    trac = load_dataset("strombergnlp/trac2020_aggression_detection", split="train")
    trac.to_json(f"{OUTPUT_DIR}/trac_aggression.jsonl")
    print(f"   ✅ Saved {len(trac)} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. Offensive Language Identification
print("\n4. Offensive Language (OLID)...")
try:
    olid = load_dataset("strombergnlp/offenseval_2020", "ar", split="train")
    olid.to_json(f"{OUTPUT_DIR}/olid.jsonl")
    print(f"   ✅ Saved {len(olid)} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 5. HateCheck - Functional Tests for Hate Speech
print("\n5. HateCheck...")
try:
    hatecheck = load_dataset("Paul/hatecheck", split="test")
    hatecheck.to_json(f"{OUTPUT_DIR}/hatecheck.jsonl")
    print(f"   ✅ Saved {len(hatecheck)} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 6. Multilingual Hate Speech
print("\n6. Multilingual Hate Speech...")
try:
    multi_hate = load_dataset("nedjmaou/MLMA_hate_speech", split="train")
    multi_hate.to_json(f"{OUTPUT_DIR}/multi_hate.jsonl")
    print(f"   ✅ Saved {len(multi_hate)} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 50)
print("Download complete!")
print("=" * 50)
