from app import lda_model, cosine_model
from flask_login import current_user
from app.models import User, News, News_sel, Category
from elasticsearch import Elasticsearch
import random
import gensim
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from gensim.models import Word2Vec
from gensim.similarities import SoftCosineSimilarity


host = "http://localhost:9200"
indexName = "inca"
es = Elasticsearch(host)
num_all = 20
num_random = 3
num_recommender = 6
num_select = 9
list_of_sources = ["nu"]


class recommender():
    
    def doctype_last(doctype, by_field = "META.ADDED"):
        user = User.query.get(current_user.id)
        selected_stories = user.selected_news.all()
        selected_ids = []
        for item in selected_stories:
            selected_ids.append(item.news_id)
        docs = es.search(index=indexName,
                  body={
                      "sort": [
                          { by_field : {"order":"desc"}}
                          ],
                      "size":num_all,
                      "query": { "bool":
                          { "filter":
                              { "match":
                                  { "_type": doctype
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
 
    def random_selection():
        """Selects a random sample of the last articles of a (rss) scraper, excluding those without text or teaser"""
        all_articles = []
        for source in list_of_sources:
            articles = doctype_last(source)
            for article in articles:
                all_articles.append(article)
        random_sample = random.sample(all_articles, num_select)
        return random_list

    def past_behavior():
        #get all the stories the user has selected in the past
        user = User.query.get(current_user.id)
        selected_stories = user.selected_news.all()
        selected_ids = []
        corpus = []
    
        #use the ids of all the stories to retrieve them from the elasticsearch database and append their processed text to the corpus (the list of documents the query is run against)
        for item in selected_stories:
            selected_ids.append(item.news_id)
        docs = es.search(index=indexName,
            body={"query":{"ids"{"type":"_id", "values":selected_ids}}}).get('hits',{}).get('hits',[""])
        for doc in docs:
            corpus.append(doc["_source"]["text_njr"])
        
        #Make a dictionary out of the corpus and define a TfidfModel as well as a similarity matrix
        dictionary = Dictionary(corpus)
        tfidf = TfidfModel(dictionary=dictionary)
        similarity_matrix = cosine_model.wv.similarity_matrix(dictionary, tfidf)
        new_articles = []
        article_keys = {}

        #Get the processed text of the newest articles and store them in a list + make a dictionary that has the text as key and the id as value
        all_articles = []
        for source in list_of_sources:
            articles = doctype_last(source)
            for article in articles:
                all_articles.append(article)
        for article in all_articles: 
            new_articles.append(article["_source"]["text_njr"])
            article_keys[article["_source"]["text_njr"] = article["_id"]

        #Make a generator so that every new article can be run as query and build an index from the corpus; calculate the average similarity of every new document with all the documents selected in the past
        query_generator = (tfidf[dictionary.doc2bow(n)] for n in new_articles)
        index = SoftCosineSimilarity(
            tfidf[[dictionary.doc2bow(document) for document in corpus]],
            similarity_matrix)                       
        for text in query_generator:
            similarities_sum = 0
            all_similarities = index[text]
            for i in range(len(corpus)):
                similarities_sum.append = all_similarities[i][1]
            similarities_avg = similarities_sum / len(corpus)
            similarities_list.append((article_keys[text],similarities_avg))

        #use a dataframe to get the 6 documents with the highest average similarity
        labels = ["key", "similarity"]
        df = pd.DataFrame.from_records(similarities_list, columns=labels)
        df = df.sort(["similarity"], ascending = False)
        selection = df['key'][0:num_recommender].tolist()

        #Remove selected articles from the list of newly retrieved articles and randomly select 3 articles from that list
        recommender_selection = []
        for article in all_articles: 
            if article["_id"] in selection: 
                all_articles.remove(article)
                recommender_selection.append(article)

        random_articles = random.sample(all_articles, num_random)
        final_list = recommender_selection + random_articles
        return(random_articles)
 
   
    def category_selection():
        user = User.query.get(current_user.id)
        categories = user.categories.order_by('-id').first()
        for source in list_of_sources:
            articles = doctype_last(source)
        print(categories)
        #depending on the categories select the 6 most fitting (depends on number of categories selected!)
        # out of the others select 3 that are not in the selected ones randomly
        all_articles = []
        for source in list_of_sources:
            articles = doctype_last(source)
            for article in articles: 
                all_articles.append(article)
        for article in all_articles: 
            if article in selection: 
                all_articles.remove(article)
        random_articles = random.sample(all_articles, 3)

                         
def article_score(article, lda_model, group):
    doc = article["clean_text"]
    doc_dict = gensim.corpora.Dictionary([doc])
    doc_corp = doc_dict.doc2bow(doc)
    doc_vec = lda_model[doc_corp]
    return gensim.matutils.cossim(group_topics[group], doc_vec)

scores = []
    article_ids = []
    for article in db.rec_articles.find():
        article_ids.append(article["id"])
        if group != -1:
            scores.append(article_score(article, lda_model, group))    
    sorted_idx = np.argsort(-np.array(scores))[:]
    rec_list = []
    score_list = []
    for i in sorted_idx:
        rec_list.append(article_ids[i])
        score_list.append(scores[i])
    return rec_list, score_list
