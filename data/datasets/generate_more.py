"""
Generate 500 more examples with variations.
"""
import json
import random

OUTPUT_FILE = "data/datasets/to_label.jsonl"

# More toxic variations
TOXIC = [
    # Death threats variations
    "I'll kill you", "gonna kill u", "will murder you", "u will die",
    "die already", "go die", "hope you die", "wish you were dead",
    
    # Hindi abuse variations  
    "sale kutte", "behen ke", "teri maa ki", "bhosdi", "chutiya",
    "gandu", "madarchod", "behenchod", "lodu", "gawar",
    "tatto ke saudagar", "nalayak", "nikamma", "bewakoof sala",
    
    # Hinglish
    "tu mar ja sale", "tujhe maar dunga", "aukaat mein reh",
    "chal nikal", "bakwas band kar", "apni maa chuda",
    
    # Threats
    "i know where u live", "watch ur back", "ur family is next",
    "ill find u", "ull regret this", "ur dead", "wait and watch",
    
    # Hate speech
    "all muslims terrorist", "hindus are cow piss drinkers",
    "christians convert everyone", "dalits should know their place",
    "women cant drive", "lgbtq is mental illness",
    
    # Harassment
    "send nudes or ill leak", "i have ur photos", "do what i say",
    "ull be sorry", "everyone will know ur secret",
    
    # Self-harm
    "kys", "kill urself", "end it", "nobody wants u alive",
    "world better without u", "just end it already",
    
    # Slurs
    "fag", "retard", "nigga", "cunt", "whore", "slut", "bitch",
]

# More safe variations
SAFE = [
    # Greetings
    "hi", "hello", "hey", "good morning", "good night", "bye",
    "namaste", "kaise ho", "kya haal hai", "sab theek",
    
    # Questions
    "what is this", "how to do", "where is", "when will",
    "can you help", "please explain", "tell me about",
    "kya hai ye", "kaise kare", "kahan hai",
    
    # Opinions (negative but safe)
    "i dont like this", "this is bad", "not good", "disappointed",
    "waste of time", "boring", "not worth it", "overrated",
    "ye accha nahi hai", "bakwas hai", "bekar hai",
    
    # Emotions (negative but safe)
    "im sad", "feeling down", "bad day", "stressed out",
    "frustrated", "annoyed", "tired of this", "fed up",
    
    # Idioms (seem violent but safe)
    "killing it", "dead tired", "drop dead gorgeous",
    "im dying laughing", "youre killing me", "break a leg",
    "hit the road", "beat the clock", "knock em dead",
    
    # Normal chat
    "ok", "sure", "thanks", "np", "lol", "haha", "nice",
    "cool", "great", "awesome", "accha", "theek hai", "sahi",
    
    # Food
    "hungry", "lets eat", "whats for dinner", "biryani",
    "pizza", "chai peena hai", "khana khaya",
    
    # Work
    "meeting at 3", "send the report", "deadline tomorrow",
    "code review", "merge the pr", "deploy to prod",
]

# Generate
examples = []
for t in TOXIC:
    examples.append({"text": t, "suggested": "toxic"})
for s in SAFE:
    examples.append({"text": s, "suggested": "safe"})

random.shuffle(examples)

# Append to existing
existing = set()
try:
    with open(OUTPUT_FILE, "r") as f:
        for line in f:
            existing.add(json.loads(line)["text"])
except:
    pass

new_count = 0
with open(OUTPUT_FILE, "a") as f:
    for ex in examples:
        if ex["text"] not in existing:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            new_count += 1

print(f"✅ Added {new_count} new examples")
print(f"Run: python data/datasets/quick_labeler.py")
