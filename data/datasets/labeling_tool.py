"""
Simple labeling tool for creating training data.
Run: python data/datasets/labeling_tool.py
"""
import json
import os

OUTPUT_FILE = "data/datasets/custom_labeled.jsonl"

# Pre-made examples to speed up labeling
SEED_EXAMPLES = {
    "toxic": [
        # Hindi abuse (add more)
        "तू मर जा",
        "साले हरामी",
        "तेरी माँ की",
        "कुत्ते कमीने",
        "भड़वा साला",
        # English threats
        "I will find where you live",
        "You'll regret this",
        "Watch your back",
        "Your family will pay",
        "I know where you work",
        # Hate speech
        "All [group] should die",
        "They don't deserve to live",
        "Subhuman garbage",
        "Go back to your country",
        "You people are animals",
    ],
    "safe": [
        "How are you today?",
        "The weather is nice",
        "Can you help me with coding?",
        "What time is the meeting?",
        "I love this restaurant",
        "आज मौसम अच्छा है",
        "कैसे हो आप?",
        "खाना बहुत अच्छा था",
    ]
}

def load_existing():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            return [json.loads(l) for l in f]
    return []

def save_example(text, label, category="custom"):
    with open(OUTPUT_FILE, "a") as f:
        f.write(json.dumps({
            "text": text,
            "label": label,
            "category": category,
            "source": "manual"
        }) + "\n")

def main():
    existing = load_existing()
    print(f"\n{'='*50}")
    print(f"Custom Labeling Tool")
    print(f"{'='*50}")
    print(f"Existing labels: {len(existing)}")
    print(f"Target: 5,000")
    print(f"\nCommands:")
    print(f"  t = toxic")
    print(f"  s = safe")
    print(f"  skip = skip this example")
    print(f"  add = add your own example")
    print(f"  quit = save and exit")
    print(f"{'='*50}\n")
    
    count = len(existing)
    
    # First, label seed examples
    all_seeds = [(t, "toxic") for t in SEED_EXAMPLES["toxic"]] + \
                [(t, "safe") for t in SEED_EXAMPLES["safe"]]
    
    for text, suggested in all_seeds:
        if any(e["text"] == text for e in existing):
            continue
            
        print(f"\n[{count}/5000] Text: {text}")
        print(f"Suggested: {suggested}")
        
        choice = input("Label (t/s/skip/add/quit): ").strip().lower()
        
        if choice == "quit":
            break
        elif choice == "skip":
            continue
        elif choice == "add":
            custom_text = input("Enter text: ").strip()
            custom_label = input("Label (t/s): ").strip()
            label = "toxic" if custom_label == "t" else "safe"
            save_example(custom_text, label)
            count += 1
            print(f"✓ Saved")
        elif choice in ["t", "s", ""]:
            if choice == "":
                label = suggested
            else:
                label = "toxic" if choice == "t" else "safe"
            save_example(text, label)
            count += 1
            print(f"✓ Saved as {label}")
    
    # Interactive mode
    print("\n--- Interactive Mode ---")
    print("Enter your own examples (type 'quit' to exit)")
    
    while count < 5000:
        text = input(f"\n[{count}/5000] Enter text (or 'quit'): ").strip()
        if text.lower() == "quit":
            break
        
        label_input = input("Label (t=toxic, s=safe): ").strip().lower()
        if label_input in ["t", "toxic"]:
            save_example(text, "toxic")
            count += 1
            print("✓ Saved as toxic")
        elif label_input in ["s", "safe"]:
            save_example(text, "safe")
            count += 1
            print("✓ Saved as safe")
    
    print(f"\n{'='*50}")
    print(f"Total labeled: {count}")
    print(f"Saved to: {OUTPUT_FILE}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
