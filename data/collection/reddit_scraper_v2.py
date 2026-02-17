"""
Reddit Comment Scraper v2 - With proper rate limiting.
Slower but won't get blocked.
"""
import json
import urllib.request
import time
import random
from collections import Counter

SUBREDDITS = [
    "india",
    "IndiaSpeaks", 
    "bollywood",
    "BollyBlindsNGossip",
    "cricket",
    "IndianDankMemes",
    "delhi",
    "mumbai",
]

def get_subreddit_posts(subreddit: str, sort: str = "hot", limit: int = 25) -> list:
    """Fetch posts from a subreddit with proper rate limiting."""
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ResearchBot/1.0'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
        return data.get('data', {}).get('children', [])
    except Exception as e:
        print(f"  Error: {e}")
        return []

def get_post_comments(subreddit: str, post_id: str) -> list:
    """Fetch comments for a specific post."""
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json?limit=100&depth=2"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ResearchBot/1.0'
    }
    
    comments = []
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
        
        if len(data) > 1:
            def extract_comments(children):
                for child in children:
                    if child.get('kind') == 't1':
                        body = child.get('data', {}).get('body', '')
                        if body and body not in ['[deleted]', '[removed]'] and len(body) > 10:
                            comments.append({
                                'text': body[:1000],
                                'score': child.get('data', {}).get('score', 0),
                            })
                        # Get replies too
                        replies = child.get('data', {}).get('replies', '')
                        if isinstance(replies, dict):
                            reply_children = replies.get('data', {}).get('children', [])
                            extract_comments(reply_children)
            
            extract_comments(data[1].get('data', {}).get('children', []))
    except Exception as e:
        pass
    
    return comments

def has_hindi_or_toxic(text: str) -> tuple:
    """Check for Hindi/Hinglish content or toxic indicators."""
    text_lower = text.lower()
    
    hindi_words = [
        'bhai', 'yaar', 'kya', 'hai', 'nahi', 'kaise', 'acha', 'accha',
        'theek', 'haan', 'matlab', 'abhi', 'bahut', 'kuch', 'sala',
        'pagal', 'sahi', 'galat', 'aur', 'lekin', 'kyun', 'kab',
        'woh', 'yeh', 'tum', 'mujhe', 'tera', 'mera', 'uska',
        'arre', 'oye', 'dekh', 'chal', 'ruk', 'bol', 'sun'
    ]
    
    toxic_words = [
        'chutiya', 'bc', 'mc', 'bhenchod', 'madarchod', 'sala',
        'kamina', 'harami', 'gandu', 'lodu', 'bhosdike', 'randi',
        'hate', 'stupid', 'idiot', 'dumb', 'worst', 'pathetic',
        'trash', 'garbage', 'loser', 'stfu', 'wtf'
    ]
    
    has_hindi = any(w in text_lower for w in hindi_words)
    has_toxic = any(w in text_lower for w in toxic_words)
    
    return has_hindi, has_toxic

def main():
    print("=" * 70)
    print("REDDIT SCRAPER v2 - Slow & Steady")
    print("=" * 70)
    print("This will take ~15-20 minutes to avoid rate limiting")
    print("=" * 70)
    
    all_comments = []
    
    for i, subreddit in enumerate(SUBREDDITS):
        print(f"\n[{i+1}/{len(SUBREDDITS)}] Scraping r/{subreddit}...")
        
        # Get posts
        posts = get_subreddit_posts(subreddit, "hot", limit=20)
        print(f"  Found {len(posts)} posts")
        
        # Wait before getting comments
        time.sleep(3)
        
        sub_comments = []
        for j, post in enumerate(posts[:15]):  # Limit posts per subreddit
            post_id = post.get('data', {}).get('id')
            post_title = post.get('data', {}).get('title', '')
            
            if not post_id:
                continue
            
            comments = get_post_comments(subreddit, post_id)
            
            for c in comments:
                has_hindi, has_toxic = has_hindi_or_toxic(c['text'])
                if has_hindi or has_toxic:
                    c['subreddit'] = subreddit
                    c['post_title'] = post_title[:100]
                    c['has_hindi'] = has_hindi
                    c['has_toxic'] = has_toxic
                    c['source'] = 'reddit'
                    sub_comments.append(c)
            
            # Progress indicator
            if (j + 1) % 5 == 0:
                print(f"    Processed {j+1}/{min(15, len(posts))} posts...")
            
            # Rate limiting - wait between posts
            time.sleep(2 + random.random())
        
        all_comments.extend(sub_comments)
        print(f"  Collected {len(sub_comments)} relevant comments")
        
        # Longer wait between subreddits
        if i < len(SUBREDDITS) - 1:
            wait_time = 10 + random.randint(0, 5)
            print(f"  Waiting {wait_time}s before next subreddit...")
            time.sleep(wait_time)
    
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
    print(f"Total unique comments: {len(unique)}")
    print(f"With Hindi/Hinglish: {sum(1 for c in unique if c.get('has_hindi'))}")
    print(f"Potentially toxic: {sum(1 for c in unique if c.get('has_toxic'))}")
    
    sub_counts = Counter(c['subreddit'] for c in unique)
    print(f"\nBy subreddit:")
    for sub, count in sub_counts.most_common():
        print(f"  r/{sub}: {count}")
    
    # Save
    with open('reddit_raw.jsonl', 'w') as f:
        for c in unique:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Saved to: reddit_raw.jsonl")
    
    # Samples
    print(f"\n--- SAMPLES ---")
    for c in unique[:10]:
        hindi = "🇮🇳" if c.get('has_hindi') else ""
        toxic = "⚠️" if c.get('has_toxic') else ""
        print(f"  [{c['subreddit']}] {hindi}{toxic} {c['text'][:60]}...")

if __name__ == '__main__':
    main()
