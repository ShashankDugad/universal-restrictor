"""
Prepare comprehensive training dataset from all sources.
"""
import json
import os
import random

OUTPUT_DIR = "data/datasets"
FINAL_OUTPUT = f"{OUTPUT_DIR}/train_comprehensive.jsonl"

all_examples = []

print("=" * 60)
print("Preparing Comprehensive Training Dataset")
print("=" * 60)

# 1. Load existing unified data
print("\n1. Loading existing unified data...")
try:
    with open(f"{OUTPUT_DIR}/train_unified.jsonl", "r") as f:
        for line in f:
            d = json.loads(line)
            all_examples.append({
                "text": d.get("text", ""),
                "label": d.get("label", "safe"),
                "source": "original"
            })
    print(f"   ✅ Loaded {len(all_examples)} from train_unified.jsonl")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. HateCheck - labeled toxic examples
print("\n2. Processing HateCheck...")
try:
    count = 0
    with open(f"{OUTPUT_DIR}/hatecheck.jsonl", "r") as f:
        for line in f:
            d = json.loads(line)
            # HateCheck has 'label_gold' field
            label = "toxic" if d.get("label_gold") == "hateful" else "safe"
            all_examples.append({
                "text": d.get("test_case", ""),
                "label": label,
                "source": "hatecheck"
            })
            count += 1
    print(f"   ✅ Added {count} from HateCheck")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Multilingual Hate Speech
print("\n3. Processing Multilingual Hate Speech...")
try:
    count = 0
    with open(f"{OUTPUT_DIR}/multi_hate.jsonl", "r") as f:
        for line in f:
            d = json.loads(line)
            # Has 'label' field
            label = "toxic" if d.get("label", 0) == 1 else "safe"
            text = d.get("tweet", d.get("text", ""))
            if text:
                all_examples.append({
                    "text": text,
                    "label": label,
                    "source": "multi_hate"
                })
                count += 1
    print(f"   ✅ Added {count} from Multilingual Hate")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. Toxic Spans
print("\n4. Processing Toxic Spans...")
try:
    count = 0
    with open(f"{OUTPUT_DIR}/toxic_spans.jsonl", "r") as f:
        for line in f:
            d = json.loads(line)
            label = "toxic" if d.get("label", 0) == 1 else "safe"
            text = d.get("text", "")
            if text:
                all_examples.append({
                    "text": text,
                    "label": label,
                    "source": "toxic_spans"
                })
                count += 1
    print(f"   ✅ Added {count} from Toxic Spans")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 5. Hate Speech Offensive
print("\n5. Processing Hate Speech Offensive...")
try:
    count = 0
    with open(f"{OUTPUT_DIR}/hate_speech_offensive.jsonl", "r") as f:
        for line in f:
            d = json.loads(line)
            # class: 0=hate speech, 1=offensive, 2=neither
            cls = d.get("class", 2)
            label = "toxic" if cls in [0, 1] else "safe"
            text = d.get("tweet", "")
            if text:
                all_examples.append({
                    "text": text,
                    "label": label,
                    "source": "hate_speech_offensive"
                })
                count += 1
    print(f"   ✅ Added {count} from Hate Speech Offensive")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 6. Implicit Hate
print("\n6. Processing Implicit Hate...")
try:
    count = 0
    with open(f"{OUTPUT_DIR}/implicit_hate.jsonl", "r") as f:
        for line in f:
            d = json.loads(line)
            # implicit_class: explicit_hate, implicit_hate, not_hate
            cls = d.get("implicit_class", "not_hate")
            label = "toxic" if cls in ["explicit_hate", "implicit_hate"] else "safe"
            text = d.get("post", "")
            if text:
                all_examples.append({
                    "text": text,
                    "label": label,
                    "source": "implicit_hate"
                })
                count += 1
    print(f"   ✅ Added {count} from Implicit Hate")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 7. ToxiGen
print("\n7. Processing ToxiGen...")
try:
    count = 0
    with open(f"{OUTPUT_DIR}/toxigen.jsonl", "r") as f:
        for line in f:
            d = json.loads(line)
            # toxicity_ai or toxicity_human > 0.5 = toxic
            tox = max(d.get("toxicity_ai", 0), d.get("toxicity_human", 0))
            label = "toxic" if tox > 0.5 else "safe"
            text = d.get("text", "")
            if text:
                all_examples.append({
                    "text": text,
                    "label": label,
                    "source": "toxigen"
                })
                count += 1
    print(f"   ✅ Added {count} from ToxiGen")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 8. Measuring Hate Speech
print("\n8. Processing Measuring Hate Speech...")
try:
    count = 0
    with open(f"{OUTPUT_DIR}/measuring_hate.jsonl", "r") as f:
        for line in f:
            d = json.loads(line)
            # hate_speech_score > 0.5 = toxic
            score = d.get("hate_speech_score", 0)
            label = "toxic" if score > 0.5 else "safe"
            text = d.get("text", "")
            if text:
                all_examples.append({
                    "text": text,
                    "label": label,
                    "source": "measuring_hate"
                })
                count += 1
    print(f"   ✅ Added {count} from Measuring Hate Speech")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 9. OLID Offensive
print("\n9. Processing OLID Offensive...")
try:
    count = 0
    with open(f"{OUTPUT_DIR}/olid_offensive.jsonl", "r") as f:
        for line in f:
            d = json.loads(line)
            label = "toxic" if d.get("label", 0) == 1 else "safe"
            text = d.get("text", "")
            if text:
                all_examples.append({
                    "text": text,
                    "label": label,
                    "source": "olid_offensive"
                })
                count += 1
    print(f"   ✅ Added {count} from OLID Offensive")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 10. Add Hindi/Hinglish slurs manually
print("\n10. Adding Hindi/Hinglish slurs...")
hindi_toxic = [
    # MC/BC and variations
    "madarchod", "madarc hod", "mc sala", "motherchod", "maderchod",
    "bhenchod", "behen chod", "bc", "behenchod sala", "benchod",
    "tu mc hai", "sala mc", "bloody madarchod", "fucking bhenchod",
    # Vulgar
    "chutiya", "chutiye", "choot", "chu tiya", "chutiyapa",
    "gandu", "gaandu", "gaand", "gaand mara", "gaand me danda",
    "lodu", "loda", "lauda", "l0de", "lavde",
    "bhosdi ke", "bhosdike", "bsdk", "bhosadpappu",
    "tatto", "tatte", "tattey",
    # Other slurs
    "randi", "randwa", "randi ka bachcha", "randi ki aulad",
    "harami", "haramkhor", "haram zada", "harami sala",
    "kutte", "kutta", "kuttiya", "kutte ki aulad", "kameene",
    "saala", "saale", "sala kamina", "kamina",
    # Phrases
    "teri maa ki", "teri ma ki", "tmkc", "teri maa ka",
    "teri behen ki", "tbkc",
    "chod de", "chod dunga", "chod diya",
    "muh me le", "nikal lawde", "bhaag yahan se",
    # Threats
    "tujhe maar dunga", "teri gaand tod dunga", "tujhe dekh lunga",
    "bahar mil", "aukaat mein reh", "aukat dekh apni",
    "mar ja", "mar jayega", "marna chahta hai",
    # More variations
    "chup kar kutte", "bhag bhosdk", "abe sale", "oye kamne",
    "nalayak", "nikamma", "bevakoof", "gadha", "ullu",
]

hindi_safe = [
    "namaste", "kaise ho", "aap kaise hain", "bahut accha", "theek hai",
    "dhanyavaad", "shukriya", "kya haal hai", "maza aa gaya",
    "khana khaya", "chai peeni hai", "ghar ja raha hoon", "office mein hoon",
    "kal milte hain", "phir milenge", "movie dekhni hai", "cricket match",
    "bohot badiya", "ekdum mast", "aaj mausam accha hai", "barish ho rahi",
    "mere paas time nahi hai", "busy hoon", "bhai kya kar raha hai",
    "dost kahan hai", "achha", "sahi hai", "thik thak", "chalo theek hai",
]

for text in hindi_toxic:
    all_examples.append({"text": text, "label": "toxic", "source": "hindi_manual"})
    all_examples.append({"text": text.upper(), "label": "toxic", "source": "hindi_manual"})

for text in hindi_safe:
    all_examples.append({"text": text, "label": "safe", "source": "hindi_manual"})

print(f"   ✅ Added {len(hindi_toxic)*2 + len(hindi_safe)} Hindi examples")

# 11. Add dangerous content manually
print("\n11. Adding dangerous content...")
dangerous = [
    "how to make a bomb", "how to make an explosive device", "build a bomb at home",
    "homemade explosive recipe", "make explosives", "bomb making instructions",
    "how to make poison", "how to make ricin", "how to make sarin gas",
    "how to make cyanide", "poisoning someone", "untraceable poison",
    "how to make meth", "cook meth at home", "methamphetamine synthesis",
    "how to make drugs", "drug manufacturing", "cocaine production",
    "how to make a gun", "3d print gun", "ghost gun", "untraceable weapon",
    "how to hack bank account", "steal credit card", "ddos attack tutorial",
    "sql injection tutorial", "hack into systems", "bypass security",
    "how to kidnap someone", "human trafficking", "child exploitation",
    "how to stalk someone", "doxxing tutorial", "find someone address",
    "biological weapon", "anthrax", "nerve agent", "chemical weapon",
    "mass shooting plan", "school shooting", "terrorist attack",
    "how to kill someone", "murder methods", "get away with murder",
    "hire hitman", "contract killer", "assassination",
]

for text in dangerous:
    all_examples.append({"text": text, "label": "toxic", "source": "dangerous_manual"})
    all_examples.append({"text": text.title(), "label": "toxic", "source": "dangerous_manual"})

print(f"   ✅ Added {len(dangerous)*2} dangerous content examples")

# 12. Deduplicate
print("\n12. Deduplicating...")
seen = set()
unique = []
for ex in all_examples:
    text_lower = ex["text"].lower().strip()
    if text_lower and text_lower not in seen:
        seen.add(text_lower)
        unique.append(ex)

print(f"   Before: {len(all_examples)}, After: {len(unique)}")

# 13. Balance classes
print("\n13. Balancing classes...")
toxic_examples = [e for e in unique if e["label"] == "toxic"]
safe_examples = [e for e in unique if e["label"] == "safe"]

print(f"   Toxic: {len(toxic_examples)}, Safe: {len(safe_examples)}")

# Target: 40% toxic, 60% safe
target_safe = int(len(toxic_examples) * 1.5)
if len(safe_examples) > target_safe:
    safe_examples = random.sample(safe_examples, target_safe)

final_examples = toxic_examples + safe_examples
random.shuffle(final_examples)

print(f"   Final Toxic: {len(toxic_examples)}, Safe: {len(safe_examples)}")

# 14. Save
print("\n14. Saving...")
with open(FINAL_OUTPUT, "w") as f:
    for ex in final_examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

toxic_count = sum(1 for e in final_examples if e["label"] == "toxic")
safe_count = sum(1 for e in final_examples if e["label"] == "safe")

print(f"\n{'='*60}")
print(f"FINAL DATASET: {FINAL_OUTPUT}")
print(f"{'='*60}")
print(f"Total examples: {len(final_examples)}")
print(f"Toxic: {toxic_count} ({100*toxic_count/len(final_examples):.1f}%)")
print(f"Safe: {safe_count} ({100*safe_count/len(final_examples):.1f}%)")
print(f"{'='*60}")
