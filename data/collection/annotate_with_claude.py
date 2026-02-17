"""
Auto-annotate unknown samples using Claude API.
Uses batch processing to minimize cost.
"""
import json
import os
import time
from pathlib import Path

# Load API key from .env
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

try:
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
except ImportError:
    print("Installing anthropic...")
    import subprocess
    subprocess.run(['pip', 'install', 'anthropic', '-q'])
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

BATCH_SIZE = 20  # Annotate 20 texts per API call

ANNOTATION_PROMPT = """You are a content moderation expert specializing in Indian/Hinglish content.

Classify each text as ONE of:
- safe: Normal conversation, opinions, questions (even if negative sentiment)
- toxic_harassment: Insults, personal attacks, slurs, abuse
- toxic_hate_speech: Discrimination against groups (religion, caste, gender, nationality)
- toxic_threat: Threats of violence or harm
- toxic_sexual: Sexual harassment or explicit content

IMPORTANT RULES:
1. Frustration/complaints are SAFE (e.g., "This is so frustrating", "I hate Mondays")
2. Criticism of ideas/policies is SAFE (e.g., "This policy is terrible")
3. Hindi slurs (bc, mc, chutiya, etc.) are toxic_harassment
4. Religious hate is toxic_hate_speech
5. "I will kill you" type statements are toxic_threat

For each text, respond with ONLY the label, one per line.
Do not add explanations or numbers.

TEXTS:
{texts}

LABELS (one per line, in same order):"""

def annotate_batch(texts: list) -> list:
    """Annotate a batch of texts using Claude."""
    # Format texts with numbers for clarity
    formatted = "\n".join(f"{i+1}. {t[:500]}" for i, t in enumerate(texts))
    
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": ANNOTATION_PROMPT.format(texts=formatted)
            }]
        )
        
        # Parse response
        labels = response.content[0].text.strip().split('\n')
        labels = [l.strip().lower() for l in labels if l.strip()]
        
        # Validate labels
        valid_labels = ['safe', 'toxic_harassment', 'toxic_hate_speech', 'toxic_threat', 'toxic_sexual']
        validated = []
        for label in labels:
            # Clean up label
            for valid in valid_labels:
                if valid in label:
                    validated.append(valid)
                    break
            else:
                validated.append('safe')  # Default to safe if unclear
        
        # Pad if needed
        while len(validated) < len(texts):
            validated.append('safe')
        
        return validated[:len(texts)]
        
    except Exception as e:
        print(f"  Error: {e}")
        return ['safe'] * len(texts)

def main():
    print("=" * 70)
    print("AUTO-ANNOTATION WITH CLAUDE")
    print("=" * 70)
    
    # Load data needing annotation
    with open('needs_annotation.jsonl') as f:
        data = [json.loads(line) for line in f]
    
    print(f"Loaded {len(data)} samples needing annotation")
    
    # Estimate cost
    # Claude Haiku: $0.25/1M input, $1.25/1M output
    # ~100 tokens per text, 20 texts per batch = 2000 tokens input
    # ~20 tokens output per batch
    batches = len(data) // BATCH_SIZE + 1
    estimated_cost = batches * (2000 * 0.25 / 1_000_000 + 50 * 1.25 / 1_000_000)
    print(f"Estimated batches: {batches}")
    print(f"Estimated cost: ${estimated_cost:.4f}")
    
    proceed = input("\nProceed? (y/n): ")
    if proceed.lower() != 'y':
        print("Aborted.")
        return
    
    # Process in batches
    annotated = []
    for i in range(0, len(data), BATCH_SIZE):
        batch = data[i:i+BATCH_SIZE]
        texts = [d['text'] for d in batch]
        
        print(f"\nBatch {i//BATCH_SIZE + 1}/{batches}: annotating {len(texts)} texts...")
        labels = annotate_batch(texts)
        
        for item, label in zip(batch, labels):
            item['label'] = label
            item['annotator'] = 'claude_haiku'
            annotated.append(item)
        
        # Show progress
        toxic_count = sum(1 for l in labels if 'toxic' in l)
        print(f"  Results: {toxic_count} toxic, {len(labels)-toxic_count} safe")
        
        time.sleep(0.5)  # Rate limiting
    
    # Save
    with open('annotated_by_claude.jsonl', 'w') as f:
        for item in annotated:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n{'='*70}")
    print("COMPLETE")
    print(f"{'='*70}")
    
    # Stats
    from collections import Counter
    label_counts = Counter(d['label'] for d in annotated)
    print(f"\nLabel distribution:")
    for label, count in label_counts.most_common():
        print(f"  {label}: {count}")
    
    print(f"\n✅ Saved to: annotated_by_claude.jsonl")

if __name__ == '__main__':
    main()
