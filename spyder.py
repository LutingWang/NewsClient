# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 15:03:42 2020

@author: ThinkPad
"""
from datetime import datetime
import urllib
import hashlib

from bs4 import BeautifulSoup
from pybloom import ScalableBloomFilter as Filter

import db


class URL:
    def __init__(self, url, expire=3):
        self.url = url
        self.__expire = expire
        assert(self.is_alive)
        
    def is_alive(self):
        return self.__expire > 0
    
    def refresh(self):
        if self.is_alive():
            self.__expire -= 1
        else:
            raise RuntimeError("URL is no longer alive")
    
    def fetch(self):
        print(f"Fetching url '{self.url}'")
        try:
            resp = urllib.request.urlopen(self.url, timeout=5)
            soup = BeautifulSoup(resp.read().decode('utf-8'), 'lxml')
            print("Fetching succeeded")
            return soup
        except:
            print("Fetching failed")
            return
    
    
class URLPool:
    
    def __init__(self, base_url, initial_capacity):
        self._queue = [URL(base_url)]
        self._visited = Filter(initial_capacity=initial_capacity)
        
    def pop(self):
        while True:
            url = self._queue.pop(0)
            soup = url.fetch()
            if soup is not None:
                self._visited.add(url.url)
                break
            url.refresh()
            if url.is_alive(): 
                self._queue.append(url)
        hrefs = [anchor.attrs['href'] for anchor in soup.select('a[href]')]
        for href in hrefs:
            if href in self._visited:
                continue
            netloc = urllib.parse.urlparse(href).netloc
            if not netloc.endswith('news.sina.com.cn'):
                continue
            self._queue.append(URL(href))
        return soup
    

def parse_news(soup):
    
    def meta(property_name):
        tag = soup.find('meta', attrs={'property': property_name})
        if tag is None: return None
        return tag.get('content')
    
    _type = meta('og:type')
    if _type != 'news':
        return
    
    title = meta('og:title')
    md5 = hashlib.md5(title.encode('utf-8')).hexdigest()
    if md5 in parse_news.filter:
        return
    parse_news.filter.add(md5)
    
    published_time = meta('article:published_time')
    author = meta('article:author')
    news = db.News(
        title=title, 
        published_time=datetime.strptime(
            published_time[:-6], 
            '%Y-%m-%dT%H:%M:%S',
            ), 
        author=author,
        )
    db.session.add(news)
    db.session.commit()
    
    article = soup.select('div#article')[0]
    content = '\r\n'.join([p.get_text() for p in article.find_all('p')])
    with open(f'./news/{news._id}.txt', 'w', encoding='utf-8') as f:
        f.write(content)


def run(n=1000):
    pool = URLPool('https://news.sina.com.cn', initial_capacity=n)
    parse_news.filter = Filter(initial_capacity=n)
    for _ in range(n):
        soup = pool.pop()
        parse_news(soup)


if __name__ == '__main__':
    run(100)