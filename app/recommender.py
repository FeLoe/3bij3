from app import softcosine_model, lda_model, lda_dict
from flask_login import current_user
from app.models import User, News, News_sel, Category
from elasticsearch import Elasticsearch
import random
import gensim
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from gensim.models import Word2Vec
from gensim.similarities import SoftCosineSimilarity
from collections import Counter, defaultdict
from operator import itemgetter
from sqlalchemy import desc


host = "http://localhost:9200"
indexName = "inca"
es = Elasticsearch(host, timeout = 60)
list_of_sources = ["ad (www)", "bd (www)", "belangvanlimburg (www)", "telegraaf (www)", "volkskrant (www)", "nrc (www)", "nos (www)", "nu"]



class recommender():

    def __init__(self):
        self.num_less = 20
        self.num_more = 100
        self.num_select = 9
        self.num_recommender = 6
        self.num_random = 3

    def get_selected(self):
        user = User.query.get(current_user.id)
        selected_articles = user.selected_news.all()
        selected_ids = [a.news_id for a in selected_articles]
        docs = es.search(index=indexName,
            body={"query":{"terms":{"_id":selected_ids}}}).get('hits',{}).get('hits',[""])
        return docs
    
    def doctype_last(self, doctype, by_field = "META.ADDED", num = None):
        if num == None:
            num = self.num_less
        user = User.query.get(current_user.id)
        selected_articles = self.get_selected()
        displayed_articles = user.displayed_news.all()
        displayed_ids = [a.es_id for a in displayed_articles]
        docs = es.search(index=indexName,
                  body={
                      "sort": [
                          { by_field : {"order":"desc"}}
                          ],
                      "size":num,
                      "query": { "bool":
                          { "filter":
                              { "term":
                                  { "doctype.keyword": doctype
                                  }
                              }
                          }
                      }}).get('hits',{}).get('hits',[""])
        final_docs = []
        for doc in docs: 
            try:
                text = doc["_source"]["text"]
                teaser = doc["_source"]["teaser"]
                if doc["_id"] not in displayed_ids:
                    final_docs.append(doc)
            except KeyError:
                try:
                    text = doc["_source"]["text"] 
                    teaser = doc["_source"]["teaser_rss"]
                    final_docs.append(doc)
                except KeyError:
                        pass
        return final_docs
 
    def random_selection(self):
        """Selects a random sample of the last articles"""
        articles = [self.doctype_last(s) for s in list_of_sources] 
        all_articles = [a for b in articles for a in b]
        try: 
            random_sample = random.sample(all_articles, self.num_select)
        except ValueError:
            try:
                newtry = self.num_more
                articles = [self.doctype_last(s, num = newtry) for s in list_of_sources]
                all_articles = [a for b in articles for a in b]
                random_sample = random.sample(all_articles, self.num_select)
            except ValueError:
                random_sample = "not enough stories"
        return random_sample

    def past_behavior(self):
    
        #retrieve past articles and append their processed text to the query list
        docs = self.get_selected()
        query_list = [a for a in docs]
        query_generator = (tfidf[dictionary.doc2bow(n["_source"]["text"].split())] for n in query_list)

        #get newest articles, list ids, make corpus (+dictionary, + similarity_matrix) and finally index (against which the query is run)
        new_articles = [self.doctype_last(s) for s in list_of_sources]
        new_articles = [a for b in new_articles for a in b]
        articles_ids = [a["_id"] for a in new_articles]
        corpus = [a["_source"]["text"].split() for a in new_articles]
        dictionary = Dictionary(corpus)
        tfidf = TfidfModel(dictionary=dictionary)
        similarity_matrix = softcosine_model.wv.similarity_matrix(dictionary, tfidf)
        index = SoftCosineSimilarity(tfidf[[dictionary.doc2bow(d) for d in corpus]],similarity_matrix)  

        #Get the three most similar new articles for each past article and store their ids in a list                
        selection = []
        ids = []
        for text in query_generator:
            sims = index[text]
            dict_ids = dict(zip(sims, articles_ids))
            for i in range(3):
                selection.append(dict_ids[sims[i]])

        #Use a counter to determine the most frequently named articles and take the first ones (specified by variable)
        recommender_ids = [a for a, count in Counter(selection).most_common(self.num_recommender)]
        recommender_selection = [a for a in new_articles if a["_id"] in recommender_ids]
        num_random = self.num_select - len(recommender_selection)
        random_list = [a for a in new_articles if a["_id"] not in recommender_ids]
        random_selection = random.sample(random_list, num_random)
        final_list = recommender_selection + random_selection
        return(final_list)
 
   
    def category_selection(self): 
        categories = Category.query.filter_by(user_id = current_user.id).order_by(desc(Category.id)).first().__dict__
        category_list = ["politiek", "economie", "sport"]
        categories = [c for c in category_list if categories[c] == 1]
        if categories == None:
            categories = ["politiek", "sport"]
        new_articles = [self.doctype_last(s) for s in list_of_sources]
        new_articles = [a for b in new_articles for a in b]
        corpus = [a["_source"]["text"].split() for a in new_articles]
        article_ids = [a["_id"] for a in new_articles]
        ids_text = dict(zip(article_ids, corpus))
        topic_dictionary = defaultdict(list)
        for article_id, text in ids_text.items():
            bow = lda_dict.doc2bow(text)
            topic_per_text = lda_model.get_document_topics(bow)
            for tuple_topic in topic_per_text:
                topic_dictionary[tuple_topic[0]].append((article_id, tuple_topic[1]))
        #match topics and categories
        categories_topics = {"politiek":3, "sport":8, "economie":10}
        #IMPORTANT: SELECT HOW MANY PER CATEGORY? HOW MANY CATEGORIES DO WE HAVE? ALSO A RANDOM ELEMENT IN HERE? 
        selection = []
        if len(categories) == 1: 
            num_category_select = 6
        elif len(categories) == 2: 
            num_category_select = 3
        elif len(categories) == 3: 
            num_category_select = 2

        for category in categories:
            topic = categories_topics[category]
            list_documents = topic_dictionary[topic]
            most_selected = sorted(list_documents,key=itemgetter(1))[:num_category_select]
            for item in most_selected: 
                selection.append(item[0])
        recommender_selection = [a for a in new_articles if a["_id"] in selection]
        num_random = self.num_select - len(recommender_selection)
        random_list = [a for a in new_articles if a["_id"] not in selection]
        random_selection = random.sample(random_list, num_random)
        final_list = random_selection + recommender_selection
        return final_list
            
