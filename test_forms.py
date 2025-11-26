import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.auth.forms import RegistrationForm


def test_registration_form_success(app):
    """Sprawdza, czy formularz przechodzi walidację przy poprawnych danych."""
    with app.test_request_context():
        form = RegistrationForm(
            username='aleksandra',
            email='aleksandra@email.com',
            password='aleksandra123',
            password2='aleksandra123'
        )

        assert form.validate() is True


def test_registration_form_pasword2_different(app):
    """Sprawdza, czy formularz wyrzuci blad przy blednie powtorzonym hasle"""
    with app.test_request_context():
        form = RegistrationForm(
            username='aleksandra',
            email='aleksandra@email.com',
            password='aleksandra123',
            password2='innehaslo'
        )

        assert form.validate() is False
        assert 'password2' in form.errors


def test_register_username_exist(app, user_ola):
    """Sprawdza, czy wykryje istniejacy username 'ola' i wyrzuci blad"""
    with app.test_request_context():
        form = RegistrationForm(
            username='ola',
            email='inny@email.com',
            password='haslo',
            password2='haslo'
        )

        assert form.validate() is False
        assert 'username' in form.errors
        assert 'Please use a different username.' in form.errors['username']


def test_register_email_exist(app, user_ola):
    """Sprawdza, czy wykryje istniejacy email i wyrzuci blad"""
    with app.test_request_context():
        form = RegistrationForm(
            username='usernamenowy',
            email='ola@email.com',
            password='haslo',
            password2='haslo'
        )

        assert form.validate() is False

        assert 'email' in form.errors
        assert 'Please use a different email address.' in form.errors['email']