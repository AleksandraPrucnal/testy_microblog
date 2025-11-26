import pytest
from datetime import datetime, timezone, timedelta
from app.models import User, Post, Message, Notification
from app import db


def test_password_hashing(user_ola):
    """Sprawdza czy haslo bedzie zahaszowane czy bedzie zwyklym tekstem"""
    assert user_ola.password_hash != 'ola123'


def test_check_password_correct(user_ola):
    """Sprawdza  czy haslo jest prawidlowe"""
    assert user_ola.check_password('ola123') is True


def test_check_password_incorrect(user_ola):
    """Sprawdza czy bledne haslo bedzie odrzucone"""
    assert user_ola.check_password('blednehaslo') is False


def test_password_correct_hashing(session):
    """Sprawdza, czy uzytkownicy, ktorzy maja takie same hasla, beda mieli inne hashe."""
    user1 = User(username='user1', email='jakis1@email.com')
    user2 = User(username='user2', email='jakis2@email.com')
    user1.set_password('probnehaslo')
    user2.set_password('probnehaslo')
    session.add_all([user1, user2])
    session.commit()
    assert user1.password_hash != user2.password_hash


def test_reset_password(app, user_ola):
    """Sprawdza, czy generuje sie token JWT i weryfikacje tokena"""
    token = user_ola.get_reset_password_token()
    user = User.verify_reset_password_token(token)
    assert user == user_ola


def test_follow(session, user_ola, user_kasia):
    """Sprawdza, czy dziala follow- Ola obserwuje Kasie"""
    user_ola.follow(user_kasia)
    session.commit()
    assert user_ola.is_following(user_kasia) is True


def test_unfollow(session, user_ola, user_kasia):
    """Sprawdza, czy dziala unfollow- Ola juz nie obserwuje Kasi"""
    user_ola.follow(user_kasia)
    session.commit()
    user_ola.unfollow(user_kasia)
    session.commit()
    assert user_ola.is_following(user_kasia) is False


def test_following_count(session, user_ola, user_kasia):
    """Sprawdza, czy zmienia sie licxzba osob zaobserwowanych po wywolaniu funckji follow"""
    assert user_ola.following_count() == 0
    user_ola.follow(user_kasia)
    session.commit()
    assert user_ola.following_count() == 1


def test_followers_count(session, user_ola, user_kasia):
    """Sprawdza, czy liczba osob obserwowanych sie zmienila"""
    assert user_kasia.followers_count() == 0
    user_ola.follow(user_kasia)
    session.commit()
    assert user_kasia.followers_count() == 1


def test_add_post(session, user_ola):
    """Sprawdza tworzenie posta przez uzytkownika"""
    p = Post(body="Test post", author=user_ola)
    session.add(p)
    session.commit()
    assert p.user_id == user_ola.id
    assert user_ola.posts_count() == 1


def test_following_posts_logic(session, user_ola, user_kasia):
    """
    Sprawdza, czy Ola widzi posty Kasi, ktora obserwuje i czy nie widzi postow Asi, ktorej nie obserwuje
    """
    user_asia = User(username='asia', email='asia@email.com')
    session.add(user_asia)

    now = datetime.now(timezone.utc)
    p1 = Post(body="Post Oli", author=user_ola, timestamp=now + timedelta(seconds=1))
    p2 = Post(body="Post Kasi", author=user_kasia, timestamp=now + timedelta(seconds=4))
    p3 = Post(body="Post Asi", author=user_asia, timestamp=now + timedelta(seconds=3))

    session.add_all([p1, p2, p3])
    session.commit()

    user_ola.follow(user_kasia)
    session.commit()

    feed = db.session.scalars(user_ola.following_posts()).all()

    assert p2 in feed
    assert p1 in feed
    assert p3 not in feed
    
    
def test_post_order_by_date(session, user_ola, user_kasia):
    """Sprawdza, czy kolejnosc postow jest od najnowszych do najstarszych"""
    now = datetime.now(timezone.utc)
    p1 = Post(body="Jakis tam post", author=user_ola, timestamp=now - timedelta(seconds=10))
    p2 = Post(body="Najnowszy post", author=user_kasia, timestamp=now)

    user_ola.follow(user_kasia)
    session.add_all([p1, p2])
    session.commit()

    feed = db.session.scalars(user_ola.following_posts()).all()
    assert feed[0] == p2
    assert feed[1] == p1


def test_unfollowed_posts_disappear(session, user_ola, user_kasia):
    """Sprawdza, czy po follow sa posty a nastepnie po unfollow powinno ich nie byc"""
    p = Post(body="Post Kasi", author=user_kasia)
    session.add(p)
    user_ola.follow(user_kasia)
    session.commit()

    assert p in db.session.scalars(user_ola.following_posts()).all()

    user_ola.unfollow(user_kasia)
    session.commit()

    assert p not in db.session.scalars(user_ola.following_posts()).all()


def test_messages_count(session, user_ola, user_kasia):
    """Sprawdza licznik nieprzeczytanych wiadomości"""
    message = Message(sender_id=user_kasia.id, recipient_id=user_ola.id, body="jakas wiadomosc")
    session.add(message)
    session.commit()
    assert user_ola.unread_message_count() == 1

    user_ola.last_message_read_time = datetime.now(timezone.utc)
    session.commit()
    assert user_ola.unread_message_count() == 0



def test_add_notification(session, user_ola):
    """Sprawdza nowe powiadomienia"""
    user_ola.add_notification('unread_message_count', 10)
    session.commit()

    notification = db.session.scalar(user_ola.notifications.select())
    assert notification.name == 'unread_message_count'
    assert notification.get_data() == 10