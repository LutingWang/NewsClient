#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 20:49:13 2020

@author: lutingwang
"""
import math
import tkinter as tk
import tkinter.scrolledtext

import jieba
from wordcloud import WordCloud

import db


# Components

class SearchBar(tk.Frame):
    
    def __init__(self, master, onsubmit):
        super().__init__(
            master=master,
            )
        self.text = tk.StringVar()
        entry = tk.Entry(
            master=self, 
            textvariable=self.text,
            width=40,
            relief='flat',
            highlightthickness=1,
            highlightbackground='blue',
            )
        entry.grid(row=0, column=0, sticky='ns')
        tk.Button(
            master=self, 
            text="搜索", 
            command=lambda: onsubmit(self.text.get()),
            font='宋体 14 bold',
            bg='blue',
            fg='white',
            relief='flat',
            ).grid(row=0, column=1, sticky='ns')


class NewsSummary(tk.Frame):
    
    def __init__(self, master, news, align='n'):
        super().__init__(
            master=master,
            )
        title = tk.Label(
            master=self,
            text=news.title,
            font='宋体 16 bold',
            )
        title.grid(row=0, column=0, sticky=align)
        title.bind(
            '<Button-1>', 
            lambda _: master.onclick_NewsSummary(news),
            )
        caption = str(news.published_time)
        if news.author:
            caption += " 作者：" + news.author
        tk.Label(
            master=self,
            text=caption,
            ).grid(row=1, column=0, sticky=align)


class Page(tk.Frame):
    
    def __init__(self, master):
        super().__init__(
            master=master,
            )
    
    def title(self):
        raise NotImplementedError("Page is an interface.")


# Page 1

class HomePage(Page):
    
    def __init__(self, master):
        super().__init__(
            master=master,
            )
        self.gen_cloud()
        self.image_file = tk.PhotoImage(
            master=self, 
            file='./wordcloud.png',
            )
        tk.Label(
            master=self, 
            image=self.image_file, 
            width=300, 
            height=150,
            ).place(relx=0.5, rely=0.45, anchor='s')
        SearchBar(
            master=self, 
            onsubmit=lambda text: self._root().goto(NewsPage, text),
            ).place(relx=0.5, rely=0.5, anchor='n')
    
    def title(self):
        return "新浪新闻客户端"
        
    def gen_cloud(self):
        frequencies = {}
        for title in db.session.query(db.News.title).all():
            for word in jieba.cut(title[0]):
                frequencies[word] = frequencies.get(word, 0) + 1
        cloud = WordCloud(
            font_path='./simhei.ttf', 
            width=300, height=150,
            background_color='white',
            )
        cloud.generate_from_frequencies(frequencies)
        cloud.to_file('./wordcloud.png')

# Page 2

class NewsList(tk.Frame):
    NEWS_PER_PAGE = 5
    
    class _NewsPage(tk.Frame):
        
        def __init__(self, master, news_list):
            super().__init__(
                master=master,
                )
            assert 0 < len(news_list) <= NewsList.NEWS_PER_PAGE
            for news in news_list:
                NewsSummary(
                    master=self, 
                    news=news, 
                    align='w',
                    ).grid(column=0, pady=10, sticky='w')
        
        def onclick_NewsSummary(self, news):
            self._root().goto(DetailPage, news)
    
    class Footer(tk.Frame):
        
        def __init__(self, master, total_page, load_page):
            super().__init__(master)
            assert total_page > 0
            self._cur_page = tk.IntVar(master=self, value=1)
            self._total_page = total_page
            self._load_page = load_page
            self._prev_button = tk.Button(
                master=self,
                text="上一页",
                command=self.prev_page,
                state='disabled',
                )
            self._next_button = tk.Button(
                master=self,
                text="下一页",
                command=self.next_page,
                state='normal' if self._total_page > 1 else 'disabled',
                )
            self._prev_button.grid(row=0, column=0, padx=5)
            tk.Label(
                master=self, 
                text="第",
                ).grid(row=0, column=1)
            tk.Label(
                master=self, 
                textvariable=self._cur_page,
                ).grid(row=0, column=2)
            tk.Label(
                master=self, 
                text="/",
                ).grid(row=0, column=3)
            tk.Label(
                master=self, 
                text=str(total_page)
                ).grid(row=0, column=4)
            tk.Label(
                master=self, 
                text="页",
                ).grid(row=0, column=5)
            self._next_button.grid(row=0, column=6, padx=5)
        
        def prev_page(self):
            cur_page = self._cur_page.get()
            assert cur_page > 1
            self._cur_page.set(cur_page - 1)
            self._load_page(cur_page, cur_page - 1)
            self._next_button['state'] = 'normal'
            if self._cur_page.get() == 1:
                self._prev_button['state'] = 'disabled'
        
        def next_page(self):
            cur_page = self._cur_page.get()
            assert cur_page < self._total_page
            self._cur_page.set(cur_page + 1)
            self._load_page(cur_page, cur_page + 1)
            self._prev_button['state'] = 'normal'
            if self._cur_page.get() == self._total_page:
                self._next_button['state'] = 'disabled'
            
    def __init__(self, master, text):
        super().__init__(master)
        query = db.session.query(db.News)
        if text:
            query = query.filter(*[
                db.News.title.like(f'%{kwd}%') 
                for kwd in text.split()
                ])
        self._list = query.all()
        self.total_page = math.ceil(len(self._list) / self.NEWS_PER_PAGE)
        self.pages = [
            self._NewsPage(
                master=self, 
                news_list=self._list[i : (i + self.NEWS_PER_PAGE)]
                )
            for i in range(0, len(self._list), self.NEWS_PER_PAGE)
            ]
        if len(self.pages) != 0:
            self.pages[0].pack()
            self.Footer(
                master=self, 
                total_page=len(self.pages),
                load_page=self.load_page,
                ).pack(side='bottom', pady=20)
        else:
            tk.Label(master=self, text="无结果").pack()

    def load_page(self, old_ind, new_ind):
        self.pages[old_ind - 1].pack_forget()
        self.pages[new_ind - 1].pack()


class NewsPage(Page):
    
    def __init__(self, master, text):
        super().__init__(
            master=master,
            )
        self.text = text
        search = SearchBar(
            master=self, 
            onsubmit=self.refresh,
            )
        search.pack(pady=40)
        search.text.set(text)
        self._list = NewsList(
            master=self, 
            text=text,
            )
        self._list.pack()
    
    def title(self):
        if self.text:
            return "搜索结果 - " + self.text
        else:
            return "搜索结果"

    def refresh(self, text):
        self._list.destroy()
        self._list = NewsList(
            master=self, 
            text=text,
            )
        self._list.pack()
    

# Page 3

class DetailPage(Page):
    
    def __init__(self, master, news):
        super().__init__(master)
        self._title = news.title
        NewsSummary(self, news).pack(pady=40, anchor='s')
        content = tk.scrolledtext.ScrolledText(
            master=self,
            font='宋体 14',
            relief='flat',
            padx=40,
            )
        content.pack(side='right')
        with open(f'./news/{news._id}.txt', 'r', encoding='utf-8') as f:
            content.insert('end', f.read())
        content['state'] = 'disabled'
    
    def title(self):
        return self._title

    def onclick_NewsSummary(self, _):
        pass


# main window

class App(tk.Tk):
    
    def _at_home(self):
        return len(self.stack) == 0
    
    def _load_page(self, page):
        self.current_page = page
        self.current_page.pack(expand='yes', fill='both')
        self.title(self.current_page.title())
    
    def __init__(self):
        super().__init__()
        self.tk_setPalette(background='white')
        self.option_add('*Font', '宋体 12')
        self.geometry(f'960x540')
        self._go_back_button = tk.Button(
            master=self,
            text="< 返回",
            command=self.navigate_back,
            font='宋体 10',
            )
        self._go_back_button.place(relx=0, rely=0)
        self.stack = []
        self._load_page(HomePage(self))

    def goto(self, page, *args, **kwargs):
        assert issubclass(page, Page)
        self.current_page.pack_forget()
        self.stack.append(self.current_page)
        self._load_page(page(self, *args, **kwargs))
        self._go_back_button.tkraise()
    
    def navigate_back(self):
        self.current_page.destroy()
        self._load_page(self.stack.pop())
        if self._at_home():
            self.current_page.tkraise()


if __name__ == '__main__':
    App().mainloop()