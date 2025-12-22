"""
Split dataset into categories for MoE training.
"""
import json
import re
from collections import defaultdict

INPUT_FILE = "data/datasets/train_comprehensive.jsonl"
OUTPUT_DIR = "data/datasets/moe"

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load all data
data = []
with open(INPUT_FILE, "r") as f:
    for line in f:
        data.append(json.loads(line))

print(f"Loaded {len(data)} examples")

# Category detection patterns
CATEGORY_PATTERNS = {
    "violence": [
        r"(?i)(kill|murder|shoot|stab|hurt|beat|attack|die|death|bomb|explosive|weapon|gun)",
        r"(?i)(i will|gonna|going to).*(kill|hurt|shoot|stab|murder)",
        r"(?i)(threat|violence|assault|massacre|slaughter)",
    ],
    "hate_speech": [
        r"(?i)(hate all|kill all|exterminate|subhuman|inferior race|master race)",
        r"(?i)(go back to your country|your kind|people like you)",
        r"(?i)(nigger|nigga|faggot|fag\b|dyke|tranny|retard)",
        r"(?i)(racist|sexist|homophobic|islamophobic|antisemitic)",
    ],
    "harassment": [
        r"(?i)(worthless|pathetic|loser|ugly|stupid|idiot|moron|dumb)",
        r"(?i)(you are (a |an )?(piece of|worthless|pathetic|stupid))",
        r"(?i)(nobody likes you|everyone hates you|kill yourself|kys)",
        r"(?i)(stalk|harass|bully|intimidate|threaten)",
    ],
    "hindi_abuse": [
        r"(?i)(madarchod|bhenchod|chutiya|gandu|randi|harami|kutt[ae]|sala[ae]?|bhosdi|lodu|lauda|tatt[eo])",
        r"(?i)(teri maa|teri behen|tmkc|bsdk|mc\b|bc\b)",
        r"(?i)(chod|gaand|muh me le)",
    ],
    "dangerous": [
        r"(?i)(how to (make|build|create).*(bomb|explosive|weapon|gun|poison|drug|meth))",
        r"(?i)(hack|ddos|sql injection|exploit|malware|ransomware)",
        r"(?i)(kidnap|trafficking|child.*exploit)",
        r"(?i)(ricin|sarin|anthrax|cyanide|nerve agent)",
    ],
    "sexual": [
        r"(?i)(porn|nude|naked|sex|rape|molest|fuck\b|fucking|dick|cock|pussy|tits|boobs)",
        r"(?i)(send nudes|sexual|erotic|orgasm)",
    ],
    "self_harm": [
        r"(?i)(kill myself|suicide|end my life|want to die|cut myself|self.?harm)",
        r"(?i)(best way to die|painless death|how to commit suicide)",
        r"(?i)(nobody would miss me|better off dead|world without me)",
    ],
}

def categorize(text, label):
    """Assign category based on patterns."""
    if label == "safe":
        return "safe"
    
    text_lower = text.lower()
    
    # Check each category
    scores = {}
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                scores[category] = scores.get(category, 0) + 1
    
    if scores:
        # Return highest scoring category
        return max(scores, key=scores.get)
    
    # Default to harassment if toxic but no specific category
    return "harassment"

# Categorize all examples
categorized = defaultdict(list)
for d in data:
    category = categorize(d["text"], d["label"])
    categorized[category].append({
        "text": d["text"],
        "label": d["label"],
        "category": category,
        "source": d.get("source", "unknown")
    })

# Print stats
print("\n" + "=" * 60)
print("CATEGORY DISTRIBUTION")
print("=" * 60)
total_toxic = 0
for cat in sorted(categorized.keys()):
    count = len(categorized[cat])
    toxic_count = sum(1 for d in categorized[cat] if d["label"] == "toxic")
    safe_count = count - toxic_count
    if cat != "safe":
        total_toxic += toxic_count
    print(f"{cat:15} | Total: {count:6} | Toxic: {toxic_count:6} | Safe: {safe_count:6}")

# Save each category
print("\n" + "=" * 60)
print("SAVING CATEGORY FILES")
print("=" * 60)
for cat, examples in categorized.items():
    output_file = f"{OUTPUT_DIR}/{cat}.jsonl"
    with open(output_file, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(f"Saved {len(examples):6} examples to {output_file}")

# Create router training data (category classification)
print("\n" + "=" * 60)
print("CREATING ROUTER TRAINING DATA")
print("=" * 60)
router_data = []
for cat, examples in categorized.items():
    for ex in examples:
        router_data.append({
            "text": ex["text"],
            "label": cat,  # Category as label for router
        })

# Save router data
router_file = f"{OUTPUT_DIR}/router_train.jsonl"
with open(router_file, "w") as f:
    for ex in router_data:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")
print(f"Saved {len(router_data)} examples to {router_file}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Total examples: {len(data)}")
print(f"Categories: {len(categorized)}")
print(f"Router training examples: {len(router_data)}")
