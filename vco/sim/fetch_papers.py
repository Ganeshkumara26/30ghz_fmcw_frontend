import urllib.request
import json

url = 'https://api.semanticscholar.org/graph/v1/paper/search?query=30+GHz+VCO+CMOS&limit=5&fields=title,authors,year,abstract,externalIds'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        for p in data.get('data', []):
            print(f"Title: {p.get('title')}")
            authors = [a['name'] for a in p.get('authors', [])]
            print(f"Authors: {', '.join(authors)}")
            print(f"Year: {p.get('year')}")
            print(f"DOI: {p.get('externalIds', {}).get('DOI', 'None')}")
            print(f"Abstract: {p.get('abstract')}")
            print('-'*40)
except Exception as e:
    print(e)
