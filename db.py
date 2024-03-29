#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 26 19:01:18 2020

@author: lutingwang
"""
import os
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.orm.session import Session

Base: DeclarativeMeta = declarative_base()


class News(Base):
    __tablename__ = 'NEWS'
    
    _id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    published_time = Column(DateTime, nullable=False)
    author = Column(String)
    
    # __mapper_args__ = {
    #     'order_by': published_time.desc()
    #     }

    def __repr__(self):
        return f"<News({self._id}, {self.title})>"


__pwd = os.getcwd()
_engine = create_engine(f'sqlite:///{__pwd}/news.db', echo=True)
session: Session = sessionmaker(bind=_engine)()

if __name__ == '__main__':
    Base.metadata.create_all(_engine)