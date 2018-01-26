from app import app, db
from app.models import User, Category, News, News_sel

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Category':Category, 'News':News, 'News_sel': News_sel}

