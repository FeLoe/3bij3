#!/usr/bin/env python3

from elasticsearch import Elasticsearch
import gensim
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from gensim.models import Word2Vec
from gensim.similarities import SoftCosineSimilarity
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import mysql.connector
from itertools import chain

softcosine_model = gensim.models.Word2Vec.load("/mnt/data/word2vec/w2v_model_nr_0_window_5_size_100_negsample_5")
print("loaded model")
host = "http://localhost:9200"
indexName = "inca"
es = Elasticsearch(host, timeout = 60)
connection = mysql.connector.connect(
    host = 'localhost',
    user = '',
    passwd= '',
    database = ''
    )
cursor = connection.cursor(prepared = True)

cursor.execute('SELECT distinct news_id, id from news_sel')
all_ids = []
all_numbers = []
for item in cursor:
    all_ids.append(item[0].decode('utf-8'))
    all_numbers.append(item[1])    

ids_dict = dict(zip(all_ids, all_numbers))
all_ids = [ all_ids[i:i+1000] for i in range(0, len(all_ids), 1000) ]

cursor.execute('select distinct all_news.id from all_news where not exists (select similarities.id_new from similarities where similarities.id_new = all_news.id)')
new_ids = [item[0].decode('utf-8') for item in cursor]
new_ids = [ new_ids[i:i+1000] for i in range(0, len(new_ids), 1000) ]

new_articles = []
for chunk in new_ids: 
    n = [doc for doc in es.search(index=indexName, body={"query":{"ids":{"values":chunk}}}, size = 1000).get('hits',{}).get('hits',[""]) if 'text_njr' in doc['_source'].keys()]
    new_articles.append(n)
new_articles = list(chain.from_iterable(new_articles))

old_articles = []
for chunk in all_ids:
    n = [doc for doc in es.search(index=indexName, body={"query":{"ids":{"values":chunk}}}, size = 1000).get('hits',{}).get('hits',[""])  if 'text_njr' in doc['_source'].keys()]
    old_articles.append(n)
old_articles = list(chain.from_iterable(old_articles))


new_text = [doc['_source']['text_njr'].split() for doc in new_articles]
old_text = [doc['_source']['text_njr'].split() for doc in old_articles]
new_ids = [doc['_id'] for doc in new_articles]
old_ids = [doc['_id'] for doc in old_articles]
table_ids = [ids_dict[i] for i in old_ids]

dictionary = Dictionary(new_text + old_text)
tfidf = TfidfModel(dictionary=dictionary)
similarity_matrix = softcosine_model.wv.similarity_matrix(dictionary, tfidf)

corpus = [dictionary.doc2bow(d) for d in new_text]

query =	tfidf[[dictionary.doc2bow(d) for d in old_text]]
index =	SoftCosineSimilarity(tfidf[[dictionary.doc2bow(d) for d in new_text]], similarity_matrix)
sims = index[query]

df = pd.DataFrame(sims, columns = new_ids, index = table_ids).stack().reset_index()
df.columns = ['source', 'target', 'similarity']
subset = df[['source', 'target', 'similarity']]
tuples = [tuple(x) for x in subset.values]
try: 
    sql_insert_query = """ insert into similarities (id_old, id_new, similarity) values (%s, %s, %s) """
    cursor.executemany(sql_insert_query, tuples)
    connection.commit()
    print(cursor.rowcount, "Record inserted successfully into similarities table")
except mysql.connector.Error as error:
    print("Failed inserting record into similarities table {}".format(error))
