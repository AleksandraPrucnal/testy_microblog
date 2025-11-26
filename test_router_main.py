import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import db
from app.models import User, Post


def login(client, username, password):
    """Funkcja pomocnicza do logowania w testach"""
    return client.post('/auth/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


def test_index_page_protected(client):
    """Niezalogowany uzytkownik powinien zostac przekierowany dostrony logowania- sprawdzenie autoryzacji"""
    response = client.get('/index')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_create_post(client, app, user_ola):
    """Dodawanie nowego posta"""
    login(client, 'ola', 'ola123')
    post_text = 'Jakis tam post bla bla bla'

    response = client.post('/index', data={'post': post_text}, follow_redirects=True)

    assert response.status_code == 200
    assert b'Your post is now live!' in response.data

    assert b'Jakis tam post bla bla bla' in response.data

    with app.app_context():
        post = db.session.scalar(db.select(Post).where(Post.body == post_text))
        assert post is not None
        assert post.author == user_ola


def test_user_profile_page(client, user_ola):
    """Sprawdza, czy profil sie wyswietla"""
    login(client, 'ola', 'ola123')

    response = client.get('/user/ola')
    assert response.status_code == 200

    assert b'User: ola' in response.data


def test_edit_profile(client, app, user_ola):
    """Sprawdza czyy dziala edycja profilu"""
    login(client, 'ola', 'ola123')

    response = client.post('/edit_profile', data={
        'username': 'ola',
        'about_me': 'bla bla bla'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Your changes have been saved.' in response.data

    with app.app_context():
        u = db.session.get(User, user_ola.id)
        assert u.about_me == 'bla bla bla'


def test_follow(client, app, user_ola, user_kasia):
    """Sprawdzamy czy dziala funkcja follow"""
    login(client, 'ola', 'ola123')
    response = client.post(f'/follow/{user_kasia.username}', follow_redirects=True)

    assert response.status_code == 200
    assert f'You are following {user_kasia.username}!'.encode('utf-8') in response.data

    with app.app_context():
        ola = db.session.get(User, user_ola.id)
        kasia = db.session.get(User, user_kasia.id)

        assert ola.is_following(kasia) is True


def test_unfollow(client, app, user_ola, user_kasia):
    """Sprawdzamy czy dziala funkcja follow"""
    user_ola.follow(user_kasia)
    db.session.commit()

    login(client, 'ola', 'ola123')
    response = client.post(f'/unfollow/{user_kasia.username}', follow_redirects=True)

    assert response.status_code == 200
    assert f'You are not following {user_kasia.username}.'.encode('utf-8') in response.data

    with app.app_context():
        ola = db.session.get(User, user_ola.id)
        kasia = db.session.get(User, user_kasia.id)
        assert ola.is_following(kasia) is False


def test_explore_page(client, user_ola, post_ola):
    """Sprawdza czy strona Explore sie wyswietla"""
    login(client, 'ola', 'ola123')

    response = client.get('/explore')
    assert response.status_code == 200

    assert b'Post Oli' in response.data