"""
Download Hindi/Hinglish hate speech datasets from working sources.
"""
import json
import urllib.request
from collections import Counter

print("=" * 70)
print("DOWNLOADING: Hindi Hate Speech Datasets")
print("=" * 70)

all_data = []

# Source 1: MOLD (Marathi and Hindi Offensive Language Dataset)
# From GitHub
sources = [
    {
        'name': 'Hindi Hostility Detection',
        'url': 'https://raw.githubusercontent.com/hate-alert/Hindi-Hostility-Detection-CONSTRAINT-2021/main/Dataset/Dataset%20for%20Shared%20Task/hindi_train.csv',
        'format': 'csv'
    },
    {
        'name': 'TRAC Aggression Hindi',
        'url': 'https://raw.githubusercontent.com/kraiyani/TRAC-2020/master/hin/trac2_hin_train.csv',
        'format': 'csv'
    }
]

import csv
from io import StringIO

for source in sources:
    print(f"\nTrying: {source['name']}...")
    try:
        req = urllib.request.Request(source['url'], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8', errors='ignore')
        
        reader = csv.DictReader(StringIO(content))
        count = 0
        for row in reader:
            # Different datasets have different column names
            text = row.get('text', row.get('Text', row.get('tweet', row.get('Tweet', ''))))
            label = row.get('label', row.get('Label', row.get('task_1', row.get('class', ''))))
            
            if text and label:
                all_data.append({
                    'text': text.strip(),
                    'label': label.strip(),
                    'source': source['name']
                })
                count += 1
        print(f"  ✅ Loaded {count} samples")
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:50]}")

# Source 2: Try direct GitHub search for Hindi datasets
alt_sources = [
    'https://raw.githubusercontent.com/harshildarji/Hinglish-Hate-Speech-Dataset/main/data/train.csv',
    'https://raw.githubusercontent.com/mohit3011/Hinglish-Offensive-Text-Classification/main/Dataset/train.csv'
]

for url in alt_sources:
    name = url.split('/')[-3]
    print(f"\nTrying: {name}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8', errors='ignore')
        
        reader = csv.DictReader(StringIO(content))
        count = 0
        for row in reader:
            text = row.get('text', row.get('Text', row.get('tweet', ''))[:500])
            label = row.get('label', row.get('Label', row.get('class', '')))
            
            if text:
                all_data.append({
                    'text': text.strip(),
                    'label': str(label).strip() if label else 'unknown',
                    'source': name
                })
                count += 1
        print(f"  ✅ Loaded {count} samples")
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:50]}")

print(f"\n" + "=" * 70)
print(f"TOTAL LOADED: {len(all_data)} samples")
print("=" * 70)

if len(all_data) > 0:
    # Analyze
    label_counts = Counter(d['label'] for d in all_data)
    source_counts = Counter(d['source'] for d in all_data)
    
    print(f"\nBy Source:")
    for src, count in source_counts.most_common():
        print(f"  {src}: {count}")
    
    print(f"\nBy Label:")
    for label, count in label_counts.most_common(10):
        print(f"  {label}: {count}")
    
    # Save raw
    with open('hindi_hate_raw.jsonl', 'w') as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Saved to: hindi_hate_raw.jsonl")
    
    # Show samples
    print(f"\n" + "=" * 70)
    print("SAMPLE TEXTS")
    print("=" * 70)
    
    import random
    random.seed(42)
    samples = random.sample(all_data, min(20, len(all_data)))
    for item in samples:
        text = item['text'][:70]
        label = item['label']
        print(f"  [{label:15}] {text}...")

else:
    print("\n⚠️ No data loaded. Creating manual Hindi dataset...")
    
    # Manual Hindi hate speech dataset (real examples you'd collect)
    manual_hindi = [
        # Toxic - Slurs
        {"text": "भड़वा साला", "label": "toxic", "category": "slur"},
        {"text": "मादरचोद कहीं का", "label": "toxic", "category": "slur"},
        {"text": "बहनचोद तू चुप रह", "label": "toxic", "category": "slur"},
        {"text": "चूतिया है क्या तू", "label": "toxic", "category": "slur"},
        {"text": "गांडू कहीं का", "label": "toxic", "category": "slur"},
        {"text": "कमीने इंसान", "label": "toxic", "category": "slur"},
        {"text": "हरामी की औलाद", "label": "toxic", "category": "slur"},
        {"text": "रंडी का बच्चा", "label": "toxic", "category": "slur"},
        {"text": "भोसड़ीके", "label": "toxic", "category": "slur"},
        {"text": "लौड़े लग गए तेरे", "label": "toxic", "category": "slur"},
        
        # Toxic - Threats
        {"text": "तेरा टाइम आ गया है, तैयार रह", "label": "toxic", "category": "threat"},
        {"text": "मार डालूंगा तुझे", "label": "toxic", "category": "threat"},
        {"text": "तेरी जान ले लूंगा", "label": "toxic", "category": "threat"},
        {"text": "देख लूंगा तुझे बाहर", "label": "toxic", "category": "threat"},
        {"text": "तेरा खून पी जाऊंगा", "label": "toxic", "category": "threat"},
        
        # Toxic - Hinglish
        {"text": "bc tu pagal hai kya", "label": "toxic", "category": "slur_hinglish"},
        {"text": "mc sala", "label": "toxic", "category": "slur_hinglish"},
        {"text": "chutiya saala", "label": "toxic", "category": "slur_hinglish"},
        {"text": "bhenchod tune kya kiya", "label": "toxic", "category": "slur_hinglish"},
        {"text": "gaandu insaan", "label": "toxic", "category": "slur_hinglish"},
        
        # Safe - Greetings
        {"text": "नमस्ते, कैसे हो आप?", "label": "safe", "category": "greeting"},
        {"text": "क्या हाल है भाई?", "label": "safe", "category": "greeting"},
        {"text": "शुभ प्रभात", "label": "safe", "category": "greeting"},
        {"text": "बहुत अच्छा मिलकर", "label": "safe", "category": "greeting"},
        {"text": "धन्यवाद आपका", "label": "safe", "category": "greeting"},
        
        # Safe - Normal conversation
        {"text": "आज मौसम बहुत अच्छा है", "label": "safe", "category": "normal"},
        {"text": "खाना बहुत स्वादिष्ट था", "label": "safe", "category": "normal"},
        {"text": "यह फिल्म बहुत अच्छी है", "label": "safe", "category": "normal"},
        {"text": "कल मिलते हैं", "label": "safe", "category": "normal"},
        {"text": "बहुत मेहनत की तुमने", "label": "safe", "category": "normal"},
        
        # Safe - Frustration (NOT toxic)
        {"text": "बहुत मुश्किल है यह", "label": "safe", "category": "frustration"},
        {"text": "थक गया हूं आज", "label": "safe", "category": "frustration"},
        {"text": "यह बहुत कठिन है", "label": "safe", "category": "frustration"},
        {"text": "परेशान हो गया हूं", "label": "safe", "category": "frustration"},
        {"text": "सर दर्द हो रहा है", "label": "safe", "category": "frustration"},
        
        # Safe - Hinglish normal
        {"text": "bhai kya scene hai", "label": "safe", "category": "hinglish_normal"},
        {"text": "chal theek hai", "label": "safe", "category": "hinglish_normal"},
        {"text": "bahut mast hai yaar", "label": "safe", "category": "hinglish_normal"},
        {"text": "time nahi hai mujhe", "label": "safe", "category": "hinglish_normal"},
        {"text": "tera number aa gaya", "label": "safe", "category": "hinglish_normal"},
    ]
    
    all_data = [{"text": d["text"], "label": d["label"], "category": d["category"], "source": "manual_hindi"} for d in manual_hindi]
    
    with open('hindi_hate_raw.jsonl', 'w') as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Created manual Hindi dataset: {len(all_data)} samples")
    
    label_counts = Counter(d['label'] for d in all_data)
    print(f"\nDistribution:")
    for label, count in label_counts.items():
        print(f"  {label}: {count}")

print("\n" + "=" * 70)
