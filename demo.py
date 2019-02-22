# -*- coding: utf-8 -*-
# @Author  : liaomingyue
# @File    : demo.py
# @Time    : 2018/12/01 17:17
import jieba
jieba.load_userdict('data/demo.txt')

for word in jieba.cut('以色列歼-20战机首次参与实战,'):
    print(word)