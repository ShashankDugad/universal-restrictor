"""
Download more data - try different datasets that actually exist.
"""
import json
import os
from datasets import load_dataset

OUTPUT_DIR = "data/datasets/moe_augment"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("DOWNLOADING DATA FOR WEAK CATEGORIES - V2")
print("=" * 60)

# 1. SELF-HARM datasets
print("\n📌 1. SELF-HARM DATASETS")
print("-" * 60)

# Try different suicide/mental health datasets
datasets_to_try = [
    ("goemotion", "emotions", "train"),
    ("sem_eval_2018_task_1", "subtask5.english", "train"),
]

print("\n1a. GoEmotions (filter for sadness/fear)...")
try:
    goemotions = load_dataset("google-research-datasets/go_emotions", "simplified", split="train")
    with open(f"{OUTPUT_DIR}/self_harm_emotions.jsonl", "w") as f:
        count = 0
        for row in goemotions:
            text = row.get("text", "")
            labels = row.get("labels", [])
            # Labels: 0=admiration, 1=amusement, 2=anger, 3=annoyance, 4=approval, 5=caring,
            # 6=confusion, 7=curiosity, 8=desire, 9=disappointment, 10=disapproval,
            # 11=disgust, 12=embarrassment, 13=excitement, 14=fear, 15=gratitude,
            # 16=grief, 17=joy, 18=love, 19=nervousness, 20=optimism, 21=pride,
            # 22=realization, 23=relief, 24=remorse, 25=sadness, 26=surprise, 27=neutral
            # Look for grief(16), fear(14), sadness(25)
            if any(l in [14, 16, 25] for l in labels):
                f.write(json.dumps({"text": text, "label": "toxic", "category": "self_harm", "source": "goemotions"}) + "\n")
                count += 1
    print(f"   ✅ Saved {count} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Generate self-harm examples
print("\n1b. Generating self-harm examples...")
self_harm_templates = [
    # Suicidal ideation
    "I want to kill myself",
    "I want to end my life",
    "I don't want to live anymore",
    "I wish I was dead",
    "I'm thinking about suicide",
    "life is not worth living",
    "nobody would miss me",
    "the world would be better without me",
    "I can't take this anymore",
    "I want to disappear forever",
    "I just want the pain to stop",
    "there's no point in living",
    "I've been planning my suicide",
    "I wrote a suicide note",
    "what's the easiest way to die",
    "painless ways to end it",
    "how many pills to overdose",
    "I'm going to jump off a bridge",
    "I bought pills to kill myself",
    "this is my last message",
    "goodbye everyone",
    "I've decided to end it",
    # Self-harm
    "I cut myself",
    "I want to hurt myself",
    "I started cutting again",
    "I burn myself to feel something",
    "self harm helps me cope",
    "I hit myself when I'm angry",
    "I deserve to be hurt",
    "I like the pain",
    "my scars remind me",
    # Encouraging self-harm
    "you should kill yourself",
    "go kill yourself",
    "kys",
    "just end it already",
    "do the world a favor and die",
    "nobody wants you alive",
    "you're better off dead",
]

# Add variations
variations = []
for text in self_harm_templates:
    variations.append(text)
    variations.append(text.lower())
    variations.append(text.upper())
    variations.append(text.replace("I", "i"))
    variations.append(text + "...")
    variations.append(text + " please help")
    variations.append("I think " + text.lower())
    variations.append("honestly " + text.lower())

with open(f"{OUTPUT_DIR}/self_harm_generated.jsonl", "w") as f:
    count = 0
    seen = set()
    for text in variations:
        if text.lower() not in seen:
            seen.add(text.lower())
            f.write(json.dumps({"text": text, "label": "toxic", "category": "self_harm", "source": "generated"}) + "\n")
            count += 1
print(f"   ✅ Generated {count} self-harm examples")

# 2. Try more Hindi datasets
print("\n📌 2. MORE HINDI DATASETS")
print("-" * 60)

print("\n2a. IndicNLP Hindi...")
try:
    # Try IndicCorp or similar
    indic = load_dataset("ai4bharat/IndicSentiment", "hi", split="test")
    with open(f"{OUTPUT_DIR}/indic_hindi.jsonl", "w") as f:
        count = 0
        for row in indic:
            text = row.get("INDIC REVIEW", row.get("text", ""))
            label = row.get("LABEL", "")
            if text and label == "Negative":
                f.write(json.dumps({"text": text, "label": "toxic", "category": "hindi_abuse", "source": "indic"}) + "\n")
                count += 1
                if count >= 2000:
                    break
    print(f"   ✅ Saved {count} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n2b. Hindi Discourse...")
try:
    hindi_disc = load_dataset("midas/hindi-discourse", split="train")
    with open(f"{OUTPUT_DIR}/hindi_discourse.jsonl", "w") as f:
        count = 0
        for row in hindi_disc:
            text = row.get("Sentence", "")
            # Just get Hindi text samples
            if text and len(text) > 10:
                f.write(json.dumps({"text": text, "label": "safe", "category": "safe", "source": "hindi_discourse"}) + "\n")
                count += 1
                if count >= 1000:
                    break
    print(f"   ✅ Saved {count} Hindi safe examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. More dangerous content from existing datasets
print("\n📌 3. MORE DANGEROUS CONTENT")
print("-" * 60)

print("\n3a. Filtering existing datasets for dangerous content...")
dangerous_keywords = [
    "bomb", "explosive", "weapon", "gun", "poison", "kill", "murder",
    "hack", "drug", "cocaine", "meth", "heroin", "kidnap", "trafficking"
]

# Check existing files
existing_files = [
    "data/datasets/hate_speech_offensive.jsonl",
    "data/datasets/toxic_spans.jsonl",
    "data/datasets/measuring_hate.jsonl",
]

dangerous_found = []
for filepath in existing_files:
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                for line in f:
                    d = json.loads(line)
                    text = d.get("text", d.get("tweet", "")).lower()
                    if any(kw in text for kw in dangerous_keywords):
                        dangerous_found.append({
                            "text": d.get("text", d.get("tweet", "")),
                            "label": "toxic",
                            "category": "dangerous",
                            "source": os.path.basename(filepath)
                        })
        except:
            pass

if dangerous_found:
    with open(f"{OUTPUT_DIR}/dangerous_filtered.jsonl", "w") as f:
        for ex in dangerous_found[:2000]:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(f"   ✅ Found {len(dangerous_found)} dangerous examples from existing data")
else:
    print(f"   ⚠️ No dangerous content found in existing files")

# 4. Summary
print("\n" + "=" * 60)
print("DOWNLOAD COMPLETE - SUMMARY")
print("=" * 60)

total = 0
for filename in sorted(os.listdir(OUTPUT_DIR)):
    filepath = f"{OUTPUT_DIR}/{filename}"
    with open(filepath, "r") as f:
        count = sum(1 for _ in f)
    print(f"   {filename}: {count} examples")
    total += count

print(f"\n   TOTAL NEW EXAMPLES: {total}")
