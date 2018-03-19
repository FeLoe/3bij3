from flask import render_template, flash, redirect, url_for, request, make_response, session
from app import app, db
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, News, News_sel, Category
from werkzeug.urls import url_parse
from app.forms import RegistrationForm, ChecklisteForm, LoginForm, SurveyForm,  ResetPasswordRequestForm, ResetPasswordForm, rating
from elasticsearch import Elasticsearch
import string
import random
import re
from app.email import send_password_reset_email
from datetime import datetime
from app.recommender import recommender
from sqlalchemy import desc

host = "http://localhost:9200"
indexName = "inca"
es = Elasticsearch(host)
rec = recommender()
day_min = 0
story_min = 0

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('newspage'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user is None or not user.check_password(form.password.data): 
            flash('Ongeldige gebruikersnaam of wachtwoord')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('newspage')
        return redirect(next_page)
    return render_template('login.html', title='Inloggen', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('newspage'))

@app.route('/consent', methods = ['GET', 'POST'])
def consent():
    return render_template('consent.html')

@app.route('/no_consent')
def no_consent():
    return render_template('no_consent.html')

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
        flash('Gefeliciteerd, u bent nu een ingeschreven gebruiker!')
        return redirect(url_for('login'))
    return render_template('register.html', title = 'Registratie', form=form)
                       
@app.route('/', methods = ['GET', 'POST'])
@app.route('/homepage', methods = ['GET', 'POST'])
@login_required 
def newspage(show_again = False):
    form = ChecklisteForm()
    if form.validate_on_submit() and request.method == 'POST' :
        sel_categories = form.data["example"]
        all_categories = ['Binnenland', 'Buitenland', 'Economie', 'Milieu', 'Wetenschap en technologie', 'Immigratie en integratie', 'Justitie en Criminaliteit', 'Sport', 'Kunst, cultuur en entertainment', 'Anders/Diversen']
        categories = []
        for category in all_categories: 
            if category in sel_categories: 
                categories.append(1)
            else:
                categories.append(0)
        category = Category(Binnenland = categories[0], Buitenland = categories[1], Economie = categories[2], Milieu = categories[3], Wetenschap = categories[4], \
Immigratie = categories[5], Justitie = categories[6], Sport = categories[7], Entertainment = categories[8], Anders = categories[9],  user_id = current_user.id)
        db.session.add(category)
        db.session.commit()  
        return redirect(url_for('newspage')) 
    elif not form.validate_on_submit() and request.method == 'POST':
        show_again = True
    results = []
    if show_again == True:
        documents = last_seen()
    elif show_again == False:
        group = current_user.group
        documents = which_recommender()
        if documents == "not enough stories":
            return render_template('no_stories_error.html')
    for result in documents:
        news_displayed = News(es_id = result["_id"], user_id = current_user.id, recommended = result['recommended'])
        db.session.add(news_displayed)
        db.session.commit()
        result["new_id"] = news_displayed.id
        result["_source"]["text_clean"] = re.sub(r'\|','', result["_source"]["text"])
        results.append(result) 
    session['start_time'] = datetime.utcnow()
    difference = time_logged_in()['difference']
    selected_news = number_read()['selected_news']
    if difference >= day_min and selected_news > story_min:
        flash('U kunt deze studie nu afsluiten en een finale vragenlijst invullen (link rechtsboven) - maar u kunt de webapp ook nog wel verder gebruiken.')   
    return render_template('newspage.html', results = results, form = form)

def which_recommender():
    group = current_user.group
    if group == 1:
        categories = Category.query.filter_by(user_id = current_user.id).order_by(desc(Category.id)).first()
        if categories == None:
            method  = rec.random_selection()
        else:
            method = rec.category_selection_classifier()
    elif group == 2:
        selected_news = number_read()['selected_news']
        if selected_news < 3:
            method = rec.random_selection()
        else:
            method = rec.past_behavior()
    elif group == 3:
        method = rec.random_selection()
    elif group == 4:
        method = rec.random_selection()
    return(method)
 
def last_seen():
    news = News.query.filter_by(user_id = current_user.id).order_by(desc(News.id)).limit(9)
    news_ids = [item.es_id for item in news]
    recommended = [item.recommended for item in news]
    id_rec = zip(news_ids, recommended)
    news_last_seen = []
    for item in id_rec:
        doc = es.search(index=indexName,
                  body={"query":{"term":{"_id":item[0]}}}).get('hits',{}).get('hits',[""])
        for text in doc:
                text['recommended'] = item[1]
                news_last_seen.append(text)
    return news_last_seen

@app.route('/detail/<id>', methods = ['GET', 'POST'])
@login_required
def show_detail(id):
     selected = News.query.filter_by(id = id).first()
     es_id = selected.es_id
     doc = es.search(index=indexName,
                  body={"query":{"term":{"_id":es_id}}}).get('hits',{}).get('hits',[""])
     for item in doc:
         text = item['_source']['text']
         if "||" in text:
             text = re.split(r'\|\|\.\|\|', text)
             text = re.split(r'\|\|\|', text[0])
             text = re.split(r'\|\|', text[1])
         else:
             text = [text]
         try: 
             teaser = item['_source']['teaser']
         except KeyError:
            teaser = item['_source']['teaser_rss']
            teaser = re.sub(r'<.*?>',' ', teaser)
         title = item['_source']['title']
         url = item['_source']['url']
         publication_date = item['_source']['publication_date']
         publication_date = datetime.strptime(publication_date, '%Y-%m-%dT%H:%M:%S') 
         try:
             for image in item['_source']['images']:
                 image_url = image['url']
         except KeyError:
             image_url = []
             image_caption = []
     form = rating()
     if request.method == 'POST' and form.validate():
         stars = request.form['rating']
         starttime= session.pop('start_time', None)
         endtime = datetime.utcnow()
         time_spent = endtime - starttime
         news_selected = News_sel(news_id = selected.es_id, user_id =current_user.id, rating = stars, 
starttime=starttime, endtime=endtime, time_spent = time_spent)
         db.session.add(news_selected)
         db.session.commit()
         return redirect(url_for('decision'))

     session['start_time'] = datetime.utcnow()
         
     return render_template('detail.html', text = text, teaser = teaser, title = title, url = url, image = image_url, time = publication_date, form = form)


@app.route('/decision', methods = ['GET', 'POST'])
@login_required
def decision():
    return render_template('decision.html')


@app.route('/reset_password_request', methods= ['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('newspage'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Controleer uw email, u hebt informatie ontvangen hoe u uw wachtwoord opnieuw kunt instellen.')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title="Wachtwoord opnieuw instellen", form=form)

@app.route('/reset_password/<token>', methods = ['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('newspage'))
    user = User.verify_reset_password_token(token)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Uw wachtwoord is opnieuw ingesteld worden.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/final_questionnaire', methods = ['GET', 'POST'])
@login_required
def final_form():
    form = SurveyForm()
    return render_template('final_questionnaire.html', form=form)

@app.context_processor
def time_logged_in():
    if current_user.is_authenticated:
        try:
            first_login = current_user.first_login
            difference_raw = datetime.utcnow() - first_login
            difference = difference_raw.days
        except:
            difference = 0
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

@app.route('/decision/popup_back')
@login_required
def popup_back():
    return render_template('information_goback.html')

@app.route('/categories/information')
@login_required
def popup_categories():
    return render_template('information_categories.html')

