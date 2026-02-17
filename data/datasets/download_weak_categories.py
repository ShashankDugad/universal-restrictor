"""
Download more data for weak categories: dangerous, self_harm, hindi_abuse
"""
import json
import os
from datasets import load_dataset

OUTPUT_DIR = "data/datasets/moe_augment"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("DOWNLOADING DATA FOR WEAK CATEGORIES")
print("=" * 60)

# 1. SELF-HARM / SUICIDE datasets
print("\n📌 1. SELF-HARM / SUICIDE DATASETS")
print("-" * 60)

# Reddit mental health
print("\n1a. Reddit Mental Health...")
try:
    reddit_mh = load_dataset("mrjunos/depression-reddit-cleaned", split="train")
    with open(f"{OUTPUT_DIR}/reddit_depression.jsonl", "w") as f:
        count = 0
        for row in reddit_mh:
            text = row.get("text", "")
            if text and len(text) > 20:
                f.write(json.dumps({"text": text, "label": "toxic", "category": "self_harm"}) + "\n")
                count += 1
                if count >= 5000:
                    break
    print(f"   ✅ Saved {count} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Suicide detection
print("\n1b. Suicide Detection Dataset...")
try:
    suicide = load_dataset("paulofinardi/suicide_watch", split="train")
    with open(f"{OUTPUT_DIR}/suicide_watch.jsonl", "w") as f:
        count = 0
        for row in suicide:
            text = row.get("text", "")
            label = row.get("label", 0)
            if text and label == 1:  # Suicidal
                f.write(json.dumps({"text": text[:500], "label": "toxic", "category": "self_harm"}) + "\n")
                count += 1
                if count >= 5000:
                    break
    print(f"   ✅ Saved {count} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. DANGEROUS CONTENT datasets
print("\n📌 2. DANGEROUS CONTENT DATASETS")
print("-" * 60)

# Generate more dangerous content examples
print("\n2a. Generating dangerous content variations...")
dangerous_templates = [
    # Weapons
    "how to make a {}", "how to build a {}", "instructions for making {}",
    "tutorial for building {}", "guide to create {}", "steps to make {}",
    "DIY {} at home", "homemade {} recipe", "easy {} instructions",
    # Actions
    "how to {} someone", "best way to {}", "methods to {}",
]

dangerous_items = [
    # Explosives
    "bomb", "explosive", "IED", "pipe bomb", "molotov cocktail",
    "detonator", "C4", "dynamite", "grenade", "landmine",
    # Weapons
    "gun", "rifle", "pistol", "silencer", "suppressor", "ghost gun",
    "3D printed gun", "untraceable weapon", "AR-15", "AK-47",
    # Drugs
    "meth", "methamphetamine", "cocaine", "heroin", "fentanyl",
    "LSD", "MDMA", "crack", "crystal meth", "drug lab",
    # Poisons
    "poison", "ricin", "cyanide", "arsenic", "nerve agent",
    "sarin gas", "VX gas", "anthrax", "botulinum toxin",
    # Hacking
    "hack bank account", "steal credit cards", "ransomware",
    "keylogger", "phishing kit", "exploit", "zero day",
    # Crimes
    "kidnap", "human trafficking", "child exploitation",
    "contract killer", "hitman", "assassination", "murder for hire",
]

dangerous_actions = [
    "kill", "murder", "poison", "kidnap", "hack", "attack",
    "stalk", "doxx", "blackmail", "extort", "traffic",
]

with open(f"{OUTPUT_DIR}/dangerous_generated.jsonl", "w") as f:
    count = 0
    for template in dangerous_templates:
        for item in dangerous_items:
            try:
                text = template.format(item)
                f.write(json.dumps({"text": text, "label": "toxic", "category": "dangerous"}) + "\n")
                count += 1
            except:
                pass
    
    for template in dangerous_templates:
        for action in dangerous_actions:
            try:
                text = template.format(action)
                f.write(json.dumps({"text": text, "label": "toxic", "category": "dangerous"}) + "\n")
                count += 1
            except:
                pass
    
    # Add contextual dangerous queries
    contextual = [
        "where can I buy illegal weapons",
        "how to get drugs delivered",
        "dark web marketplace for weapons",
        "hire someone to hurt my ex",
        "how to make someone disappear",
        "undetectable poisons",
        "how to avoid getting caught",
        "clean crime scene",
        "dispose of a body",
        "how to hack into government systems",
        "steal someone's identity",
        "create fake documents",
        "bypass security systems",
        "break into a house",
        "pick locks tutorial",
        "disable alarm systems",
        "make untraceable calls",
        "anonymous threats online",
        "swatting guide",
        "how to stalk someone online",
        "find someone's home address",
        "track someone's location",
    ]
    for text in contextual:
        f.write(json.dumps({"text": text, "label": "toxic", "category": "dangerous"}) + "\n")
        count += 1

print(f"   ✅ Generated {count} dangerous examples")

# 3. HINDI ABUSE datasets
print("\n📌 3. HINDI ABUSE DATASETS")
print("-" * 60)

# Hindi Hate Speech
print("\n3a. Hindi Hate Speech Dataset...")
try:
    hindi_hate = load_dataset("Hate-speech-CNERG/hindi-abusive-hate-speech", split="train")
    with open(f"{OUTPUT_DIR}/hindi_hate.jsonl", "w") as f:
        count = 0
        for row in hindi_hate:
            text = row.get("text", "")
            label = row.get("label", 0)
            if text and label in [1, 2]:  # Abusive or hate
                f.write(json.dumps({"text": text, "label": "toxic", "category": "hindi_abuse"}) + "\n")
                count += 1
    print(f"   ✅ Saved {count} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# HASOC Hindi
print("\n3b. HASOC Hindi Dataset...")
try:
    hasoc = load_dataset("Hate-speech-CNERG/HASOC2019-hindi", split="train")
    with open(f"{OUTPUT_DIR}/hasoc_hindi.jsonl", "w") as f:
        count = 0
        for row in hasoc:
            text = row.get("text", "")
            label = row.get("task_1", "")
            if text and label == "HOF":  # Hate/Offensive
                f.write(json.dumps({"text": text, "label": "toxic", "category": "hindi_abuse"}) + "\n")
                count += 1
    print(f"   ✅ Saved {count} examples")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Generate more Hindi abuse
print("\n3c. Generating Hindi abuse variations...")
hindi_slurs = [
    # Base slurs
    "madarchod", "bhenchod", "chutiya", "gandu", "randi", "harami",
    "kutte", "kutta", "kuttiya", "saala", "saale", "kamina", "kameena",
    "bhosdi ke", "bhosdike", "lodu", "loda", "lauda", "tatti", "tatte",
    "ullu", "gadha", "bevakoof", "nalayak", "nikamma", "haramkhor",
    # Romanized variations
    "mc", "bc", "bsdk", "tmkc", "lund", "chut", "gaand",
    # Phrases
    "teri maa ki", "teri behen ki", "maa chuda", "bhag yahan se",
    "nikal lawde", "aukaat mein reh", "aukat dekh",
]

hindi_templates = [
    "{}", "tu {}", "abe {}", "oye {}", "sale {}",
    "{} sala", "{} saale", "bloody {}", "fucking {}",
    "you {}", "he is a {}", "she is a {}", "what a {}",
    "shut up {}", "get lost {}", "go away {}",
]

with open(f"{OUTPUT_DIR}/hindi_generated.jsonl", "w") as f:
    count = 0
    for slur in hindi_slurs:
        for template in hindi_templates:
            text = template.format(slur)
            f.write(json.dumps({"text": text, "label": "toxic", "category": "hindi_abuse"}) + "\n")
            count += 1
        # Also add uppercase
        f.write(json.dumps({"text": slur.upper(), "label": "toxic", "category": "hindi_abuse"}) + "\n")
        count += 1

print(f"   ✅ Generated {count} Hindi abuse examples")

# 4. Summary
print("\n" + "=" * 60)
print("DOWNLOAD COMPLETE - SUMMARY")
print("=" * 60)

for filename in os.listdir(OUTPUT_DIR):
    filepath = f"{OUTPUT_DIR}/{filename}"
    with open(filepath, "r") as f:
        count = sum(1 for _ in f)
    print(f"   {filename}: {count} examples")
