import pytest
import sys
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from app import create_app, db
from app.models import User

USERNAME = "ola"
EMAIL = "ola@email.com"
PASSWORD = "ola123"

DESCRIPTION = "JAKIS TAM OPIS"


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

    user = User(username=USERNAME, email=EMAIL)
    user.set_password(PASSWORD)
    db.session.add(user)
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


def test_edit_profile(driver, db_setup):
    wait = WebDriverWait(driver, 10)

    driver.get("http://localhost:5000/auth/login")
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "submit").click()

    wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Home")))
    profile_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Profile")))
    driver.execute_script("arguments[0].click();", profile_link)

    wait.until(EC.visibility_of_element_located((By.XPATH, f"//*[contains(text(), '{USERNAME}')]")))

    edit_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Edit your profile")))
    driver.execute_script("arguments[0].click();", edit_link)

    desc_field = wait.until(EC.visibility_of_element_located((By.NAME, "about_me")))
    desc_field.clear()
    desc_field.send_keys(DESCRIPTION)

    submit = driver.find_element(By.ID, "submit")
    driver.execute_script("arguments[0].scrollIntoView(true);", submit)
    driver.execute_script("arguments[0].click();", submit)

    """Powinien byc komunikat ze zmiany zostaly zmienione"""
    flash_msg = wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'changes have been saved')]")))
    assert flash_msg.is_displayed()

    new_desc = driver.find_element(By.XPATH, f"//*[contains(text(), '{DESCRIPTION}')]")
    assert new_desc.is_displayed()


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))