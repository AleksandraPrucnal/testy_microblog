import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import User
from app import db


def test_login_page_loads(client):
    """Sprawdza, czy dziala strona logowania, czy serwer odpowiada- kod 200"""
    response = client.get('/auth/login')

    assert response.status_code == 200
    assert b'Sign In' in response.data


def test_login_success(client, user_ola):
    """Sprawdza, czy po poprawnym wpisaniu username i password nastapi poprawne logowanie"""
    response = client.post('/auth/login', data={
        'username': 'ola',
        'password': 'ola123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Logout' in response.data


def test_login_failure(client, user_ola):
    """Sprawdza, czy po blednym wpisaniu username i password, serwer odrzuci rzadanie"""
    response = client.post('/auth/login', data={
        'username': 'ola',
        'password': 'innehaslo'
    }, follow_redirects=True)

    assert b'Invalid username or password' in response.data


def test_logout(client, user_ola):
    """Sprawdza poprawne logowanie a nastepnie wylogowanie"""
    client.post('/auth/login', data={'username': 'ola', 'password': 'ola123'})

    response = client.get('/auth/logout', follow_redirects=True)

    assert response.status_code == 200
    assert b'Login' in response.data


def test_register_success(client, app):
    """Sprawdza poprawna rejestracje nowego uzytkownika"""
    # Dane nowego użytkownika
    new_user_data = {
        'username': 'aleksandra',
        'email': 'aleksandra@email.com',
        'password': 'aleksandra123',
        'password2': 'aleksandra123'
    }

    response = client.post('/auth/register', data=new_user_data, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.username == 'aleksandra'))
        assert user is not None
        assert user.email == 'aleksandra@email.com'


def test_register_username_exist(client, user_ola):
    """Sprawdza, czy wykryje istniejacy username 'ola' i wyrzuci blad"""
    response = client.post('/auth/register', data={
        'username': 'ola',
        'email': 'inny@email.com',
        'password': 'haslo',
        'password2': 'haslo'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Please use a different username.' in response.data


def test_register_email_exist(client, user_ola):
    """Sprawdza, czy wykryje istniejacy email"""
    response = client.post('/auth/register', data={
        'username': 'usernamenowy',
        'email': 'ola@email.com',
        'password': 'haslo',
        'password2': 'haslo'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Please use a different email address.' in response.data