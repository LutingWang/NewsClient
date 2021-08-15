# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 14:57:24 2020

@author: ThinkPad
"""
import db
import spyder
import app


if __name__ == '__main__':
    db.Base.metadata.create_all(db._engine)
    spyder.Controller().run()
    app.App().mainloop()