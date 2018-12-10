from core.processor_class import Processer
import sys
from sys import maxunicode
import unicodedata
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem.snowball import SnowballStemmer
import nltk
import joblib
stopwords_list = set(stopwords.words('dutch'))
stemmer=SnowballStemmer('dutch')
tbl = dict.fromkeys(i for i in range(maxunicode) if unicodedata.category(chr(i)).startswith('P'))
classifier = joblib.load(open('path to pickle with topic classifier', 'rb'))
vectorizer = joblib.load(open('path to pickle with vectorizer', 'rb'))

class driebijdrie_processer(Processer):
        def process(self, document_field):
            text = document_field.replace(u"`",u"").replace(u"´",u"").translate(tbl)
            text = word_tokenize(text)
            text = [stemmer.stem(w.lower()) for w in text if w.lower() not in stopwords_list and not (w.isalpha() and len(w)==1\
)]
            text_bigrams = ["_".join(tup) for tup in nltk.ngrams(text,2)]
            text_final = text + text_bigrams
            text_final = " ".join(text_final)
            tfidf_article = vectorizer.transform([text_final])[0]
            topic = classifier.predict(tfidf_article)
            topic = topic[0]
            return topic
