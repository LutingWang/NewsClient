# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 15:03:42 2020

@author: ThinkPad
"""
from gevent import monkey; monkey.patch_all()

from datetime import datetime
import urllib
import hashlib

import chardet
from bs4 import BeautifulSoup
from pybloom import ScalableBloomFilter as Filter
import gevent

import db

news_num = 1000


class URL:
    
    def __init__(self, url, expire=3):
        self.url = url
        self.__expire = expire
        assert(self.is_alive)
        
    def is_alive(self):
        return self.__expire > 0
    
    def fetch(self):
        if self.is_alive():
            self.__expire -= 1
        else:
            raise RuntimeError("URL is no longer alive")
        
        print(f"Fetching url '{self.url}'")
        try:
            resp = urllib.request.urlopen(self.url, timeout=5)
        except urllib.error.HTTPError as e:
            print(e.code)
            if e.code < 500:
                self.__expire = 0
            return
        except urllib.error.URLError as e:
            print(e.reason)
            self.__expire = 0
            return
        except:
            print("Unexpected error when requesting url")
            return
        
        try:
            content = resp.read()
            charset = chardet.detect(content)['encoding']
            soup = BeautifulSoup(content.decode(charset), 'lxml')
            print("Fetching succeeded")
            return soup
        except:
            print("Unable to predict charset")
            return
    

def produce(soups, base_url, n_product):
    queue = [URL(base_url)]
    visited = Filter(initial_capacity=news_num)
    for _ in range(n_product):
        while True:
            url = queue.pop(0)
            soup = url.fetch()
            if soup is not None:
                visited.add(url.url)
                break
            if url.is_alive(): 
                queue.append(url)
        soups.put(soup)
        hrefs = [
            anchor.attrs['href'] 
            for anchor in soup.select('a[href]')
            ]
        for href in hrefs:
            if href in visited:
                continue
            netloc = urllib.parse.urlparse(href).netloc
            if netloc.endswith('news.sina.com.cn'):
                queue.append(URL(href))
    soups.put(None)
    

def consume(soups):
    
    def meta(soup, property_name):
        tag = soup.find('meta', attrs={'property': property_name})
        if tag is None: return None
        return tag.get('content')
    
    filter = Filter(initial_capacity=news_num)
    while True:
        soup = soups.get()
        if soup is None: return
        
        print("Consuming soup")
        if meta(soup, 'og:type') != 'news': continue
    
        title = meta(soup, 'og:title')
        md5 = hashlib.md5(title.encode('utf-8')).hexdigest()
        if md5 in filter: continue
        filter.add(md5)
    
        published_time = meta(soup, 'article:published_time')
        author = meta(soup, 'article:author')
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


def control(n=news_num):
    soups = gevent.queue.Queue(maxsize=5)
    producer = gevent.spawn(
        produce,
        soups=soups, 
        base_url='https://news.sina.com.cn', 
        n_product=n,
        )
    consumer = gevent.spawn(
        consume,
        soups=soups,
        )
    gevent.joinall([producer, consumer])


if __name__ == '__main__':
    control(100)