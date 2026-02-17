"""
YouTube scraper focused specifically on Hindi/Hinglish content.
Targets channels and videos with maximum Hindi comments.
"""
import json
import urllib.request
import urllib.parse
import time
import os
from collections import Counter
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
API_KEY = os.getenv('YOUTUBE_API_KEY', '')

# Hindi-specific search queries
HINDI_TARGETS = [
    # Hindi news debates
    "aaj tak debate",
    "zee news debate hindi",
    "republic bharat debate",
    "news nation debate",
    "india tv rajat sharma",
    
    # Bollywood gossip (high Hinglish)
    "bollywood gossip hindi",
    "karan johar controversy",
    "salman khan fight",
    "kangana ranaut interview",
    
    # Cricket Hindi
    "india vs pakistan hindi commentary",
    "virat kohli press conference hindi",
    "rohit sharma interview hindi",
    
    # Indian YouTubers (Hinglish heavy)
    "carryminati",
    "triggered insaan roast",
    "ashish chanchlani",
    "bb ki vines",
    "tanmay bhat",
    "thugesh",
    "lakshay chaudhary",
    
    # Controversial Hindi
    "hindu muslim debate hindi",
    "caste reservation debate hindi",
    "farmers protest hindi",
    "jnu controversy hindi",
    
    # Reality shows (toxic comments)
    "bigg boss hindi fight",
    "roadies hindi audition",
    "splitsvilla fight",
    "khatron ke khiladi",
    
    # Regional
    "delhi vs mumbai hindi",
    "north india south india debate",
    "up bihar controversy",
]

def search_videos(query: str, max_results: int = 5) -> list:
    """Search for videos."""
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={urllib.parse.quote(query)}&type=video&maxResults={max_results}&regionCode=IN&key={API_KEY}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
        
        videos = []
        for item in data.get('items', []):
            videos.append({
                'video_id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle']
            })
        return videos
    except Exception as e:
        print(f"  Search error: {str(e)[:40]}")
        return []

def get_video_comments(video_id: str, max_comments: int = 100) -> list:
    """Get comments from a video."""
    comments = []
    url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults={min(max_comments, 100)}&textFormat=plainText&key={API_KEY}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
        
        for item in data.get('items', []):
            snippet = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'text': snippet['textDisplay'][:1000],
                'likes': snippet['likeCount'],
                'video_id': video_id
            })
    except:
        pass
    
    return comments

def is_hindi_content(text: str) -> bool:
    """Check if text contains Hindi/Hinglish."""
    # Devanagari script
    has_devanagari = any('\u0900' <= c <= '\u097F' for c in text)
    if has_devanagari:
        return True
    
    # Hinglish words
    hinglish = [
        'bhai', 'yaar', 'kya', 'hai', 'nahi', 'kaise', 'accha', 'acha',
        'theek', 'haan', 'matlab', 'abhi', 'bahut', 'bohot', 'kuch',
        'sala', 'saala', 'pagal', 'sahi', 'galat', 'aur', 'lekin',
        'kyun', 'kyu', 'kaun', 'woh', 'yeh', 'tum', 'tera', 'mera',
        'arre', 'oye', 'dekh', 'chal', 'bol', 'sun', 'bolo', 'suno',
        'karo', 'karna', 'hota', 'liye', 'wala', 'waala', 'wali',
        'sabse', 'jaldi', 'abhi', 'baad', 'pehle', 'upar', 'niche',
        'bc', 'mc', 'chutiya', 'bhenchod', 'madarchod', 'gandu',
        'kamina', 'harami', 'bakwas', 'bekar', 'mast', 'zabardast',
        'ekdum', 'bilkul', 'pakka', 'sachchi', 'jhooth', 'sach'
    ]
    
    text_lower = text.lower()
    hindi_count = sum(1 for w in hinglish if w in text_lower)
    return hindi_count >= 2  # At least 2 Hindi words

def is_toxic(text: str) -> bool:
    """Check for toxic indicators."""
    toxic_words = [
        'chutiya', 'bc', 'mc', 'bhenchod', 'madarchod', 'sala', 'saala',
        'kamina', 'harami', 'gandu', 'lodu', 'bhosdike', 'randi',
        'gadha', 'ullu', 'bewakoof', 'nalayak', 'nikamma', 'tatti',
        'hate', 'stupid', 'idiot', 'worst', 'pathetic', 'trash',
        'kill', 'die', 'murder', 'terrorist', 'anti-national'
    ]
    text_lower = text.lower()
    return any(w in text_lower for w in toxic_words)

def main():
    print("=" * 70)
    print("YOUTUBE HINDI SCRAPER")
    print("=" * 70)
    
    if not API_KEY:
        print("❌ YOUTUBE_API_KEY not set!")
        return
    
    print(f"✅ API Key loaded")
    print(f"Targets: {len(HINDI_TARGETS)} search queries")
    
    all_comments = []
    
    for i, query in enumerate(HINDI_TARGETS):
        print(f"\n[{i+1}/{len(HINDI_TARGETS)}] 🔍 {query}")
        
        videos = search_videos(query, max_results=3)
        print(f"  Found {len(videos)} videos")
        
        for video in videos:
            comments = get_video_comments(video['video_id'], max_comments=50)
            
            # Filter for Hindi content
            hindi_comments = []
            for c in comments:
                if is_hindi_content(c['text']):
                    c['is_hindi'] = True
                    c['is_toxic'] = is_toxic(c['text'])
                    c['video_title'] = video['title']
                    c['channel'] = video['channel']
                    c['search_query'] = query
                    c['source'] = 'youtube_hindi'
                    hindi_comments.append(c)
            
            all_comments.extend(hindi_comments)
            
            if hindi_comments:
                print(f"    📹 {len(hindi_comments)} Hindi comments from: {video['title'][:40]}...")
            
            time.sleep(0.3)
        
        time.sleep(0.5)
    
    # Deduplicate
    seen = set()
    unique = []
    for c in all_comments:
        h = hash(c['text'][:100])
        if h not in seen:
            seen.add(h)
            unique.append(c)
    
    # Stats
    print(f"\n{'='*70}")
    print("COMPLETE")
    print(f"{'='*70}")
    print(f"Total Hindi comments: {len(unique)}")
    print(f"Potentially toxic: {sum(1 for c in unique if c.get('is_toxic'))}")
    
    # By query
    query_counts = Counter(c['search_query'] for c in unique)
    print(f"\nTop queries:")
    for q, count in query_counts.most_common(10):
        print(f"  {q}: {count}")
    
    # Save
    with open('youtube_hindi_raw.jsonl', 'w') as f:
        for c in unique:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Saved to: youtube_hindi_raw.jsonl")
    
    # Samples
    print(f"\n{'='*70}")
    print("SAMPLES")
    print(f"{'='*70}")
    
    toxic = [c for c in unique if c.get('is_toxic')][:5]
    print("\n--- TOXIC HINDI ---")
    for c in toxic:
        print(f"  {c['text'][:70]}...")
    
    safe = [c for c in unique if not c.get('is_toxic')][:5]
    print("\n--- SAFE HINDI ---")
    for c in safe:
        print(f"  {c['text'][:70]}...")

if __name__ == '__main__':
    main()
