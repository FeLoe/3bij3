# newsapp
Developing a news app with different recommender systems
It is recommended to use this app in a virtual environment. 
- Creating a virtual environment: python3 -m venv venv
- activating a virtual environment: source venv/bin/activate

Before running the app: 
export FLASK_APP=newsapp.py

Initializing, migrating and upgrading a sqlite database (needed for this app to work): 

flask db init
flask db migrate
flask db upgrade
