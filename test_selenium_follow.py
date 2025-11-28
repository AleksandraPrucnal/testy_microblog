import pytest
import time
import sys
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import sqlalchemy as sa

from app import create_app, db
from app.models import User, Post


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


USERNAME = 'ola'
EMAIL = 'ola@example.com'
PASSWORD = 'ola123'

OTHER_USERNAME = 'kasia'
OTHER_EMAIL = 'kasia@email.com'
OTHER_PASSWORD = 'kasia321'

POST = 'bla bla bla post'


def _clean_database():
    """Usuwa bazę i tworzy nową (reset - opcja atomowa)"""
    db.session.remove()
    db.drop_all()
    db.create_all()


@pytest.fixture(scope="function")
def db_setup():
    """Kontekst aplikacji, czyszczenie i tworzenie DWÓCH użytkowników"""
    app = create_app()
    app_context = app.app_context()
    app_context.push()

    _clean_database()

    user = User(username=USERNAME, email=EMAIL)
    user.set_password(PASSWORD)
    db.session.add(user)

    other_user = User(username=OTHER_USERNAME, email=OTHER_EMAIL)
    other_user.set_password(OTHER_PASSWORD)
    db.session.add(other_user)

    db.session.commit()

    post = Post(body=POST, author=other_user)
    db.session.add(post)
    db.session.commit()

    yield app

    _clean_database()
    app_context.pop()


@pytest.fixture(scope="function")
def driver():
    """Ustawienia przegladarki (komunikaty z chrome przeszkadzaly w testach- wylaczam wszystkie pojawiajace sie okienka)"""
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "safebrowsing.enabled": False,
        "safebrowsing.disable_download_protection": True,
    })

    chrome_options.add_argument("--disable-features=PasswordLeakDetection")
    chrome_options.add_argument("--disable-features=SafetyCheck")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--incognito")

    browser_driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    browser_driver.implicitly_wait(10)
    yield browser_driver
    browser_driver.quit()


def test_follow(driver, db_setup):
    """Sprawdza, czy dziala funkcja follow. Wczesniej Ola nie obserwuje Kasi
    Jezeli ja obserwuje to jej post bedzie na stronie Home, jezeli nie obserwuje, to nie bedzie tam postu Kasi"""
    wait = WebDriverWait(driver, 10)

    driver.get("http://localhost:5000/auth/login")
    driver.find_element(By.ID, "username").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "submit").click()

    wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Home")))

    assert POST not in driver.page_source

    driver.get(f"http://localhost:5000/user/{OTHER_USERNAME}")
    follow = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Follow']")))
    driver.execute_script("arguments[0].click();", follow)

    message = wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'following')]")))
    assert message.is_displayed()

    """Powinien byc widoczny przycisk unfollow"""
    unfollow = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@value='Unfollow']")))
    assert unfollow.is_displayed()

    """Teraz post Kasi powinien sie wyswietlac na stronie Home"""
    driver.find_element(By.LINK_TEXT, "Home").click()
    wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Explore")))

    assert POST in driver.page_source


def test_unfollow(driver, db_setup):
    """W bazie danych ustawiamy relacje Kasi i Oli (Ola obserwuje Kasie)"""
    wait = WebDriverWait(driver, 10)

    ola = db.session.scalar(sa.select(User).where(User.username == USERNAME))
    kasia = db.session.scalar(sa.select(User).where(User.username == OTHER_USERNAME))

    ola.follow(kasia)
    db.session.commit()

    driver.get("http://localhost:5000/auth/login")
    driver.find_element(By.ID, "username").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "submit").click()

    wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Home")))

    """Post Kasi jest widoczny bo Ola ja obserwuje"""
    assert POST in driver.page_source

    driver.get(f"http://localhost:5000/user/{OTHER_USERNAME}")
    unfollow = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Unfollow']")))
    driver.execute_script("arguments[0].click();", unfollow)

    message = wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'not following')]")))
    assert message.is_displayed()

    """Przycisk powinien zmienic sie na follow"""
    follow_btn_again = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@value='Follow']")))
    assert follow_btn_again.is_displayed()

    """Na stronie Home nie powinno byc postu Kasi"""
    driver.find_element(By.LINK_TEXT, "Home").click()
    wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Explore")))

    assert POST not in driver.page_source


def test_follow_self(driver, db_setup):
    """Sprawdza, czy uzytkownik moze zaobserwowac samego siebie"""
    wait = WebDriverWait(driver, 10)

    driver.get("http://localhost:5000/auth/login")
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "submit").click()

    wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Home")))
    driver.get(f"http://localhost:5000/user/{USERNAME}")

    follow = driver.find_elements(By.XPATH, "//input[@value='Follow']")
    assert len(follow) == 0


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))
