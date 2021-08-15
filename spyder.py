# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 15:03:42 2020

@author: ThinkPad
"""
from gevent import monkey; monkey.patch_all(thread=False)

from datetime import datetime
import urllib.error
import urllib.request
import hashlib

import chardet
from bs4 import BeautifulSoup
from pybloom import ScalableBloomFilter as Filter
import gevent

import db


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
        
        print(self.url)
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
            soup = BeautifulSoup(content.decode(charset), 'html.parser')
            print("Fetching succeeded")
            return soup
        except Exception as e:
            print("Unable to predict charset", e)
            return
    

class Controller:
    
    @staticmethod
    def _meta(soup, property_name):
        tag = soup.find('meta', attrs={'property': property_name})
        if tag is None: return None
        return tag.get('content')

    def __init__(self, base_url='https://news.sina.com.cn', n_news=100, n_producers=5, n_consumers=1):
        self.base_url = base_url
        self.n_news = n_news
        self.n_producers = n_producers
        self.n_consumers = n_consumers

        self.urls = gevent.queue.Queue()
        self.soups = gevent.queue.Queue(maxsize=n_producers)
        self.urls.put(URL(base_url))

        self.visited_urls = Filter(initial_capacity=n_news)
        self.news_filter = Filter(initial_capacity=n_news)

    def produce(self, id_, n_product):
        print(f"{id_}: init")
        for i in range(n_product):
            while True:
                url = self.urls.get()
                soup = url.fetch()
                if soup is not None: break
                if url.is_alive(): 
                    self.urls.put(url)
            self.soups.put(soup)
            hrefs = [
                anchor.attrs['href'] 
                for anchor in soup.select('a[href]')
                ]
            for href in hrefs:
                if href in self.visited_urls:
                    continue
                netloc = urllib.parse.urlparse(href).netloc
                if netloc.endswith('news.sina.com.cn'):
                    self.urls.put(URL(href))
                    self.visited_urls.add(href)
            print(f"{id_}: {i}/{n_product}")
        print(f"{id_}: finished")
        self.soups.put(None)
    
    def consume(self, id_):
        print(f"{id_}: init")
        remaining_producers = self.n_producers
        while True:
            soup = self.soups.get()
            while soup is None: 
                remaining_producers -= 1
                if remaining_producers == 0:
                    print(f"{id_}: finished")
                    return
                soup = self.soups.get()

            print(f"{id_}: consuming")
            if self._meta(soup, 'og:type') != 'news': continue
        
            title = self._meta(soup, 'og:title')
            md5 = hashlib.md5(title.encode('utf-8')).hexdigest()
            if md5 in self.news_filter: continue
            self.news_filter.add(md5)
        
            published_time = self._meta(soup, 'article:published_time')
            author = self._meta(soup, 'article:author')
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
    
    def run(self):
        n_product = self.n_news // self.n_producers
        rem = self.n_news % self.n_producers
        producers = [gevent.spawn(
            self.produce,
            id_=i,
            n_product=n_product + 1 if i < rem else n_product,
            ) for i in range(self.n_producers)]
        consumers = [gevent.spawn(self.consume, id_=i) for i in range(self.n_consumers)]
        gevent.joinall(producers + consumers)
    

if __name__ == '__main__':
    Controller(n_news=20).run()