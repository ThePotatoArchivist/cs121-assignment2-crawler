import re
from typing import Any, Iterator
from urllib.parse import ParseResult, urljoin, urlparse
from utils.response import Response
from bs4 import BeautifulSoup

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

def possible_links(soup: BeautifulSoup) -> Iterator[Any]:
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

def links(url: str, soup: BeautifulSoup) -> Iterator[str]:
    for rawlink in possible_links(soup):
        if type(rawlink) != str: continue
        
        yield urljoin(url, rawlink)
    
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
    
    return list(links(url, BeautifulSoup(resp.raw_response.content, 'html.parser')))

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    parsed: ParseResult = urlparse(url)
    try:
        if parsed.scheme not in set(["http", "https"]):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
