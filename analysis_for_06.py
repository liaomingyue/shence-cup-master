# -*- coding: utf-8 -*-
# @Author  : liaomingyue
# @File    : analysis_for_06.py
# @Time    : 2018/12/22 17:17
import pickle
import pandas as pd
from tqdm import tqdm
from jieba.analyse import extract_tags,textrank # tf-idf
from jieba import posseg
import random
import jieba
jieba.analyse.set_stop_words('data/stop_words.txt') # 去除停用词
jieba.load_userdict('data/custom_dict.txt') # 设置词库

'''
  nr 人名 nz 其他专名 ns 地名 nt 机构团体 n 名词 l 习用语 i 成语 a 形容词 
  nrt 
  v 动词 t 时间词
'''

test_data=pd.read_csv('data/test_docs.csv')
train_data=pd.read_csv('data/new_train_docs.csv')
allow_pos={'nr':1,'nz':2,'ns':3,'nt':4,'eng':5,'n':6,'l':7,'i':8,'a':9,'nrt':10,'v':11,'t':12}
# allow_pos={'nr':1,'nz':2,'ns':3,'nt':4,'eng':5,'nrt':10}
tf_pos = ['ns', 'n', 'vn', 'nr', 'nt', 'eng', 'nrt','v','a']


def generate_name(word_tags):
    name_pos = ['ns', 'n', 'vn', 'nr', 'nt', 'eng', 'nrt']
    for word_tag in word_tags:
        if word_tag[0] == '·' or word_tag=='！':
            index = word_tags.index(word_tag)
            if (index+1)<len(word_tags):
                prefix = word_tags[index - 1]
                suffix = word_tags[index + 1]
                if prefix[1] in name_pos and suffix[1] in name_pos:
                    name = prefix[0] + word_tags[index][0] + suffix[0]
                    word_tags = word_tags[index + 2:]
                    word_tags.insert(0, (name, 'nr'))
    return word_tags


def evaluate():
    ids, titles= train_data['id'], train_data['title']
    with open('data/train_docs.pkl','rb') as in_data:
        docs=pickle.load(in_data)
    true_keywords=train_data['keyword'].apply(lambda x:x.split(','))
    labels_1 = []
    labels_2 = []
    use_idf,part_wrong= 0,0
    score=0
    for title,doc,true_keys in tqdm(zip(titles, docs,true_keywords)):
        title_keywords = []
        word_tags = [(word, pos) for word, pos in posseg.cut(title)]  # 标题
        # 判断是否存在特殊符号
        if '·' in title:
            word_tags=generate_name(word_tags)

        for word_pos in word_tags:
            if word_pos[1] in allow_pos:
                title_keywords.append(word_pos)
        title_keywords = [keyword for keyword in title_keywords if len(keyword[0]) > 1] # 长度大于1
        title_keywords = sorted(title_keywords, reverse=False, key=lambda x: (allow_pos[x[1]], -len(x[0]))) # 词性和长度排序

        if '·' in title and not title.endswith('·'):
            key_1 = title_keywords[0][0]
            key_2 = title_keywords[1][0]
            if key_1 not in true_keys or key_2 not in true_keys:
                pass
                # print("---"*100)
                # print((key_1,key_2),'--','--',true_keys,'--',title,'--',keywords,doc)

            if key_1 in true_keys:
                score+=0.5
            if key_2 in true_keys:
                score+=0.5
            labels_1.append(key_1)
            labels_2.append(key_2)
        else:
            # 使用tf-idf
            use_idf += 1
            # ---------重要文本-----
            primary_words = []
            for keyword in title_keywords:
                if keyword[1] == 'n':
                    primary_words.append(keyword[0])
                if keyword[1] in ['nr', 'nz', 'nt', 'ns']:
                    primary_words.extend([keyword[0]]*5)

            abstract_text = "".join(doc.split(' ')[:15])
            abstract_text_pos=[(word,tag) for word,tag in jieba.posseg.cut(abstract_text)]
            for word, tag in jieba.posseg.cut(abstract_text):
                if tag == 'n':
                    primary_words.append(word)
                if tag in ['nr', 'nz','ns']:
                    primary_words.extend([word]*5)
            primary_text = "".join(primary_words)
            # 拼接成最后的文本
            text=primary_text * 2 + title * 6 + " ".join(doc.split(' ')[:15]* 2)+doc
            # ---------重要文本-----

            temp_keywords = [keyword for keyword in extract_tags(text,topK=10)]
            # tfidf_word_tags=[(word,tag) for word,tag in posseg.cut(" ".join(temp_keywords))]
            key_1,key_2=temp_keywords[0],temp_keywords[1]
            labels_1.append(key_1)
            labels_2.append(key_2)

            if key_1 in true_keys:
                score += 0.5
            if key_2 in true_keys:
                score += 0.5

            if key_1 not in true_keys or key_2 not in true_keys:
                part_wrong+=1
                print("---"*100)
                print("true_key:{}".format(true_keys))
                print("title_word_tags:{} \t title:{}".format(title_keywords, title))
                print("tfidf:{}".format(temp_keywords))
                print("abstract_text=>",abstract_text,abstract_text_pos)
                print('primary_text=>',primary_text)
    data = {'id': ids,
            'label1': labels_1,
            'label2': labels_2}
    df_data = pd.DataFrame(data, columns=['id', 'label1', 'label2'])
    df_data.to_csv('result/06_train.csv', index=False)
    print("使用tf-idf提取的次数：", use_idf)
    print("预测出错的次数：",part_wrong)
    print("最终得分为：",score)


def extract_keyword_ensemble(test_data):
    ids,titles=test_data['id'],test_data['title']
    with open('data/test_doc.pkl','rb') as in_data:
        test_docs=pickle.load(in_data)
    labels_1 = []
    labels_2 = []
    use_idf=0

    for title, doc in tqdm(zip(titles, test_docs)):
        title_keywords = []
        word_tags = [(word, pos) for word, pos in posseg.cut(title)]  # 标题
        # 判断是否存在特殊符号
        if '·' in title:
            word_tags = generate_name(word_tags)

        for word_pos in word_tags:
            if word_pos[1] in allow_pos:
                title_keywords.append(word_pos)

        title_keywords = [keyword for keyword in title_keywords if len(keyword[0]) > 1]
        title_keywords = sorted(title_keywords, reverse=False, key=lambda x: (allow_pos[x[1]], -len(x[0])))
        if '·' in title :
            if len(title_keywords) >= 2:
                key_1 = title_keywords[0][0]
                key_2 = title_keywords[1][0]
            else:
                # print(keywords,title,word_tags)
                key_1 = title_keywords[0][0]
                key_2 = ''

            labels_1.append(key_1)
            labels_2.append(key_2)
        else:
            # 使用tf-idf
            use_idf += 1

            # ---------重要文本-----
            primary_words = []
            for keyword in title_keywords:
                if keyword[1] == 'n':
                    primary_words.append(keyword[0])
                if keyword[1] in ['nr', 'nz', 'nt', 'ns']:
                    primary_words.extend([keyword[0]] * len(keyword[0]))

            abstract_text = "".join(doc.split(' ')[:15])
            for word, tag in jieba.posseg.cut(abstract_text):
                if tag == 'n':
                    primary_words.append(word)
                if tag in ['nr', 'nz', 'ns']:
                    primary_words.extend([word] * len(word))
            primary_text = "".join(primary_words)
            # 拼接成最后的文本
            text = primary_text * 2 + title * 6 + " ".join(doc.split(' ')[:15] * 2) + doc
            # ---------重要文本-----

            temp_keywords = [keyword for keyword in extract_tags(text, topK=2)]
            if len(temp_keywords)>=2:
                labels_1.append(temp_keywords[0])
                labels_2.append(temp_keywords[1])
            else:
                labels_1.append(temp_keywords[0])
                labels_2.append(' ')
    data = {'id': ids,
            'label1': labels_1,
            'label2': labels_2}
    df_data = pd.DataFrame(data, columns=['id', 'label1', 'label2'])
    df_data.to_csv('result/06_jieba_ensemble.csv', index=False)
    print("使用tf-idf提取的次数：",use_idf)


if __name__ == '__main__':
    # evaluate()
    extract_keyword_ensemble(test_data)