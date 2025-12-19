"""
Quick labeler - just press Enter to accept suggestion, or t/s to change.
"""
import json
import os

INPUT_FILE = "data/datasets/to_label.jsonl"
OUTPUT_FILE = "data/datasets/custom_labeled.jsonl"

def main():
    # Load examples to label
    examples = []
    with open(INPUT_FILE, "r") as f:
        for line in f:
            examples.append(json.loads(line))
    
    # Load existing
    existing = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            for line in f:
                d = json.loads(line)
                existing.add(d["text"])
    
    print(f"\n{'='*50}")
    print("Quick Labeler")
    print(f"{'='*50}")
    print(f"Examples to label: {len(examples)}")
    print(f"Already labeled: {len(existing)}")
    print(f"\nPress ENTER to accept suggestion")
    print(f"Type 't' for toxic, 's' for safe")
    print(f"Type 'q' to quit")
    print(f"{'='*50}\n")
    
    count = len(existing)
    
    with open(OUTPUT_FILE, "a") as out:
        for i, ex in enumerate(examples):
            if ex["text"] in existing:
                continue
            
            print(f"\n[{count+1}] {ex['text']}")
            print(f"    Suggested: {ex['suggested']}")
            
            choice = input("    Label [Enter/t/s/q]: ").strip().lower()
            
            if choice == "q":
                break
            elif choice == "t":
                label = "toxic"
            elif choice == "s":
                label = "safe"
            else:
                label = ex["suggested"]
            
            out.write(json.dumps({
                "text": ex["text"],
                "label": label,
                "source": "manual"
            }, ensure_ascii=False) + "\n")
            
            count += 1
            print(f"    ✓ {label}")
    
    print(f"\n{'='*50}")
    print(f"Labeled: {count} examples")
    print(f"Saved to: {OUTPUT_FILE}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
