# 3bij3 - A framework for testing recommender systems and their effects

# How to use it
(instructions work for MacOS and Linux systems, not tested on Windows yet)

It is recommended to use this app in a virtual environment. 
- Creating a virtual environment: python3 -m venv venv
- activating a virtual environment: source venv/bin/activate

To use the app, you need all the packages listed in the requirements (you can install them with pip3 install -r requirements.txt). 

*Note: You might run into some issues regarding the mysqlclient package. On MacOS you can either use [this solution](https://stackoverflow.com/a/44507301) if you use a brew installation; otherwise you first need to [install MySQL](https://dev.mysql.com/doc/refman/8.0/en/osx-installation-pkg.html) and then pip-install mysql-connector-python. On Linux systems, [this solution](https://stackoverflow.com/a/35191977) might help you*

The way it is set up now you need an Elasticsearch database (infos on how to install this are [here](https://github.com/uvacw/inca/blob/development/doc/gettingstarted.md) under point 3) for storing the news content you want to show to the user and an MySQL or SQLite database for storing the results. 

Before running the app: 
export FLASK_APP=3bij3.py

In addition, you also need to initialize, migrate and upgrade the database. This can be done by running:

```python3
flask db init
flask db migrate
flask db upgrade
```

During development, you can start the app by typing "flask run", it then can be found in the browser under localhost:5000

More detailed instructions on how a flask app is built can be found in a [highly recommended tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world) by Miguel Grinberg which was used to build this application. Here you can also find further information on how to put the application to production. 
