"""
Download Hindi datasets from Zenodo.
"""
import json
import urllib.request
import zipfile
import os
from io import BytesIO

print("=" * 70)
print("DOWNLOADING: Hindi Datasets from Zenodo")
print("=" * 70)

# HASOC 2021 Hindi - Zenodo Record 5172672
zenodo_records = [
    {
        'name': 'HASOC 2021',
        'record_id': '5172672',
        'description': 'Hindi, English, Marathi hate speech'
    },
    {
        'name': 'Hindi Hostility Detection',
        'record_id': '4459889',
        'description': 'CONSTRAINT 2021 shared task'
    }
]

for record in zenodo_records:
    print(f"\n--- {record['name']} ---")
    print(f"Description: {record['description']}")
    print(f"URL: https://zenodo.org/records/{record['record_id']}")
    
    # Try to get metadata
    try:
        api_url = f"https://zenodo.org/api/records/{record['record_id']}"
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        print(f"Title: {data.get('metadata', {}).get('title', 'N/A')}")
        
        # List files
        files = data.get('files', [])
        print(f"Files available:")
        for f in files:
            size_mb = f.get('size', 0) / (1024*1024)
            print(f"  - {f.get('key', 'unknown')} ({size_mb:.1f} MB)")
            print(f"    Download: {f.get('links', {}).get('self', 'N/A')}")
    
    except Exception as e:
        print(f"Error: {e}")

print(f"\n" + "=" * 70)
print("MANUAL DOWNLOAD INSTRUCTIONS")
print("=" * 70)
print("""
To download Hindi datasets:

1. HASOC 2021 (Recommended):
   - Go to: https://zenodo.org/records/5172672
   - Download the zip file
   - Extract to: ~/Downloads/universal-restrictor/data/datasets/curated/raw/

2. Hindi Hostility CONSTRAINT 2021:
   - Go to: https://zenodo.org/records/4459889
   - Download the zip file
   - Extract to: ~/Downloads/universal-restrictor/data/datasets/curated/raw/

3. After downloading, run the analysis script.
""")
