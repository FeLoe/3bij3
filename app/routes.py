from flask import render_template, flash, redirect, url_for, request
from app import app, db
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, News, News_sel, Category
from werkzeug.urls import url_parse
from app.forms import RegistrationForm, ChecklisteForm, LoginForm, ResetPasswordRequestForm, ResetPasswordForm
from elasticsearch import Elasticsearch
import string
import random
import re
from app.email import send_password_reset_email
from datetime import datetime


host = "http://localhost:9200"
indexName = "inca"
es = Elasticsearch(host)

list_of_sources = ["nu"]


@app.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('newspage'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user is None or not user.check_password(form.password.data): 
            flash('Ungültiger Nutzername oder Passwort')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('newspage')
        return redirect(next_page)
    return render_template('login.html', title='Anmelden', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('newspage'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('newspage'))
    form = RegistrationForm()
    if form.validate_on_submit():
        group = random.randint(1,4)
        user = User(username=form.username.data, email=form.email.data, group = group)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Glückwunsch, Sie sind nun ein registrierter Nutzer!')
        return redirect(url_for('login'))
    return render_template('register.html', title = 'Registrieren', form=form)
                       
@app.route('/', methods = ['GET', 'POST'])
@app.route('/homepage', methods = ['GET', 'POST'])
@login_required
#def which_recommender():
#have the output of the three recommender systems and choose depending on the group 
#still to do: based on past behavior and based on category selection
#already: random (can be used for two groups) 

 
def newspage():
    results_dict=random_selection()
    results = []
    for source in results_dict:
        for result in source:
            news_displayed = News(es_id = result["_id"], user_id = current_user.id)
            db.session.add(news_displayed)
            db.session.commit()
            result["new_id"] = news_displayed.id
            results.append(result)
    form = ChecklisteForm()
    difference = time_logged_in()['difference']
    selected_news = number_read()['selected_news']
    if difference == 0 and selected_news > 0:
        flash('Sie können die Studie jetzt beenden und einen finalen Fragebogen ausfüllen (Link rechts oben). Sie können die App aber auch gerne noch weiter benutzen.')
    if form.validate_on_submit():
        sel_categories = form.data["example"]
        all_categories = ["Sport", "Wirtschaft", "Politik"]
        categories_dict = {}
        for category in all_categories: 
            if category in sel_categories: 
                categories_dict[category] = 1
            else:
                categories_dict[category] = 0
        category = Category(Sport = categories_dict["Sport"], Wirtschaft = categories_dict["Wirtschaft"], \
                   Politik = categories_dict["Politik"], user_id = current_user.id)
        db.session.add(category)
        db.session.commit()  
        return redirect(url_for('newspage')) 
    return render_template('newspage.html', results = results, form = form, title = 'Kategorien')

def doctype_last(doctype, num=20, by_field = "META.ADDED", query = None):
    body = {
        "sort": [
            {by_field : {"order":"desc"}}
            ],
        "size":num,
        "query":
        {"match":
         {"doctype":
          doctype
         }
        }}
    if query:
        _logger.debug("adding string query: {query}".format(**locals()))
        body['query'] = {'query_string':{'query': query}}

    docs = es.search(index=indexName,
                  body={
                      "sort": [
                          { by_field : {"order":"desc"}}
                          ],
                      "size":num,
                      "query": { "bool":
                          { "filter":
                              { "match":
                                  { "_type": doctype
                                  }
                              }
                          }
                      }}).get('hits',{}).get('hits',[""])
    return docs

def random_selection(num_select = 9):
    """Selects a random sample of the last articles of a (rss) scraper, excluding those without text or teaser"""
    for source in list_of_sources:
        random_list = []
        articles = doctype_last(source)
        for article in articles: 
            try: 
            	if (article["_source"]["text"] == "") or (article["_source"]["teaser"] == ""):
                    articles.remove(article)
            except KeyError:
                articles.remove(article)
        random_sample = random.sample(articles, num_select)
        random_list.append(random_sample)
    return random_list

@app.route('/detail/<id>', methods = ['GET', 'POST'])
@login_required
def show_detail(id):
     selected = News.query.filter_by(id = id).first()
     es_id = selected.es_id
     doc = es.search(index=indexName,
                  body={"query":{"term":{"_id":es_id}}}).get('hits',{}).get('hits',[""])
     for item in doc: 
         text = item['_source']['text']
         teaser = item['_source']['teaser']
         title = item['_source']['title']
         url = item['_source']['url']
         try:
             for image in item['_source']['images']:
                 image_url = image['url']
                 image_caption = image['alt']
         except KeyError:
             image_url = []
             image_caption = []
         news_selected = News_sel(news_id = selected.es_id, user_id =current_user.id)
         db.session.add(news_selected)
         db.session.commit()
     return render_template('detail.html', text = text, teaser = teaser, title = title, url = url, image = image_url, image_caption = image_caption)

@app.route('/reset_password_request', methods= ['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('newspage'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Schauen Sie in ihren Emails nach Anweisungen, wie sie ihr Passwort zurücksetzen können')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title="Passwort zurücksetzen", form=form)

@app.route('/reset_password/<token>', methods = ['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('newspage'))
    user = User.verify_reset_password_token(token)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Ihr Passwort wurde zurückgesetzt.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/final_questionnaire', methods = ['GET', 'POST'])
@login_required
def final_form():
    return render_template('final_questionnaire.html')

@app.context_processor
def time_logged_in():
    if current_user.is_authenticated:
        first_login = current_user.first_login
        difference_raw = datetime.utcnow() - first_login
        difference = difference_raw.days
    else: 
        difference = 0
    return dict(difference = difference)

@app.context_processor
def number_read():
    if current_user.is_authenticated:
        try:
            selected_news = News_sel.query.filter_by(user_id = current_user.id).all()
            selected_news = len(selected_news)
        except: 
            selected_news = 0
    else:
        selected_news = 0
    return dict(selected_news = selected_news)