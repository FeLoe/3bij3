from app import dictionary, index, article_ids, db, mysql_user, mysql_password, mysql_database
from flask_login import current_user
from app.models import User, News, News_sel, Category
import random
from collections import Counter, defaultdict
from operator import itemgetter
from sqlalchemy import desc
from gensim.models import TfidfModel
from app.vars import host, indexName, es, list_of_sources
from app.vars import num_less, num_more, num_select, num_recommender
from app.vars import topicfield, textfield, teaserfield, teaseralt
from app.vars import doctypefield, classifier_dict, all_categories
import mysql.connector

connection = mysql.connector.connect(
    host = 'localhost',
    user = mysql_user,
    passwd= mysql_password,
    database = mysql_database
    )
cursor = connection.cursor(prepared = True)

class recommender():

    def __init__(self):
        self.num_less = num_less
        self.num_more = num_more
        self.num_select = num_select
        self.num_recommender = User.query.get(current_user.num_recommended)
        self.topicfield = topicfield
        self.textfield = textfield
        self.teaserfield = teaserfield
        self.teaseralt = teaseralt
        self.doctypefield = doctypefield
        self.classifier_dict = classifier_dict
        self.all_categories = all_categories


    def get_selected(self):
        user = User.query.get(current_user.id)
        selected_articles = user.selected_news.all()
        selected_ids = [a.news_id for a in selected_articles]
        docs = []
        for item in selected_ids:
            doc = es.search(index=indexName,
                body={"query":{"terms":{"_id":[item]}}}).get('hits',{}).get('hits',[""])
            for d in doc:
                docs.append(d)
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
                                  { self.doctypefield: doctype
                                  }
                              }
                          }
                      }}).get('hits',{}).get('hits',[""])
        final_docs = []
        a = ["podcast", "live"]
        for doc in docs:
            if self.textfield not in doc["_source"].keys() or (self.teaserfield not in doc["_source"].keys() and self.teaseralt not in doc["_source"].keys()) or doc['_id'] in displayed_ids or topicfield not in doc['_source'].keys():
                pass
            elif "paywall_na" in doc["_source"].keys():
                if doc["_source"]["paywall_na"] == True:
                    pass
                else:
                    if any(x in doc['_source'][self.textfield] for x in a):
                        pass
                    else:
                        final_docs.append(doc)
            elif any(x in doc["_source"][self.textfield] for x in a):
                pass
            else:
                final_docs.append(doc)
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
        The similarity coefficients should already be in the SQL database (by running the 'get_similarities' file on a regular basis) and only need to be retrieved (no calculation at this point)
        '''
        #make a query generator out of the past selected articles (using tfidf model from dictionary); retrieve the articles that are part of the index (based on article_ids)
        if None in (dictionary, index, article_ids):
            final_list = self.random_selection()
            return(final_list)

        #Get all ids of read articles of the user from the database and retrieve their similarities
        user = User.query.get(current_user.id)
        selected_articles = user.selected_news.all()
        selected_ids = [a.id for a in selected_articles]
        list_tuples = []
        cursor.execute("select * from similarities where similarities.id_old in ('%s')" % "','".join(selected_ids))
        for item in cursor:
            list_tuples.append(item)

        #make datatframe to get the three most similar articles to every read article, then select the ones that are most often in thet top 3 and retrieve those as selection
        data = pd.DataFrame(list_tuples, columns=['id', 'id2', 'url', 'similarity'])
        data['url'] = data['url'].str.decode('utf-8')
        data['similarity'] = data['similarity'].str.decode('utf-8')
        a = data.sort_values(by=['similarity'], ascending = True).groupby('id2').head(3).groupby('url').size().sort_values(ascending = False)
        recommender_ids = a.index[0, self.num_recommender]
        recommender_selection = es.search(index=indexName,
            body={"query":{"terms":{"_id":recommender_ids}}}).get('hits',{}).get('hits',[""])
        #Possibly: Weigh in the ratings for the past articles to determine which ones get "preference"
        
        #Mark the selected articles as recommended, select random articles from the non-recommended articles
        #(and get more if not enough unseen articles available), put the two lists together, randomize the ordering and return them
        num_random = self.num_select - len(recommender_selection)
        random_list = [a for a in new_articles if a["_id"] not in recommender_ids and a["_id"] not in query_ids]
        try:
            random_selection = random.sample(random_list, num_random)
            for article in random_selection:
                article['recommended'] = 0
        except ValueError:
            try:
                newtry = self.num_more
                new_articles = [self.doctype_last(s, num = newtry) for s in list_of_sources]
                new_articles = [a for b in articles for a in b]
                random_list = [a for a in new_articles if a["_id"] not in recommender_ids]
                random_selection = random.sample(random_list, num_random)
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

    def past_behavior_topic(self):
        '''
         Recommends articles based on the topics of the stories the user has selected in the past (topics indicated by classifier)
         This only works if your articles have a topic variable, otherwise it will only return random articles
        '''
        #Get the topics of the stories the user selected in the past and randomly select up to three of them
        selected_articles = self.get_selected()
        try:
            topics = [item['_source'][self.topicfield] for item in selected_articles]
        except KeyError:
            final_list = self.random_selection()
            return(final_list)
        if len(topics) >= 3:
            topic_list = random.sample(topics, 3)
        else:
            topic_list = topics
        if len(topic_list) == 1:
            num_category_select = 6
        elif len(topic_list) == 2:
            num_category_select = 3
        elif len(topic_list) == 3:
            num_category_select = 2
        else:
            num_category_select = 0

        #Retrieve new articles
        new_articles = [self.doctype_last(s) for s in list_of_sources]
        new_articles = [a for b in new_articles for a in b]

        category_selection = []
        for category in topic_list:
            topic_selection = []
            for item in new_articles:
                try:
                    if item['_source'][self.topicfield] == category:
                        topic_selection.append(item["_id"])
                except KeyError:
                    pass
            if len(topic_selection) > num_category_select:
                topic_selection = random.sample(topic_selection, num_category_select)
            for item in topic_selection:
                category_selection.append(item)
        if len(category_selection) < self.num_recommender:
            newtry = self.num_more
            new_articles = [self.doctype_last(s, num = newtry) for s in list_of_sources]
            new_articles = [a for b in new_articles for a in b]
            category_selection = []
            for category in topic_list:
                topic_selection = []
                for item in new_articles:
                    try:
                        if item['_source'][self.topicfield] == category:
                            topic_selection.append(item['_id'])
                    except KeyError:
                        pass
                    if len(topic_selection) > num_category_select:
                        topic_selection = random.sample(topic_selection, num_category_select)
                    for item in topic_selection:
                        category_selection.append(item)

      #Mark the selected articles as recommended, select random articles from the non-recommended articles (and get more if not enough unseen articles available), put the two lists together, randomize the ordering and return them
        recommender_selection = [a for a in new_articles if a["_id"] in category_selection]
        for article in recommender_selection:
            article['recommended'] = 1
        num_random = self.num_select - len(recommender_selection)
        random_list = [a for a in new_articles if a["_id"] not in category_selection]
        try:
            random_selection = random.sample(random_list, num_random)
            for article in random_selection:
                article['recommended'] = 0
        except ValueError:
            try:
                newtry = self.num_more
                articles = [self.doctype_last(s, num = newtry) for s in list_of_sources]
                all_articles = [a for b in articles for a in b]
                random_list = [a for a in all_articles if a["_id"] not in category_selection]
                random_selection = random.sample(random_list, self.num_select)
            except:
                random_selection = "not enough stories"
                return(random_selection)
        for article in random_selection:
            article['recommended'] = 0
        final_list = random_selection + recommender_selection
        final_list = random.sample(final_list, len(final_list))
        return(final_list)

    def category_selection_classifier(self):
        '''
        Uses a classifier to determine the topic categories of each article
        This only works if the articles have a topic field (past and new articles) - if one of those is not true, random articles are returned
        '''
        #Get the categories the user selected last
        categories = Category.query.filter_by(user_id = current_user.id).order_by(desc(Category.id)).first().__dict__
        sel_categories = []
        for key, value in self.all_categories.items():
            if categories[key] == 1:
                sel_categories.append(self.classifier_dict[value])
        #Retrieve new articles, make one list containing the processed texts and one of all the ids and zip them into a dict
        new_articles = [self.doctype_last(s) for s in list_of_sources]
        new_articles = [a for b in new_articles for a in b]
        #Determine how many articles per topic will be retrieved (dependent on the number of categories selected)
        selection = []
        if len(sel_categories) == 1:
            num_category_select = 6
        elif len(sel_categories) == 2:
            num_category_select = 3
        elif len(sel_categories) == 3:
            num_category_select = 2
        else:
            num_category_select = 0
        #For each selected category retrieve the articles that fit this category (and randomly select if the list is longer than needed) and fill the rest with random articles (could also be more than normally as some topics might not appear in the article selection often enough)
        category_selection = []
        for category in sel_categories:
            topic_selection = []
            for item in new_articles:
                try:
                    if item['_source'][self.topicfield] in category:
                        topic_selection.append(item["_id"])
                except KeyError:
                    pass
            if len(topic_selection) > num_category_select:
                topic_selection = random.sample(topic_selection, num_category_select)
            for item in topic_selection:
                category_selection.append(item)
        if len(category_selection) < self.num_recommender:
            newtry = self.num_more
            new_articles = [self.doctype_last(s, num = newtry) for s in list_of_sources]
            new_articles = [a for b in new_articles for a in b]
            category_selection = []
            for category in sel_categories:
                topic_selection = []
                for item in new_articles:
                    try:
                        if item['_source'][self.topicfield] in category:
                            topic_selection.append(item['_id'])
                    except KeyError:
                        pass
                    if len(topic_selection) > num_category_select:
                        topic_selection = random.sample(topic_selection, num_category_select)
                    for item in topic_selection:
                        category_selection.append(item)

        #Mark the selected articles as recommended, select random articles from the non-recommended articles (and get more if not enough unseen articles available), put the two lists together, randomize the ordering and return them
        recommender_selection = [a for a in new_articles if a["_id"] in category_selection]
        for article in recommender_selection:
            article['recommended'] = 1
        num_random = self.num_select - len(recommender_selection)
        random_list = [a for a in new_articles if a["_id"] not in category_selection]
        try:
            random_selection = random.sample(random_list, num_random)
            for article in random_selection:
                article['recommended'] = 0
        except ValueError:
            try:
                newtry = self.num_more
                articles = [self.doctype_last(s, num = newtry) for s in list_of_sources]
                all_articles = [a for b in articles for a in b]
                random_list = [a for a in all_articles if a["_id"] not in category_selection]
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
        still work in progress
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
