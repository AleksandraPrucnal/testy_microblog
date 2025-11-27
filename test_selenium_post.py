import pytest
import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from app import create_app, db
from app.models import User, Post

USERNAME = 'ola'
EMAIL = 'ola@example.com'
PASSWORD = 'haslo123'

OTHER_USERNAME = 'ola2'
OTHER_EMAIL = 'ola2@email.com'
OTHER_PASSWORD = 'innehaslo'


def _clean_database():
    """Usuwa bazę i tworzy nową (reset)"""
    db.session.remove()
    db.drop_all()
    db.create_all()


@pytest.fixture(scope="function")
def db_setup():
    """Kontekst aplikacji i czysci baze danych"""
    app = create_app()
    app_context = app.app_context()
    app_context.push()

    _clean_database()

    user = User(username=USERNAME, email=EMAIL)
    user.set_password(PASSWORD)
    db.session.add(user)
    db.session.commit()

    yield app

    _clean_database()
    app_context.pop()


@pytest.fixture(scope="function")
def driver():
    """Uruchamia i konfiguruje przegladarke"""
    browser_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    browser_driver.implicitly_wait(10)

    yield browser_driver

    browser_driver.quit()


def test_create_post_successful(driver, db_setup):
    driver.get("http://localhost:5000/auth/login")

    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "submit").click()

    time.sleep(1)

    assert "/index" in driver.current_url

    post_content = "bla bla bla jakis post"
    driver.find_element(By.NAME, "post").send_keys(post_content)
    driver.find_element(By.ID, "submit").click()

    time.sleep(1)

    message = driver.find_element(By.XPATH, "//*[contains(text(), 'Your post is now live!')]")
    assert message.is_displayed()

    new_post = driver.find_element(By.XPATH, f"//*[contains(text(), '{post_content}')]")
    assert new_post.is_displayed()


def test_create_post_empty_failure(driver, db_setup):
    """Sprawdza czy jest niemozliwe utworzenie posta bez tresci"""
    driver.get("http://localhost:5000/auth/login")

    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    assert "Your post is now live!" not in driver.page_source


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))