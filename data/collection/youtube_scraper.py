"""
YouTube Comments Scraper for Hinglish/Indian Content.
Targets: News channels, Drama, Cricket, Bollywood - high toxicity areas.
"""
import json
import urllib.request
import urllib.parse
import time
import os
from collections import Counter
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
API_KEY = os.getenv('YOUTUBE_API_KEY', '')

# Indian channels/videos with high Hinglish + toxic comments
TARGETS = [
    # News Debates (very toxic)
    ("indian news debate", "search"),
    ("arnab goswami debate", "search"),
    ("india pakistan cricket", "search"),
    ("bollywood nepotism", "search"),
    ("indian politics debate", "search"),
    
    # Controversial topics
    ("hindu muslim india", "search"),
    ("reservation india debate", "search"),
    ("north south india", "search"),
    ("delhi vs mumbai", "search"),
    
    # Bollywood drama
    ("bollywood star interview", "search"),
    ("bigg boss fight", "search"),
    ("roadies audition", "search"),
    
    # Cricket (toxic during losses)
    ("india cricket loss", "search"),
    ("virat kohli out", "search"),
    ("ipl fight", "search"),
    
    # Gaming/Memes (Hinglish heavy)
    ("carryminati roast", "search"),
    ("indian gaming toxic", "search"),
    ("thugesh roast", "search"),
]

def search_videos(query: str, max_results: int = 10) -> list:
    """Search for videos and return video IDs."""
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={urllib.parse.quote(query)}&type=video&maxResults={max_results}&regionCode=IN&relevanceLanguage=hi&key={API_KEY}"
    
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
        print(f"  Search error: {e}")
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
                'author': snippet['authorDisplayName'],
                'video_id': video_id
            })
    except Exception as e:
        if '403' in str(e):
            print(f"    ⚠️ Comments disabled")
        elif '404' in str(e):
            print(f"    ⚠️ Video not found")
        else:
            print(f"    ⚠️ Error: {str(e)[:40]}")
    
    return comments

def has_hindi_or_toxic(text: str) -> tuple:
    """Check for Hindi/Hinglish or toxic content."""
    text_lower = text.lower()
    
    hindi_words = [
        'bhai', 'yaar', 'kya', 'hai', 'nahi', 'kaise', 'acha', 'accha',
        'theek', 'haan', 'matlab', 'abhi', 'bahut', 'kuch', 'sala',
        'pagal', 'sahi', 'galat', 'aur', 'lekin', 'kyun', 'kab',
        'woh', 'yeh', 'tum', 'mujhe', 'tera', 'mera', 'uska',
        'arre', 'oye', 'dekh', 'chal', 'ruk', 'bol', 'sun',
        'karo', 'karna', 'hota', 'hoti', 'liye', 'wala', 'waala',
        'sabse', 'bahut', 'bohot', 'achha', 'bura', 'jaldi'
    ]
    
    # Hindi script detection
    has_devanagari = any('\u0900' <= c <= '\u097F' for c in text)
    
    toxic_words = [
        'chutiya', 'bc', 'mc', 'bhenchod', 'madarchod', 'sala',
        'kamina', 'harami', 'gandu', 'lodu', 'bhosdike', 'randi',
        'hate', 'stupid', 'idiot', 'dumb', 'worst', 'pathetic',
        'trash', 'garbage', 'loser', 'wtf', 'die', 'kill',
        'gadha', 'ullu', 'bewakoof', 'nalayak', 'nikamma',
        'tatti', 'bakwas', 'ghatiya', 'bekaar'
    ]
    
    has_hindi = has_devanagari or any(w in text_lower for w in hindi_words)
    has_toxic = any(w in text_lower for w in toxic_words)
    
    return has_hindi, has_toxic

def main():
    print("=" * 70)
    print("YOUTUBE COMMENTS SCRAPER - Indian Content")
    print("=" * 70)
    
    if not API_KEY:
        print("\n❌ ERROR: YOUTUBE_API_KEY not found in .env!")
        print("Add to ~/Downloads/universal-restrictor/.env:")
        print("  YOUTUBE_API_KEY=your_api_key_here")
        return
    
    print(f"✅ API Key loaded: {API_KEY[:10]}...")
    
    all_comments = []
    videos_processed = 0
    
    for query, target_type in TARGETS:
        print(f"\n🔍 Searching: {query}")
        
        videos = search_videos(query, max_results=5)
        print(f"  Found {len(videos)} videos")
        
        for video in videos:
            print(f"    📹 {video['title'][:50]}...")
            comments = get_video_comments(video['video_id'], max_comments=50)
            
            relevant = []
            for c in comments:
                has_hindi, has_toxic = has_hindi_or_toxic(c['text'])
                if has_hindi or has_toxic or len(c['text']) > 50:
                    c['has_hindi'] = has_hindi
                    c['has_toxic'] = has_toxic
                    c['video_title'] = video['title']
                    c['channel'] = video['channel']
                    c['source'] = 'youtube'
                    c['search_query'] = query
                    relevant.append(c)
            
            all_comments.extend(relevant)
            videos_processed += 1
            print(f"      Got {len(relevant)} relevant comments")
            
            time.sleep(0.5)
        
        time.sleep(1)
    
    # Deduplicate
    seen = set()
    unique = []
    for c in all_comments:
        h = hash(c['text'][:100])
        if h not in seen:
            seen.add(h)
            unique.append(c)
    
    # Stats
    print(f"\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"Videos processed: {videos_processed}")
    print(f"Total unique comments: {len(unique)}")
    print(f"With Hindi/Hinglish: {sum(1 for c in unique if c.get('has_hindi'))}")
    print(f"Potentially toxic: {sum(1 for c in unique if c.get('has_toxic'))}")
    
    query_counts = Counter(c['search_query'] for c in unique)
    print(f"\nBy search query:")
    for q, count in query_counts.most_common(10):
        print(f"  {q}: {count}")
    
    # Save
    with open('youtube_raw.jsonl', 'w') as f:
        for c in unique:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Saved to: youtube_raw.jsonl")
    
    # Samples
    print(f"\n" + "=" * 70)
    print("SAMPLE COMMENTS")
    print("=" * 70)
    
    hindi_samples = [c for c in unique if c.get('has_hindi')][:5]
    print("\n--- HINDI/HINGLISH ---")
    for c in hindi_samples:
        print(f"  {c['text'][:70]}...")
    
    toxic_samples = [c for c in unique if c.get('has_toxic')][:5]
    print("\n--- POTENTIALLY TOXIC ---")
    for c in toxic_samples:
        print(f"  {c['text'][:70]}...")

if __name__ == '__main__':
    main()
