# 3bij3 - A framework for testing recommender systems and their effects

# How to use it
(instructions work for MacOS and Linux systems, not tested on Windows yet)

To use the app, you need all the packages listed in the requirements (you can install them with sudo pip3 install -r Requirements). The way it is set up now you need an Elasticsearch database for storing the news content you want to show to the user and an MySQL or SQLite database for storing the results. 

It is recommended to use this app in a virtual environment. 
- Creating a virtual environment: python3 -m venv venv
- activating a virtual environment: source venv/bin/activate

Before running the app: 
export FLASK_APP=3bij3.py

Initializing, migrating and upgrading a sqlite database (needed for this app to work): 

flask db init

flask db migrate

flask db upgrade

To finally start the app, type "flask run", it can the be found in the browser under localhost:5000
