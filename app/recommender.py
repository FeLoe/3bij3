from app import softcosine_model
from flask_login import current_user
from app.models import User, News, News_sel, Category
from elasticsearch import Elasticsearch
import random
import gensim
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from gensim.models import Word2Vec
from gensim.similarities import SoftCosineSimilarity
from collections import Counter


host = "http://localhost:9200"
indexName = "inca"
es = Elasticsearch(host)
list_of_sources = ["nu"]


class recommender():

    def get_selected(self):
        user = User.query.get(current_user.id)
        selected_stories = user.selected_news.all()
        selected_ids = [a.news_id for a in selected_stories]
        docs = es.search(index=indexName,
            body={"query":{"terms":{"_id":selected_ids}}}).get('hits',{}).get('hits',[""])
        return docs
        
    def doctype_last(self, doctype, by_field = "META.ADDED", num_all = 20):
        selected = self.get_selected()
        selected_ids = [a["_id"] for a in selected]
        docs = es.search(index=indexName,
                  body={
                      "sort": [
                          { by_field : {"order":"desc"}}
                          ],
                      "size":num_all,
                      "query": { "bool":
                          { "filter":
                              { "term":
                                  { "doctype.keyword": doctype
                                  }
                              }
                          }
                      }}).get('hits',{}).get('hits',[""])
        for doc in docs: 
            try: 
                if (doc["_source"]["text"] == "") or (doc["_source"]["teaser"] == "") or (doc["_id"] in selected_ids):
                    docs.remove(doc)
            except KeyError:
                docs.remove(doc)
        return docs
 
    def random_selection(self, num_select = 9):
        """Selects a random sample of the last articles"""
        articles = [self.doctype_last(s) for s in list_of_sources]
        all_articles = [a for b in articles for a in b]
        random_sample = random.sample(all_articles, num_select)
        return random_sample

    def past_behavior(self, num_random = 3, num_recommender = 6):
    
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
        recommender_ids = [a for a, count in Counter(selection).most_common(num_recommender)]
        recommender_selection = [a for a in new_articles if a["_id"] in recommender_ids]
        random_list = [a for a in new_articles if a["_id"] not in recommender_ids]
        random_selection = random.sample(random_list, num_random)
        final_list = recommender_selection + random_selection
        return(final_list)
 
   
    def category_selection(self):
        categories = current_user.categories.order_by('-id').first()
        print(categories)
        #depending on the categories select the 6 most fitting (depends on number of categories selected!)
	#doc = article["clean_text"]
	#doc_dict = gensim.corpora.Dictionary([doc])
	#doc_corp = doc_dict.doc2bow(doc)
	#doc_vec = lda_model[doc_corp]
	#return gensim.matutils.cossim(group_topics[group], doc_vec)
	#scores = []
    	#article_ids = []
    	#for article in db.rec_articles.find():
        #article_ids.append(article["id"])
        #if group != -1:
        #scores.append(article_score(article, lda_model, group))    
    	#sorted_idx = np.argsort(-np.array(scores))[:]
    	#rec_list = []
    	#score_list = []
    	#for i in sorted_idx:
        #rec_list.append(article_ids[i])
        #score_list.append(scores[i])
    	#return rec_list, score_list
