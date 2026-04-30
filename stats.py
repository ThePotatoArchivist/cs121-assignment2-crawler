from dataclasses import dataclass, field
import pickle
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

WORD = re.compile(r'[A-Za-z0-9](?:[-A-Za-z0-9\']*[A-Za-z0-9])')
NUMBER = re.compile(r'\d+')

with open('stopwords.txt') as file:
    STOPWORDS = set(l.strip() for l in file)
    
@dataclass
class Stats:
    pages: int = 0
    most_words: int = 0
    most_words_url: list[str] = field(default_factory=list)
    word_counts: dict[str, int] = field(default_factory=dict)
    subdomains: dict[str, int] = field(default_factory=dict)
    
try:
    with open('stats.pickle', 'rb') as file:
        STATS = pickle.load(file)
except FileNotFoundError:
    STATS = Stats()
    
def save():
    with open('stats.pickle', 'wb') as file:
        pickle.dump(STATS, file)
        
def words(text: str):
    for match in WORD.finditer(text):
        word = match.group().lower()
        if word and word not in STOPWORDS and not NUMBER.match(word):
            yield word

def update_stats(url: str, content: str):
    soup = BeautifulSoup(content, 'html.parser')
    if not soup.body: return
    
    STATS.pages += 1

    word_count = 0
    
    for text in soup.strings:
        for word in words(text):
            word_count += 1
            try:
                STATS.word_counts[word] += 1
            except KeyError:
                STATS.word_counts[word] = 1
        
    if (word_count > STATS.most_words):
        STATS.most_words = word_count
        STATS.most_words_url = [url]
    elif (word_count == STATS.most_words):
        STATS.most_words_url.append(url)
        
    hostname = urlparse(url).hostname
    if hostname:
        try:
            STATS.subdomains[hostname] += 1
        except KeyError:
            STATS.subdomains[hostname] = 1
        
    save()

if __name__ == '__main__':
    print("Pages:", STATS.pages)
    print(f"Page(s) with most words: {', '.join(STATS.most_words_url)} ({STATS.most_words})")
    print("\nSubdomains:")
    for subdomain, count in STATS.subdomains.items():
        print(f'{subdomain}, {count}')

    print("\nTop 50 words:")
    word_counts = sorted(STATS.word_counts.items(), key = lambda item: item[1], reverse=True)
    for i in range(50):
        word, count = word_counts[i]
        print(f'{count} {word}')