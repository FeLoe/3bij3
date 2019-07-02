'''
In this file you can specify all the variables
to customize the application.
'''

'''
ELASTICSEARCH FIELDS (examples given are from INCA database)

textfield is the elasticsearch field where the text can be found (should already be processed and tokenized)
teaserfield is the elasticsearch field where the teaser can be found
teaseralt is the elasticsearch field where an alternative teaser can be found (e.g. a rss teaser)
doctypefield is the elasticsearch field where the document type is stored
classifier_dict is the dictionary that has the results of a prediction with the topic classifier as key and the topic or topics (as list) as value
'''
topicfield = "topic"
textfield = "text"
teaserfield = "teaser"
teaseralt = "teaser_rss"
doctypefield = "doctype"
'''
ELASTICSEARCH SETUP (examples given are from INCA database)
'''
from elasticsearch import Elasticsearch
host = "http://localhost:9200"
indexName = "inca"
es = Elasticsearch(host, timeout = 60)

'''
DOCUMENT TYPES
list_of sources: Which document types do you want to use? They should be in the doctypefield you supplied
doctype_dict: How the sources will be displayed to the user
topics: whether a topic variable will be used/displayed to the user
'''
list_of_sources = ["nu", "ad (www)", "bd (www)", "telegraaf (www)", "volkskrant (www)"]
doctype_dict = {'telegraaf (www)': 'telegraaf.nl', 'ad (www)': 'ad.nl', 'nu': 'nu.nl', 'bd (www)':'bd.nl', 'volkskrkant (www)': 'volkskrant.nl'}
topics = True

'''
NUMBER OF ARTICLES AND GROUPS
num_less is the initial number of articles per source that will be scraped,
num_more is the number that will be used when running out of stories(e.g. person has already seen all the stories retrieved)
num_select is the number of stories that will be displayed to the user
num_recommender is the number of stories that will be chosen by the recommender (if applicable)
group_number is how many different groups (i.e. recommenders) do you have?
'''
num_less = 20
num_more = 200
num_select = 9
num_recommender = 6
group_number = 4

'''
REQUIREMENTS FOR FINISHING STUDY
day_min: How many days need participants to use the application 
points_min: how many points do they need to collect
'''
day_min = 10
points_min = 100

'''
TOPICS
topic_list: The different topic categories that can be displayed to the user
classifier_dict: map numbers in elasticsearch database to strings (for the topic tag)
all_categories: map topic strings to topic numbers (that are stored in the SQL database)
'''
topic_list = ["Binnenland","Buitenland", "Economie", "Milieu", "Wetenschap", "Immigratie",\
"Justitie","Sport","Entertainment","Anders"]

classifier_dict = {topic_list[0]:['13','14','20', '3', '4', '5', '6'], topic_list[1]:['16', '19', '2'],\
 topic_list[2]:['1','15'], topic_list[3]:['8', '7'],  topic_list[4]:['17'], topic_list[5]:['9'],  topic_list[6]:['12'],\
  topic_list[7]:['29'], topic_list[8]:['23'], topic_list[9]:['10','99']}

all_categories = {"topic1":topic_list[0], "topic2":topic_list[1], "topic3":topic_list[2], "topic4":topic_list[3],\
 "topic5":topic_list[4], "topic6":topic_list[5], "topic7":topic_list[6], "topic8":topic_list[7], \
 "topic9":topic_list[8], "topic10":topic_list[9]}
