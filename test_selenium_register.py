import pytest
import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from app import create_app, db
from app.models import User, Post

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

TEST_USERNAME = 'ola'
TEST_EMAIL = 'ola@email.com'
TEST_PASSWORD = 'ola123'

OTHER_TEST_USERNAME = 'ola2'
OTHER_TEST_EMAIL = 'ola2@email.com'
OTHER_TEST_PASSWORD = 'innehaslo'


def _clean_database():
    """Usuwa uzytkownika ola jesli istnieje"""
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

    yield app
    _clean_database()
    app_context.pop()


@pytest.fixture(scope="function")
def driver():
    """Uruchamia i konfiguruje przegladarke, po zakonczeniu testu zamyka okno"""
    browser_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    browser_driver.implicitly_wait(10)

    yield browser_driver

    browser_driver.quit()


def test_register_success(driver, db_setup):
    driver.get("http://localhost:5000/auth/register")

    driver.find_element(By.NAME, "username").send_keys(TEST_USERNAME)
    driver.find_element(By.NAME, "email").send_keys(TEST_EMAIL)
    driver.find_element(By.NAME, "password").send_keys(TEST_PASSWORD)

    try:
        """szuka drugiego pola by_name 'password2',
        jesli takiego nie ma to by_css_selector czyli elementy zawierajace'password'
        drugie takie pole to powtorzenie hasla dlatego len>=2"""
        driver.find_element(By.NAME, "password2").send_keys(TEST_PASSWORD)
    except:
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        if len(inputs) >= 2:
            inputs[1].send_keys(TEST_PASSWORD)

    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    assert "/auth/login" in driver.current_url
    message = driver.find_element(By.XPATH, "//*[contains(text(), 'Congratulations')]")
    assert message.is_displayed()


def test_register_passwords_mismatch(driver, db_setup):
    driver.get("http://localhost:5000/auth/register")

    driver.find_element(By.ID, "username").send_keys(TEST_USERNAME)
    driver.find_element(By.ID, "email").send_keys(TEST_EMAIL)
    driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)

    try:
        driver.find_element(By.NAME, "check_password").send_keys(OTHER_TEST_PASSWORD)
    except:
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        if len(inputs) >= 2:
            inputs[1].send_keys(OTHER_TEST_PASSWORD)

    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    assert "/auth/register" in driver.current_url
    message = driver.find_element(By.XPATH, "//*[contains(text(), 'Field must be equal to password')]")
    assert message.is_displayed()


def test_register_username_exist(driver, db_setup):
    """Sprawdza, czy wykryje istniejacy username 'ola' i wyrzuci blad"""
    existing_user = User(username=TEST_USERNAME, email=OTHER_TEST_EMAIL)
    existing_user.set_password(TEST_PASSWORD)
    db.session.add(existing_user)
    db.session.commit()

    driver.get("http://localhost:5000/auth/register")

    driver.find_element(By.NAME, "username").send_keys(TEST_USERNAME)
    driver.find_element(By.NAME, "email").send_keys(TEST_EMAIL)
    driver.find_element(By.NAME, "password").send_keys(OTHER_TEST_PASSWORD)

    try:
        driver.find_element(By.NAME, "password2").send_keys(OTHER_TEST_PASSWORD)
    except:
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        if len(inputs) >= 2:
            inputs[1].send_keys(OTHER_TEST_PASSWORD)

    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    assert "/auth/register" in driver.current_url
    error_msg = driver.find_element(By.XPATH, "//*[contains(text(), 'Please use a different username')]")
    assert error_msg.is_displayed()


def test_register_email_exist(driver, db_setup):
    """Sprawdza, czy wykryje istniejacy email i wyrzuci blad"""
    existing_user = User(username=OTHER_TEST_USERNAME, email=TEST_EMAIL)
    existing_user.set_password(TEST_PASSWORD)
    db.session.add(existing_user)
    db.session.commit()

    driver.get("http://localhost:5000/auth/register")

    driver.find_element(By.NAME, "username").send_keys(TEST_USERNAME)
    driver.find_element(By.NAME, "email").send_keys(TEST_EMAIL)
    driver.find_element(By.NAME, "password").send_keys(OTHER_TEST_PASSWORD)

    try:
        driver.find_element(By.NAME, "password2").send_keys(OTHER_TEST_PASSWORD)
    except:
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        if len(inputs) >= 2:
            inputs[1].send_keys(OTHER_TEST_PASSWORD)

    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    assert "/auth/register" in driver.current_url
    error_msg = driver.find_element(By.XPATH, "//*[contains(text(), 'Please use a different email address')]")
    assert error_msg.is_displayed()


def test_register_invalid_email_format(driver, db_setup):
    """sprawdza czy wyrzuci blad jesli podamy email w nieodpowiednim formacie"""
    driver.get("http://localhost:5000/auth/register")

    driver.find_element(By.ID, "username").send_keys(TEST_USERNAME)
    driver.find_element(By.ID, "email").send_keys("olaemail.com")
    driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)

    try:
        driver.find_element(By.NAME, "password2").send_keys(TEST_PASSWORD)
    except:
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        if len(inputs) >= 2:
            inputs[1].send_keys(TEST_PASSWORD)

    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    assert "/auth/register" in driver.current_url

    message = driver.find_element(By.XPATH, "//*[contains(text(), 'Invalid email address')]")
    assert message.is_displayed()


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))