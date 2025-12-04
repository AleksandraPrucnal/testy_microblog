import pytest
import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


from app import create_app, db
from app.models import User, Message


USERNAME = 'ola'
EMAIL = 'ola@example.com'
PASSWORD = 'ola123'

OTHER_USERNAME = 'kasia'
OTHER_EMAIL = 'kasia@email.com'
OTHER_PASSWORD = 'kasia321'

MESSAGE = "wiadomosc dla Kasi od Oli"


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
        service=Service(executable_path='./chromedriver.exe'),
        options=chrome_options
    )

    browser_driver.implicitly_wait(10)
    yield browser_driver
    browser_driver.quit()


def test_send_and_receive_message(driver, db_setup):
    """Ola loguje sie i wysyla wiadomosc do Kasi. Kasia loguje sie i ma wiadomosc w skrzynce"""
    wait = WebDriverWait(driver, 10)

    driver.get("http://localhost:5000/auth/login")
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "submit").click()

    wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Home")))

    driver.get(f"http://localhost:5000/user/{OTHER_USERNAME}")

    send_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Send private message")))
    driver.execute_script("arguments[0].click();", send_link)

    msg_field = wait.until(EC.visibility_of_element_located((By.NAME, "message")))
    """czyszczenie pola tekstowego i ustawienie kursora w srodku pola- click"""
    msg_field.click()
    msg_field.clear()

    msg_field.send_keys(MESSAGE)

    time.sleep(1)

    driver.find_element(By.ID, "submit").click()

    success_msg = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Your message has been sent')]")
        )
    )
    assert success_msg.is_displayed()

    """Wylogowanie Oli. Zalogowanie Kasi"""
    logout_link = driver.find_element(By.LINK_TEXT, "Logout")
    driver.execute_script("arguments[0].click();", logout_link)

    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Login")))
    driver.get("http://localhost:5000/auth/login")
    driver.find_element(By.NAME, "username").send_keys(OTHER_USERNAME)
    driver.find_element(By.NAME, "password").send_keys(OTHER_PASSWORD)
    driver.find_element(By.ID, "submit").click()

    wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Home")))

    messages_link = wait.until(
        EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Messages"))
    )
    driver.execute_script("arguments[0].click();", messages_link)

    received_msg = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, f"//*[contains(text(), '{MESSAGE}')]")
        )
    )
    assert received_msg.is_displayed()


def test_send_message_empty_failure(driver, db_setup):
    """Sprawdzamy czy wysle pusta wiadomosc"""
    wait = WebDriverWait(driver, 10)

    driver.get("http://localhost:5000/auth/login")
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "submit").click()

    wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Home")))

    driver.get(f"http://localhost:5000/user/{OTHER_USERNAME}")

    send_msg_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Send private message")))
    driver.execute_script("arguments[0].click();", send_msg_link)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))

    """od razu submit bez wczesniej wpisanego testu"""
    driver.find_element(By.ID, "submit").click()

    time.sleep(1)

    assert "Your message has been sent" not in driver.page_source


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))