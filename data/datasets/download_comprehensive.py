"""
Download comprehensive toxic/hate speech datasets.
"""
import os
from datasets import load_dataset

OUTPUT_DIR = "data/datasets"

print("=" * 50)
print("Downloading Comprehensive Toxic Datasets")
print("=" * 50)

datasets_downloaded = []

# 1. HateCheck - 3728 examples (already downloaded)
print("\n1. HateCheck (functional tests)... ✅ Already have 3728")

# 2. Multilingual Hate Speech - 18661 examples (already downloaded)  
print("2. Multilingual Hate Speech... ✅ Already have 18661")

# 3. Jigsaw Multilingual Toxic
print("\n3. Jigsaw Multilingual Toxic...")
try:
    jigsaw = load_dataset("jigsaw-unintended-bias-in-toxicity", split="train[:30000]")
    jigsaw.to_json(f"{OUTPUT_DIR}/jigsaw_multi.jsonl")
    print(f"   ✅ Saved {len(jigsaw)} examples")
    datasets_downloaded.append(("jigsaw_multi", len(jigsaw)))
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. Toxic Spans Detection
print("\n4. Toxic Spans...")
try:
    toxic_spans = load_dataset("SetFit/toxic_conversations_50k", split="train[:20000]")
    toxic_spans.to_json(f"{OUTPUT_DIR}/toxic_spans.jsonl")
    print(f"   ✅ Saved {len(toxic_spans)} examples")
    datasets_downloaded.append(("toxic_spans", len(toxic_spans)))
except Exception as e:
    print(f"   ❌ Error: {e}")

# 5. Hate Speech Offensive
print("\n5. Hate Speech Offensive...")
try:
    hs_off = load_dataset("hate_speech_offensive", split="train")
    hs_off.to_json(f"{OUTPUT_DIR}/hate_speech_offensive.jsonl")
    print(f"   ✅ Saved {len(hs_off)} examples")
    datasets_downloaded.append(("hate_speech_offensive", len(hs_off)))
except Exception as e:
    print(f"   ❌ Error: {e}")

# 6. Ethos - Hate Speech Detection (multilingual)
print("\n6. Ethos Hate Speech...")
try:
    ethos = load_dataset("ethos", "binary", split="train")
    ethos.to_json(f"{OUTPUT_DIR}/ethos.jsonl")
    print(f"   ✅ Saved {len(ethos)} examples")
    datasets_downloaded.append(("ethos", len(ethos)))
except Exception as e:
    print(f"   ❌ Error: {e}")

# 7. Implicit Hate
print("\n7. Implicit Hate (subtle/veiled)...")
try:
    implicit = load_dataset("SALT-NLP/ImplicitHate", split="train")
    implicit.to_json(f"{OUTPUT_DIR}/implicit_hate.jsonl")
    print(f"   ✅ Saved {len(implicit)} examples")
    datasets_downloaded.append(("implicit_hate", len(implicit)))
except Exception as e:
    print(f"   ❌ Error: {e}")

# 8. ToxiGen - Machine Generated Toxic
print("\n8. ToxiGen (machine generated toxic)...")
try:
    toxigen = load_dataset("skg/toxigen-data", "train", split="train[:15000]")
    toxigen.to_json(f"{OUTPUT_DIR}/toxigen.jsonl")
    print(f"   ✅ Saved {len(toxigen)} examples")
    datasets_downloaded.append(("toxigen", len(toxigen)))
except Exception as e:
    print(f"   ❌ Error: {e}")

# 9. Social Bias Frames
print("\n9. Social Bias Frames...")
try:
    sbf = load_dataset("social_bias_frames", split="train[:20000]")
    sbf.to_json(f"{OUTPUT_DIR}/social_bias.jsonl")
    print(f"   ✅ Saved {len(sbf)} examples")
    datasets_downloaded.append(("social_bias", len(sbf)))
except Exception as e:
    print(f"   ❌ Error: {e}")

# 10. Measuring Hate Speech
print("\n10. Measuring Hate Speech...")
try:
    mhs = load_dataset("ucberkeley-dlab/measuring-hate-speech", split="train[:25000]")
    mhs.to_json(f"{OUTPUT_DIR}/measuring_hate.jsonl")
    print(f"   ✅ Saved {len(mhs)} examples")
    datasets_downloaded.append(("measuring_hate", len(mhs)))
except Exception as e:
    print(f"   ❌ Error: {e}")

# 11. OLID - Offensive Language
print("\n11. OLID Offensive Language...")
try:
    olid = load_dataset("cardiffnlp/tweet_eval", "offensive", split="train")
    olid.to_json(f"{OUTPUT_DIR}/olid_offensive.jsonl")
    print(f"   ✅ Saved {len(olid)} examples")
    datasets_downloaded.append(("olid_offensive", len(olid)))
except Exception as e:
    print(f"   ❌ Error: {e}")

# 12. Dangerous Content / Weapons
print("\n12. Dangerous Content Detection...")
try:
    # This might not exist, we'll generate our own
    print("   ⚠️ No public dataset - will generate manually")
except:
    pass

print("\n" + "=" * 50)
print("Summary")
print("=" * 50)
total = sum(d[1] for d in datasets_downloaded) + 3728 + 18661  # Add already downloaded
print(f"Total new examples: {total}")
for name, count in datasets_downloaded:
    print(f"   {name}: {count}")
