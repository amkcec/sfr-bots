import argparse
import logging
import phonenumbers
import sys
import time
import tkinter as tk

from logging.handlers import TimedRotatingFileHandler

from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options

from tkinter.messagebox import askretrycancel
from tkinter.simpledialog import askstring


class ValidationError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def accept_cookies(driver):
    while True:
        try:
            elem = driver.find_element(By.CSS_SELECTOR, "#CkC > div > a.A").click()
        except NoSuchElementException as e:
            logger.error("Erreur lors de l'acceptation des cookies")
            askretrycancel(
                "Selenium", "Erreur lors de l'acceptation des cookies. Réessayer ?"
            )
        else:
            logger.info("Cookies acceptés")
            break


def format_phone_number(phone_number):
    phone_number = phonenumbers.parse(phone_number, "FR")
    if not phonenumbers.is_valid_number(phone_number):
        raise ValidationError(
            phonenumbers.format_number(
                phone_number, phonenumbers.PhoneNumberFormat.NATIONAL
            )
        )
    phone_number = phonenumbers.format_number(
        phone_number, phonenumbers.PhoneNumberFormat.NATIONAL
    ).replace(" ", "")
    return phone_number


def get_phone_numbers_and_top_ups():
    while True:
        try:
            table = askstring("Bot recharges", "Renseignez le tableau")
            lines = table.split("\n")
            phone_numbers_and_top_ups = []
            for s in lines:
                phone_number, top_up = s.split("\t")
                phone_number = format_phone_number(phone_number)
                top_up = top_up.replace(" ", "")
                phone_numbers_and_top_ups.append([phone_number, top_up])
        except AttributeError:
            logger.info("Programme arrêté manuellement")
            sys.exit(0)
        except ValueError:
            logger.error("Tableau mal renseigné")
        except ValidationError as e:
            logger.error("Un des numéros est non valide", e)
        except Exception:
            logger.exception("Autre")
        else:
            break
    return phone_numbers_and_top_ups


def enter_phone_number(phone_number):
    while True:
        try:
            form = driver.find_element(By.XPATH, "//*[@id='chooseLineForm']")
            entry = form.find_element(By.NAME, "lineToBeRecharged")
            entry.send_keys(phone_number)
            driver.find_element(By.CSS_SELECTOR, "#valider_ligne_btn").click()
        except (NoSuchElementException, ElementNotInteractableException):
            logger.error("Erreur avec le numéro de ligne mobile")
            askretrycancel(
                "Selenium", "Erreur avec le numéro de ligne mobile. Réessayer ?"
            )
        else:
            break


def enter_top_up(top_up):
    while True:
        try:
            entry = driver.find_element(By.NAME, "codeCoupon")
            entry.send_keys(cltRec)
            driver.find_element(By.CSS_SELECTOR, "#code_coupon_btn_valider").click()
        except (NoSuchElementException, ElementNotInteractableException):
            logger.error("Erreur avec le code de recharge")
            askretrycancel("Selenium", "Erreur avec le code de recharge. Réessayer ?")
        else:
            break


def recharge(phone_number, top_up):
    driver.get(url)
    time.sleep(1)

    enter_phone_number(phone_number)
    time.sleep(random.uniform(0.64, 1.28))

    enter_top_up(top_up)
    time.sleep(random.uniform(0.64, 1.28))

    try:
        driver.find_element(By, CSS_SELECTOR, ".nonValide")
    except NoSuchElementException:
        logger.info("La recharge a fonctionné")
    else:
        logger.warning("Recharge non valide")
        askretrycancel("Selenium", "Erreur lors du rechargement. Réessayer ?")


def create_no_cache_profile():
    options = Options()
    options.set_preference("browser.cache.disk.enable", False)
    options.set_preference("browser.cache.memory.enable", False)
    options.set_preference("browser.cache.offline.enable", False)
    return options


def create_loggers():
    logger_format = logging.Formatter("[%(asctime)s] %(levelname)-8s | %(message)s")

    log_file_handler = TimedRotatingFileHandler("logs/recharge.log", when="D")
    log_file_handler.setFormatter(logger_format)
    log_file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logger_format)
    console_handler.setLevel(logging.INFO)

    logger = logging.getLogger("recharge")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(log_file_handler)
    logger.addHandler(console_handler)

    results_file_handler = TimedRotatingFileHandler(
        "logs/resultats_recharge.log", when="D"
    )
    results_file_handler.setFormatter(logger_format)
    results_file_handler.setLevel(logging.DEBUG)

    results_logger = logging.getLogger("recharge.resultats")
    results_logger.addHandler(results_file_handler)

    return logger, results_logger


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="expliquer ce qui est fait"
    )
    args = parser.parse_args

    logger, results_logger = create_loggers()
    url = "https://www.sfr.fr/espace-client/rechargement/saisie-ligne.html"

    logger.info("Ouverture de tkinter")

    phone_numbers_and_top_ups = get_phone_numbers_and_top_ups()

    organisation_name = askstring("Bot recharges", "Nom du tableau")

    options = create_no_cache_profile()
    logging.info("Ouverture du navigateur")

    driver = webdriver.Firefox(options=options)
    driver.set_window_size(1024, 950)

    driver.get(url)

    while True:
        try:
            accept_cookies(driver)


    for phone_number, top_up in phone_numbers_and_top_ups:
        try:
            recharge(phone_number, top_up)
        except Exception as e:
            askretrycancel("Selenium", "narsiute")
            logging.exception("Erreur de donnée")
