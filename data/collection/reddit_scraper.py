"""
Reddit Comment Scraper for Hinglish Content.
No API key needed - uses public JSON endpoints.
"""
import json
import urllib.request
import time
import random
import re
from collections import Counter

# Subreddits with high Hinglish/Indian content
SUBREDDITS = [
    "india",
    "IndiaSpeaks", 
    "bollywood",
    "BollyBlindsNGossip",
    "cricket",
    "IndianGaming",
    "delhi",
    "mumbai",
    "bangalore",
    "IndianDankMemes",
    "SaimanSays",
    "indiasocial",
]

# We want controversial/hot posts for more toxic content
SORT_OPTIONS = ["controversial", "hot", "new"]

def get_comments(subreddit: str, sort: str = "hot", limit: int = 100) -> list:
    """Fetch comments from a subreddit."""
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ContentResearch/1.0'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        comments = []
        posts = data.get('data', {}).get('children', [])
        
        for post in posts:
            post_data = post.get('data', {})
            post_id = post_data.get('id')
            post_title = post_data.get('title', '')
            
            # Get comments for this post
            comment_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json?limit=50"
            try:
                req = urllib.request.Request(comment_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    comment_data = json.loads(response.read().decode())
                
                if len(comment_data) > 1:
                    comment_list = comment_data[1].get('data', {}).get('children', [])
                    for comment in comment_list:
                        if comment.get('kind') == 't1':
                            body = comment.get('data', {}).get('body', '')
                            score = comment.get('data', {}).get('score', 0)
                            
                            # Skip deleted/removed
                            if body in ['[deleted]', '[removed]', '']:
                                continue
                            
                            # Skip very short
                            if len(body) < 10:
                                continue
                                
                            comments.append({
                                'text': body[:1000],  # Limit length
                                'subreddit': subreddit,
                                'score': score,
                                'post_title': post_title[:100],
                                'source': 'reddit'
                            })
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                continue
        
        return comments
        
    except Exception as e:
        print(f"Error fetching r/{subreddit}: {e}")
        return []

def has_hinglish(text: str) -> bool:
    """Check if text contains Hinglish/Hindi."""
    # Common Hindi words in Latin script
    hindi_indicators = [
        'bhai', 'yaar', 'kya', 'hai', 'nahi', 'kaise', 'acha', 'accha',
        'theek', 'haan', 'matlab', 'abhi', 'bahut', 'kuch', 'sala',
        'chutiya', 'bc', 'mc', 'behen', 'maa', 'gaand', 'lodu',
        'pagal', 'bewakoof', 'kamina', 'harami', 'bakwas',
        'sahi', 'galat', 'aur', 'lekin', 'kyun', 'kab', 'kaun',
        'woh', 'yeh', 'tum', 'mujhe', 'tera', 'mera', 'uska',
        'ji', 'arre', 'oye', 'haha', 'lol', 'bro'
    ]
    
    text_lower = text.lower()
    return any(word in text_lower for word in hindi_indicators)

def is_potentially_toxic(text: str) -> bool:
    """Quick check for potentially toxic content."""
    toxic_indicators = [
        # English
        'hate', 'stupid', 'idiot', 'dumb', 'kill', 'die', 'worst',
        'trash', 'garbage', 'pathetic', 'loser', 'shut up', 'stfu',
        # Hindi/Hinglish
        'chutiya', 'bc', 'mc', 'bhenchod', 'madarchod', 'sala',
        'kamina', 'harami', 'gandu', 'lodu', 'bhosdike', 'randi',
        'pagal', 'bewakoof', 'gadha', 'ullu',
        # Negative sentiment
        'worst', 'terrible', 'horrible', 'disgusting', 'pathetic'
    ]
    
    text_lower = text.lower()
    return any(word in text_lower for word in toxic_indicators)

def main():
    print("=" * 70)
    print("REDDIT HINGLISH COMMENT SCRAPER")
    print("=" * 70)
    
    all_comments = []
    
    for subreddit in SUBREDDITS:
        for sort in SORT_OPTIONS:
            print(f"\nScraping r/{subreddit} ({sort})...")
            comments = get_comments(subreddit, sort, limit=50)
            
            # Filter for Hinglish or potentially toxic
            filtered = []
            for c in comments:
                if has_hinglish(c['text']) or is_potentially_toxic(c['text']):
                    c['has_hinglish'] = has_hinglish(c['text'])
                    c['potentially_toxic'] = is_potentially_toxic(c['text'])
                    filtered.append(c)
            
            all_comments.extend(filtered)
            print(f"  Found {len(comments)} comments, {len(filtered)} relevant")
            
            time.sleep(1)  # Be nice to Reddit
    
    # Deduplicate
    seen = set()
    unique_comments = []
    for c in all_comments:
        text_hash = hash(c['text'][:100])
        if text_hash not in seen:
            seen.add(text_hash)
            unique_comments.append(c)
    
    print(f"\n" + "=" * 70)
    print(f"SCRAPING COMPLETE")
    print(f"=" * 70)
    print(f"Total unique comments: {len(unique_comments)}")
    
    # Stats
    hinglish_count = sum(1 for c in unique_comments if c.get('has_hinglish'))
    toxic_count = sum(1 for c in unique_comments if c.get('potentially_toxic'))
    
    print(f"With Hinglish: {hinglish_count}")
    print(f"Potentially toxic: {toxic_count}")
    
    # By subreddit
    sub_counts = Counter(c['subreddit'] for c in unique_comments)
    print(f"\nBy subreddit:")
    for sub, count in sub_counts.most_common():
        print(f"  r/{sub}: {count}")
    
    # Save
    with open('reddit_raw.jsonl', 'w') as f:
        for c in unique_comments:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Saved to: reddit_raw.jsonl")
    
    # Show samples
    print(f"\n" + "=" * 70)
    print("SAMPLE COMMENTS")
    print("=" * 70)
    
    # Hinglish samples
    hinglish = [c for c in unique_comments if c.get('has_hinglish')][:5]
    print("\n--- HINGLISH ---")
    for c in hinglish:
        print(f"  [{c['subreddit']}] {c['text'][:80]}...")
    
    # Potentially toxic samples  
    toxic = [c for c in unique_comments if c.get('potentially_toxic')][:5]
    print("\n--- POTENTIALLY TOXIC ---")
    for c in toxic:
        print(f"  [{c['subreddit']}] {c['text'][:80]}...")

if __name__ == '__main__':
    main()
