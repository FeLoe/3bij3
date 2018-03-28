from app import classifier, vectorizer, dictionary, index, article_ids
from flask_login import current_user
from app.models import User, News, News_sel, Category
from elasticsearch import Elasticsearch
import random
from collections import Counter, defaultdict
from operator import itemgetter
from sqlalchemy import desc
from sklearn.feature_extraction.text import TfidfVectorizer
import logging
from gensim.models import TfidfModel

#Connect with elasticsearch, specify the name of the index and the sources that should be included

logger = logging.getLogger(__name__)

host = "http://localhost:9200"
indexName = "inca"
es = Elasticsearch(host, timeout = 60)
list_of_sources = ["ad (www)", "bd (www)", "telegraaf (www)", "volkskrant (www)", "nu"]

class recommender():

    def __init__(self):
        '''
        num_less is the initial number of articles per source that will be scraped, 
        num_more is the number that will be used when running out of stories(e.g. person has already seen all the stories retrieved)
        num_select is the number of stories that will be displayed to the user
        num_recommender is the number of stories that will be chosen by the recommender (if applicable)
        textfield is the elasticsearch field where the text can be found (should already be processed and tokenized)
        teaserfield is the elasticsearch field where the teaser can be found
        teaseralt is the elasticsearch field where an alternative teaser can be found (e.g. a rss teaser)
        classifier_dict is the dictionary that has the results of a prediction with the topic classifier as key and the topic or topics (as list) as value
        ''' 
        self.num_less = 20
        self.num_more = 100
        self.num_select = 9
        self.num_recommender = 6
        self.topictextfield = "text_processed"
        self.textfield = "text_njr"
        self.teaserfield = "teaser"
        self.teaseralt = "teaser_rss"
        self.classifier_dict = {'Binnenland':['13','14','20', '3', '4', '5', '6'], 'Buitenland':['16', '19', '2'], 'Economie':['1','15'], 'Milieu':['8', '7'],  'Wetenschap':['17'], 'Immigratie':['9'],  'Justitie':['12'], 'Sport':['29'], 'Entertainment':['23'], 'Anders':['10','99']}

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
        displayed_ids = [a.elasticsearch for a in displayed_articles]
        docs = es.search(index=indexName,
                  body={
                      "sort": [
                          { by_field : {"order":"desc"}}
                          ],
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
        logger.debug(docs)
        for doc in docs: 
            try:
                text = doc["_source"][self.textfield]
                teaser = doc["_source"][self.teaserfield]
                if doc["_id"] not in displayed_ids:
                    final_docs.append(doc)
            except KeyError:
                try:
                    text = doc["_source"][self.textfield] 
                    teaser = doc["_source"][self.teaseralt]
                    if doc["_id"] not in displayed_ids:
                        final_docs.append(doc)
                except KeyError:
                        pass
        return final_docs
 
    def random_selection(self):
        '''Selects a random sample of the last articles'''
        articles = [self.doctype_last(s) for s in list_of_sources] 
        all_articles = [a for b in articles for a in b]
        try: 
            random_sample = random.sample(all_articles, self.num_select)
            for article in random_sample:
                article['recommended'] = 0
        except ValueError:
            try:
                newtry = self.num_more
                articles = [self.doctype_last(s, num = newtry) for s in list_of_sources]
                all_articles = [a for b in articles for a in b]
                random_sample = random.sample(all_articles, self.num_select)
                for article in random_sample:
                    article['recommended'] = 0
            except ValueError:
                random_sample = "not enough stories"
        return random_sample

    def past_behavior(self):
        '''
        Recommends articles based on the stories the user has selected in the past, using SoftCosineSimilarity
        '''
        #get newest articles, list ids, make corpus (+dictionary, + similarity_matrix) and finally index (against which the query is run)
        tfidf = TfidfModel(dictionary=dictionary)
        docs = self.get_selected()
        query_list = [a for a in docs]
        query_ids = [a['_id'] for a in query_list]
        query_generator = [tfidf[dictionary.doc2bow(n['_source'][self.textfield].split())] for n in query_list]
        query_generator = (item for item in query_generator)
        new_articles = es.search(index=indexName,
            body={"query":{"terms":{"_id":article_ids}}}).get('hits',{}).get('hits',[""])                        
        #Get the three most similar new articles for each past article and store their ids in a list                
        selection = []
        ids = []
        for text in query_generator:
            sims = index[text]
            sims_ids = list(zip(sims, article_ids))
            sims_ids = [n for n in sims_ids if n[1] not in query_ids]
            new_sims_ids = [n[1] for n in sims_ids]
            sims_ids = sorted(enumerate(sims_ids), key=lambda item: -item[0])
            for i in range(3):
                selection.append(sims_ids[i][1])
        #Use a counter to determine the most frequently named articles and take the first ones (specified by variable)
        recommender_ids = [a for a, count in Counter(selection).most_common(self.num_recommender)]
        recommender_selection = [a for a in new_articles if a["_id"] in recommender_ids]
        #Mark the selected articles as recommended, select random articles from the non-recommended articles (and get more if not enough unseen articles available), put the two lists together, randomize the ordering and return them 
        num_random = self.num_select - len(recommender_selection)
        random_list = [a for a in new_articles if a["_id"] not in recommender_ids and a["_id"] not in query_ids]             
        try:
            random_selection = random.sample(random_list, num_random)
            for article in random_selection:
                article['recommended'] = 0
        except ValueError:
            try:
                newtry = self.num_more
                articles = [self.doctype_last(s, num = newtry) for s in list_of_sources]
                all_articles = [a for b in articles for a in b]
                random_list = [a for a in all_articles if a["_id"] not in recommender_ids] 
                random_selection = random.sample(random_list, self.num_select)
            except:
                random_selection = "not enough stories"
                return(random_selection)
        for article in random_selection:
            article['recommended'] = 0
        for article in recommender_selection:
            article['recommended'] = 1
        final_list = recommender_selection + random_selection
        final_list = random.sample(final_list, len(final_list))
        return(final_list)
 
    def category_selection_classifier(self):
        '''
        Uses a classifier to determine the topic categories of each article
        '''
        #Get the categories the user selected last
        categories = Category.query.filter_by(user_id = current_user.id).order_by(desc(Category.id)).first().__dict__
        categories = [c for c in self.classifier_dict.keys() if categories[c] == 1]
        #Retrieve new articles, make one list containing the processed texts and one of all the ids and zip them into a dict
        new_articles = [self.doctype_last(s) for s in list_of_sources]
        new_articles = [a for b in new_articles for a in b]
        texts = [' '.join(a["_source"][self.topictextfield]) for a in new_articles]
        article_ids = [a["_id"] for a in new_articles]

        #Determine the article topic (or topics) by vectorizing the article (tfidf), predicting the topic with the classifier and putting the article id and the category (retrieved by looking up the topic in the classifier_dict) in a tuple, appending it to the overall list
        article_topic = []
        tfidf_articles = vectorizer.transform(texts)
        topics = classifier.predict(tfidf_articles)
        topic_category = []
        for key, value in self.classifier_dict.items():
            for t in topics:
                if t in value:   
                    topic_category.append(key)       
        article_topic = zip(article_ids, topic_category)
            
        #Determine how many articles per topic will be retrieved (dependent on the number of categories selected) 
        selection = []
        if len(categories) == 1: 
            num_category_select = 6
        elif len(categories) == 2: 
            num_category_select = 3
        elif len(categories) == 3: 
            num_category_select = 2

        #For each selected category retrieve the articles that fit this category (and randomly select if the list is longer than needed) and fill the rest with random articles (could also be more than normally as some topics might not appear in the article selection often enough)
        for category in categories:
            category_selection = []
            for item in article_topic:
                if category in item[1]:
                    category_selection.append(item[0])
            if len(category_selection) > num_category_select:
                category_selection = random.sample(category_selection, num_category_select)
            for a_id in category_selection:
                selection.append(a_id)

        #Mark the selected articles as recommended, select random articles from the non-recommended articles (and get more if not enough unseen articles available), put the two lists together, randomize the ordering and return them        
        recommender_selection = [a for a in new_articles if a["_id"] in selection]
        for article in recommender_selection:
            article['recommended'] = 1
        num_random = self.num_select - len(recommender_selection)
        random_list = [a for a in new_articles if a["_id"] not in selection]
        try:
            random_selection = random.sample(random_list, num_random)
            for article in random_selection:
                article['recommended'] = 0
        except ValueError:
            try:
                newtry = self.num_more
                articles = [self.doctype_last(s, num = newtry) for s in list_of_sources]
                all_articles = [a for b in articles for a in b]
                random_list = [a for a in all_articles if a["_id"] not in recommender_ids] 
                random_selection = random.sample(random_list, self.num_select)
            except:
                random_selection = "not enough stories"
                return(random_selection)
        for article in random_selection:
            article['recommended'] = 0
        final_list = random_selection + recommender_selection
        final_list = random.sample(final_list, len(final_list))
        return(final_list)


    def category_selection_lda(self):
        '''
        Uses an lda model to determine which articles fit the selected topic categories best
        '''
        #Get the categories the user selected last
        categories = Category.query.filter_by(user_id = current_user.id).order_by(desc(Category.id)).first().__dict__
        
        #Retrieve the numbers the selected categories have in the lda model
        categories = [c for c in self.classifier_dict.keys() if categories[c] == 1]
        
        #Retrieve new articles, build one corpus (containing the processed texts) and a list of all the ids and zip them into a dict
        new_articles = [self.doctype_last(s) for s in list_of_sources]
        new_articles = [a for b in new_articles for a in b]
        corpus = [a["_source"][self.textfield] for a in new_articles]
        lda_dict = Dictionary(corpus)
        article_ids = [a["_id"] for a in new_articles]
        ids_text = dict(zip(article_ids, corpus))
        
        #Make one dictionary that has all the topics as keys and a list of tuples (article id and degree of match with the topic) as values
        topic_dictionary = defaultdict(list)
        for article_id, text in ids_text.items():
            bow = lda_dict.doc2bow(text)
            topic_per_text = lda_model.get_document_topics(bow)
            for tuple_topic in topic_per_text:
                topic_dictionary[tuple_topic[0]].append((article_id, tuple_topic[1]))
                
        #Determine how many articles per topic will be retrieved (dependent on the number of categories selected)        
        selection = []
        if len(categories) == 1: 
            num_category_select = 6
        elif len(categories) == 2: 
            num_category_select = 3
        elif len(categories) == 3: 
            num_category_select = 2
            
        #Find the most fitting articles for each selected category by retrieving the list of tuples for the category sorting it by degree of match, taking the most fitting (number depending on number of selected categories) and appending it to the overall selection
        for category in categories:
            list_documents = topic_dictionary[category]
            most_selected = sorted(list_documents,key=itemgetter(1))[:num_category_select]
            for item in most_selected: 
                selection.append(item[0])

        #Mark the selected articles as recommended, select random articles from the non-recommended articles (and get more if not enough unseen articles available), put the two lists together, randomize the ordering and return them 
        recommender_selection = [a for a in new_articles if a["_id"] in selection]
        for article in recommender_selection:
            article['recommended'] = 1
        num_random = self.num_select - len(recommender_selection)
        random_list = [a for a in new_articles if a["_id"] not in selection]
        try:
            random_selection = random.sample(random_list, num_random)
            for article in random_selection:
                article['recommended'] = 0
        except ValueError:
            try:
                newtry = self.num_more
                articles = [self.doctype_last(s, num = newtry) for s in list_of_sources]
                all_articles = [a for b in articles for a in b]
                random_list = [a for a in all_articles if a["_id"] not in recommender_ids] 
                random_selection = random.sample(random_list, self.num_select)
            except:
                random_selection = "not enough stories"
                return(random_selection)
        for article in random_selection:
            article['recommended'] = 0
        final_list = random_selection + recommender_selection
        final_list = random.sample(final_list, len(final_list))
        return final_list
            
