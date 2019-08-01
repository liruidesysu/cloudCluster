# -*- encoding: utf-8 -*-
# Copyright 2016 Vinzor Co.,Ltd.
#
# comment
#
# 7/31/19 liruide : Init

from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
