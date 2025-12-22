"""
Generate more Hindi abuse examples to reach 2000+
"""
import json

OUTPUT_FILE = "data/datasets/moe/hindi_abuse.jsonl"

# Load existing
existing = []
with open(OUTPUT_FILE, "r") as f:
    for line in f:
        existing.append(json.loads(line))

print(f"Existing: {len(existing)}")

# More comprehensive Hindi/Hinglish slurs
slurs = [
    # Core slurs
    "madarchod", "bhenchod", "chutiya", "gandu", "randi", "harami",
    "kutte", "kutta", "kuttiya", "saala", "saale", "kamina", "kameena",
    "bhosdi ke", "bhosdike", "lodu", "loda", "lauda", "tatti", "tatte",
    "ullu", "gadha", "bevakoof", "nalayak", "nikamma", "haramkhor",
    "chutiyapa", "bakchodi", "gand", "lund", "chut",
    # Abbreviations
    "mc", "bc", "bsdk", "tmkc", "bkl", "mkc", "bkc",
    # More slurs
    "hijra", "chakka", "raand", "dalla", "dallal", "suar", "suwar",
    "kutiya", "bhadwa", "bhadwe", "gawar", "jahil", "anpadh",
    "chirkut", "fattu", "namard", "meetha", "hijda",
]

templates = [
    "{}", "tu {}", "abe {}", "oye {}", "sale {}", "teri {}", "tere {}",
    "{} sala", "{} saale", "bloody {}", "fucking {}", "damn {}",
    "you {}", "he is {}", "she is {}", "what a {}", "such a {}",
    "shut up {}", "get lost {}", "go away {}", "go to hell {}",
    "die {}", "mar ja {}", "{} ki aulad", "{} ke bacche",
    "tu ek {}", "tu bada {}", "kitna {} hai", "pura {} hai",
    "abe {} nikal", "{} mat ban", "chal {} chal",
    "{} kahin ka", "{} insaan", "ekdum {}",
]

phrases = [
    "teri maa ki", "teri behen ki", "maa chuda", "behen chuda",
    "gaand mara", "gaand mein daal", "muh mein le", "nikal yahan se",
    "bhag yahan se", "chal bhag", "aukaat mein reh", "aukat dekh apni",
    "tujhe dekh lunga", "bahar mil", "tera khoon pee jaunga",
    "tujhe maar dunga", "tujhe chod dunga", "teri band baja dunga",
    "tera muh tod dunga", "tujhe jaan se maar dunga",
    "tu mar jayega", "tujhe nahi chodunga", "tera kaam tamam",
    "tera kaat dunga", "tujhe ukhaad dunga", "tujhe jalaa dunga",
    "tera sara khandan", "teri poori family", "tere baap ko",
    "apni maa chuda", "apni behen bhej", "apna kaam kar",
    "muh band kar", "bakwas band kar", "faltu bakwas",
    "chup kar kutte", "chup kar kuttiya", "kuch nahi hai tera",
    "aukaat nahi hai teri", "gutter mein ja", "naali ka keeda",
    "gandagi hai tu", "suar ki nasal", "kutte ki nasal",
]

# Generate combinations
seen = set(ex["text"].lower() for ex in existing)
new_examples = []

for slur in slurs:
    for template in templates:
        text = template.format(slur)
        if text.lower() not in seen:
            seen.add(text.lower())
            new_examples.append({"text": text, "label": "toxic", "category": "hindi_abuse", "source": "hindi_gen_v2"})

for phrase in phrases:
    if phrase.lower() not in seen:
        seen.add(phrase.lower())
        new_examples.append({"text": phrase, "label": "toxic", "category": "hindi_abuse", "source": "hindi_gen_v2"})
    # Variations
    for var in [phrase.upper(), phrase.title(), phrase + "!", phrase + " sala"]:
        if var.lower() not in seen:
            seen.add(var.lower())
            new_examples.append({"text": var, "label": "toxic", "category": "hindi_abuse", "source": "hindi_gen_v2"})

print(f"Generated: {len(new_examples)} new examples")

# Combine and save
all_examples = existing + new_examples
with open(OUTPUT_FILE, "w") as f:
    for ex in all_examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Total saved: {len(all_examples)}")
