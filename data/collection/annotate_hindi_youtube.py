"""
Annotate Hindi YouTube comments using Claude.
"""
import json
import os
import time
from pathlib import Path

# Load API key
def load_env():
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

import anthropic
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

BATCH_SIZE = 25

PROMPT = """You are a Hindi/Hinglish content moderation expert.

Classify each text as ONE of:
- safe: Normal conversation, opinions, frustration, criticism
- toxic_harassment: Slurs (bc, mc, chutiya, etc.), personal attacks
- toxic_hate_speech: Hate against religion/caste/region/community
- toxic_threat: Threats of violence
- toxic_sexual: Sexual harassment

RULES:
1. Political criticism is SAFE (e.g., "BJP/Congress ki galti hai")
2. Frustration is SAFE (e.g., "bahut bura lag raha hai")
3. Hindi slurs (bc, mc, chutiya, sala, kamina) are harassment
4. "Pakistan bhejo", "ye log desh ke dushman" is hate_speech
5. "maar dunga", "dekh lunga" is threat

Respond with ONLY labels, one per line.

TEXTS:
{texts}

LABELS:"""

def annotate_batch(texts):
    formatted = "\n".join(f"{i+1}. {t[:400]}" for i, t in enumerate(texts))
    
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=600,
            messages=[{"role": "user", "content": PROMPT.format(texts=formatted)}]
        )
        
        labels = response.content[0].text.strip().split('\n')
        labels = [l.strip().lower() for l in labels if l.strip()]
        
        valid = ['safe', 'toxic_harassment', 'toxic_hate_speech', 'toxic_threat', 'toxic_sexual']
        validated = []
        for label in labels:
            found = False
            for v in valid:
                if v in label:
                    validated.append(v)
                    found = True
                    break
            if not found:
                validated.append('safe')
        
        while len(validated) < len(texts):
            validated.append('safe')
        
        return validated[:len(texts)]
    except Exception as e:
        print(f"  Error: {e}")
        return ['safe'] * len(texts)

def main():
    print("=" * 70)
    print("ANNOTATING HINDI YOUTUBE COMMENTS")
    print("=" * 70)
    
    with open('youtube_hindi_raw.jsonl') as f:
        data = [json.loads(line) for line in f]
    
    print(f"Loaded {len(data)} Hindi comments")
    
    batches = len(data) // BATCH_SIZE + 1
    estimated_cost = batches * 0.0005  # ~$0.0005 per batch
    print(f"Batches: {batches}, Estimated cost: ${estimated_cost:.3f}")
    
    proceed = input("Proceed? (y/n): ")
    if proceed.lower() != 'y':
        return
    
    annotated = []
    for i in range(0, len(data), BATCH_SIZE):
        batch = data[i:i+BATCH_SIZE]
        texts = [d['text'] for d in batch]
        
        print(f"Batch {i//BATCH_SIZE + 1}/{batches}...", end=" ")
        labels = annotate_batch(texts)
        
        toxic_count = sum(1 for l in labels if 'toxic' in l)
        print(f"({toxic_count} toxic)")
        
        for item, label in zip(batch, labels):
            item['label'] = label
            if 'toxic' in label:
                item['category'] = label.replace('toxic_', '')
            else:
                item['category'] = 'safe'
            annotated.append(item)
        
        time.sleep(0.3)
    
    # Save
    with open('youtube_hindi_annotated.jsonl', 'w') as f:
        for item in annotated:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Stats
    from collections import Counter
    label_counts = Counter(d['label'] for d in annotated)
    
    print(f"\n{'='*70}")
    print("ANNOTATION COMPLETE")
    print(f"{'='*70}")
    for label, count in label_counts.most_common():
        print(f"  {label}: {count}")
    
    print(f"\n✅ Saved to: youtube_hindi_annotated.jsonl")
    
    # Add to final dataset
    print(f"\nAdding to final dataset...")
    
    final_dir = Path("../datasets/curated/final")
    with open(final_dir / "all.jsonl") as f:
        existing = [json.loads(line) for line in f]
    
    # Format for final dataset
    new_samples = []
    for item in annotated:
        new_samples.append({
            'text': item['text'],
            'label': 'toxic' if 'toxic' in item['label'] else 'safe',
            'category': item['category'],
            'source': 'youtube_hindi'
        })
    
    combined = existing + new_samples
    
    # Save
    import random
    random.seed(42)
    random.shuffle(combined)
    
    n = len(combined)
    train_end = int(n * 0.8)
    val_end = int(n * 0.9)
    
    with open(final_dir / "all.jsonl", 'w') as f:
        for item in combined:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    with open(final_dir / "train.jsonl", 'w') as f:
        for item in combined[:train_end]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    with open(final_dir / "val.jsonl", 'w') as f:
        for item in combined[train_end:val_end]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    with open(final_dir / "test.jsonl", 'w') as f:
        for item in combined[val_end:]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Final dataset now has {len(combined)} samples")
    
    # Hindi count
    hindi_sources = ['youtube_hindi', 'hindi_curated']
    hindi_count = len([d for d in combined if d.get('source') in hindi_sources])
    print(f"✅ Hindi/Hinglish samples: {hindi_count}")

if __name__ == '__main__':
    main()
