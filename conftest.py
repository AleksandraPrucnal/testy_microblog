import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from config import Config
from app.models import User, Post
from datetime import datetime, timezone


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'klucz'

    WTF_CSRF_ENABLED = False

    ELASTICSEARCH_URL = None
    REDIS_URL = 'redis://'


@pytest.fixture(scope='function')
def app():
    """Instancja aplikacji"""
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Klient do żądań HTTP"""
    return app.test_client()


@pytest.fixture(scope='function')
def session(app):
    """Zwraca sesję bd"""
    return db.session


@pytest.fixture(scope='function')
def user_ola(session):
    """Użytkownik Ola"""
    u = User(username='ola', email='ola@email.com')
    u.set_password('ola123')
    session.add(u)
    session.commit()
    return u


@pytest.fixture(scope='function')
def user_kasia(session):
    """Użytkownik Kasia"""
    u = User(username='kasia', email='kasia@email.com')
    u.set_password('kasia123')
    session.add(u)
    session.commit()
    return u


@pytest.fixture(scope='function')
def post_ola(session, user_ola):
    """Post Oli"""
    p = Post(body="Post Oli", author=user_ola, timestamp=datetime.now(timezone.utc))
    session.add(p)
    session.commit()
    return p