#!/usr/bin/env python3                                                                                                         \


from elasticsearch import Elasticsearch
import gensim
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from gensim.models import Word2Vec
from gensim.similarities import SoftCosineSimilarity
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle

softcosine_model = gensim.models.Word2Vec.load("path to word2vecmodel")
host = "http://localhost:9200"
indexName = "inca"
es = Elasticsearch(host, timeout = 60)
list_of_sources = ["ad (www)", "bd (www)", "telegraaf (www)", "volkskrant (www)", "nu"]


def doctype_last(doctype, by_field = "META.ADDED", num = 40):
    docs = es.search(index=indexName,
            body={
                "sort": [
                    { by_field : {"order":"desc"}}],
                      "size":num,
                      "query": { "bool":
                          { "filter":
                              { "term":
                                  { "doctype": doctype
                                  }
                              }
                          }
                      }}).get('hits',{}).get('hits',[""])
    final_docs = []
    a = ["podcast", "live"]
    for doc in docs:
        if "text_njr"  not in doc["_source"].keys() or ("teaser" not in doc["_source"].keys() and "teaser_rss"  not in doc["_so\
urce"].keys()) or "topic" not in doc["_source"].keys():
            pass
        elif "paywall_na" in doc["_source"].keys():
            if doc["_source"]["paywall_na"] == True:
                pass
            elif any(x in doc["_source"]["text_njr"] for x in a):
                pass
            else:
                final_docs.append(doc)
    return final_docs

def make_matrix():
    new_articles = [doctype_last(s) for s in list_of_sources]
    new_articles = [a for b in new_articles for a in b]
    articles_ids = [a["_id"] for a in new_articles]
    corpus = [a["_source"]["text_njr"].split() for a in new_articles]
    dictionary = Dictionary(corpus)
    dictionary.save('index.dict')
    tfidf = TfidfModel(dictionary=dictionary)
    similarity_matrix = softcosine_model.wv.similarity_matrix(dictionary, tfidf)
    index = SoftCosineSimilarity(tfidf[[dictionary.doc2bow(d) for d in corpus]],similarity_matrix)
    index.save("SimIndex.index")
    with open("sim_list.txt", "wb") as fp:
        pickle.dump(articles_ids, fp)

if __name__ == '__main__':
    make_matrix()
