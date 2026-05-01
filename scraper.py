import re
from typing import Any, Iterator
from urllib.parse import ParseResult, urldefrag, urljoin, urlparse, urlunparse
from stats import update_stats
from utils.response import Response
from bs4 import BeautifulSoup
import json

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

# link.href
# iframe.src
# meta.content[]
# a.href
# form.action
# *.src
# !img.src
# *.href
# !

# based on https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
meta_url = re.compile(r'(https?:\/\/|\/)[-a-zA-Z0-9()@:%_\+.~#?&/=]*$')
url_match = re.compile(r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&/=]*)$')

def soup_possible_links(soup: BeautifulSoup) -> Iterator[Any]:
    for element in soup.find_all():
        if element.has_attr('src'):
            yield element['src']

        if element.has_attr('href'):
            yield element['href']

        if element.name == 'meta' and element.has_attr('content'):
            content = element['content']
            if (type(content) is str and meta_url.match(content)):
                yield content

        if element.name == 'form' and element.has_attr('form'):
            yield element['action']

def soup_links(soup: BeautifulSoup) -> Iterator[str]:
    for rawlink in soup_possible_links(soup):
        if type(rawlink) == str:
            yield rawlink

def try_extract_soup(content: str, full_doc: bool = False) -> Iterator[str]:
    soup = BeautifulSoup(content, 'html.parser')
    if (soup.body or not full_doc and soup.find()):
        yield from soup_links(soup)
    
def json_links(json_obj: Any) -> Iterator[str]:
    if type(json_obj) is str:
        if url_match.match(json_obj):
            yield json_obj
        yield from try_extract_soup(json_obj)
        return

    if type(json_obj) is dict:
        for value in json_obj.values():
            yield from json_links(value)
        
    if type(json_obj) is list:
        for value in json_obj:
            yield from json_links(value)
            
def filter_valid(base: str, rawlinks: Iterator[str]):
    for rawlink in rawlinks:
        scheme, netloc, path, params, query, _ = urlparse(urljoin(base, rawlink))
        url = urlunparse((
            scheme,
            netloc,
            path,
            params,
            # special case: query params are rarely for different pages except on the root page
            query if path == "/" or path == "" or path.startswith("/wp-json") else None,
            None # discard fragment
        ))

        if is_valid(url):
            yield url

def try_extract_links(content: str):
    try:
        json_obj = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    else:
        yield from json_links(json_obj)
        return
    
    yield from try_extract_soup(content, full_doc = True)
    
def extract_next_links(url: str, resp: Response) -> list[str]:
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    if (resp.status != 200):
        return []
    
    if (resp.raw_response is None):
        print("Response was None")
        return []

    update_stats(url, resp.raw_response.content)

    return list(filter_valid(url, try_extract_links(resp.raw_response.content)))

allowed_domains = re.compile(r'.*\.(ics|cs|informatics|stat)\.uci\.edu$')

def is_valid(url: str):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    parsed: ParseResult = urlparse(url)
    try:
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        if not allowed_domains.match(parsed.hostname or ""):
            return False
        
        # special case: events pages are 1-per-day and don't contain any information
        if re.match(r'/events/', parsed.path):
            return False

        # special case: wiki pages are many and inaccessible
        if parsed.path.startswith("/doku.php"):
            return False
        
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico|svg"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False
        
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
