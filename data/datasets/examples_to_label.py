"""
Generate examples for quick labeling.
"""
import json
import random

OUTPUT_FILE = "data/datasets/to_label.jsonl"

# ============================================
# TOXIC EXAMPLES (you verify these)
# ============================================
TOXIC_TEMPLATES = [
    # Hindi abuse
    "तू मर जा साले",
    "तेरी माँ की ***",
    "भड़वे कहीं के",
    "कुत्ते कमीने",
    "हरामी साला",
    "चुप कर कुत्ते",
    "तुझे मार डालूंगा",
    "औकात में रह",
    "गंदी नाली के कीड़े",
    "जाके मर बेहंकार",
    
    # English threats
    "I will kill you",
    "I will find where you live",
    "You're dead meat",
    "Watch your back",
    "I'll destroy your family",
    "You will regret this",
    "I'm going to hurt you",
    "Your days are numbered",
    "I'll make you suffer",
    "You won't survive this",
    
    # Hate speech
    "All Muslims should die",
    "Hindus are terrorists",
    "Christians should leave India",
    "Dalits are subhuman",
    "Women belong in kitchen only",
    "Gay people are sick",
    "Pakistanis are all terrorists",
    "Bangladeshis should be shot",
    "Northeast people are Chinese",
    "South Indians are dark and ugly",
    
    # Subtle threats
    "I know where your kids go to school",
    "Nice family you have there",
    "Would be a shame if something happened",
    "Sleep with one eye open",
    "Karma will get you",
    
    # Cyberbullying
    "You're worthless",
    "Nobody loves you",
    "Kill yourself",
    "The world is better without you",
    "You're a waste of oxygen",
    "Your parents must be ashamed",
    "You'll never amount to anything",
    "Everyone hates you",
    "You're disgusting",
    "You deserve to suffer",
    
    # Harassment
    "Send me your photos or else",
    "I'll leak your pictures",
    "I have your personal info",
    "I'll tell everyone your secret",
    "Do what I say or face consequences",
]

# ============================================
# SAFE EXAMPLES (you verify these)
# ============================================
SAFE_TEMPLATES = [
    # Normal conversation
    "How are you doing today?",
    "Can you help me with this problem?",
    "What's the weather like?",
    "I love this movie",
    "The food was delicious",
    "Thank you for your help",
    "Have a great day",
    "See you tomorrow",
    "That's interesting",
    "I agree with you",
    
    # Hindi normal
    "आप कैसे हैं?",
    "आज मौसम अच्छा है",
    "खाना बहुत स्वादिष्ट था",
    "धन्यवाद आपकी मदद के लिए",
    "कल मिलते हैं",
    "यह बहुत अच्छा है",
    "मुझे यह पसंद आया",
    "क्या आप मेरी मदद कर सकते हैं?",
    
    # Questions
    "What is machine learning?",
    "How do I cook biryani?",
    "Where is the nearest hospital?",
    "What time does the train arrive?",
    "Can you explain this concept?",
    
    # Opinions (not toxic)
    "I don't like this policy",
    "The government should do better",
    "This movie was disappointing",
    "I disagree with this decision",
    "This could be improved",
    
    # Edge cases (seem negative but safe)
    "I'm feeling sad today",
    "This is frustrating",
    "I'm angry about this situation",
    "That was a terrible experience",
    "I hate waiting in lines",
    "This traffic is killing me",  # metaphor, not threat
    "I could eat a horse",  # idiom
    "Break a leg!",  # idiom
    "I'm dying of laughter",  # idiom
]

# Generate with variations
examples = []

for text in TOXIC_TEMPLATES:
    examples.append({"text": text, "suggested": "toxic"})

for text in SAFE_TEMPLATES:
    examples.append({"text": text, "suggested": "safe"})

# Shuffle
random.shuffle(examples)

# Save
with open(OUTPUT_FILE, "w") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"✅ Generated {len(examples)} examples to label")
print(f"   Saved to: {OUTPUT_FILE}")
print(f"\nNext: Run the quick labeler")
