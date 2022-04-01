#!/usr/bin/python

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

from tkinter.messagebox import askretrycancel, showerror, showwarning
from tkinter.simpledialog import askstring


class ValidationError(Exception):
    def __init__(self, phone_number):
        self.value = phonenumbers.format_number(
            phone_number, phonenumbers.PhoneNumberFormat.NATIONAL
        )

    def __str__(self):
        return repr(self.value)


def accept_cookies(driver):
    logger.info("Acceptation des cookies")
    while True:
        try:
            elem = driver.find_element(By.CSS_SELECTOR, "#CkC > div > a.A").click()
        except NoSuchElementException as e:
            error_message = "Erreur lors de l'acceptation des cookies"
            logger.error(error_message)
            retry = askretrycancel(app_name, f"{error_message}. Réessayer ?")
            if retry:
                logger.debug("Nouvelle tentative d'acceptation des cookies")
            else:
                logger.info("Programme arrêté manuellement")
                sys.exit(0)
        else:
            logger.info("Cookies acceptés")
            break


def format_phone_number(phone_number):
    phone_number = phonenumbers.parse(phone_number, "FR")
    if not phonenumbers.is_valid_number(phone_number):
        raise ValidationError(phone_number)
    phone_number = phonenumbers.format_number(
        phone_number, phonenumbers.PhoneNumberFormat.NATIONAL
    ).replace(" ", "")
    return phone_number


def get_phone_numbers_and_top_ups():
    logger.info("Renseignement des numéros de téléphone et recharges")
    while True:
        try:
            table = askstring(
                app_name, "Renseignez les numéros de téléphone et recharges"
            )
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
            error_message = "Les numéros de téléphone et les recharges doivent provenir d'un tableau à deux colonnes"
            showerror(app_name, error_message)
            logger.error(error_message)
        except ValidationError as e:
            error_message = f"Le numéro suivant est non valide : {str(e)}"
            showerror(app_name, error_message)
            logger.error(error_message)
        except Exception as e:
            logger.exception("Autre erreur")
        else:
            break
    return phone_numbers_and_top_ups


def enter_phone_number(phone_number):
    logger.debug(f"Instruction du numéro de la ligne mobile : {phone_number}")
    while True:
        try:
            form = driver.find_element(By.XPATH, "//*[@id='chooseLineForm']")
            entry = form.find_element(By.NAME, "lineToBeRecharged")
            entry.send_keys(phone_number)
            driver.find_element(By.CSS_SELECTOR, "#valider_ligne_btn").click()
        except (NoSuchElementException, ElementNotInteractableException):
            error_message = (
                f"Erreur lors du renseignement de la ligne mobile : {phone_number}"
            )
            logger.error(error_message)
            retry = askretrycancel(app_name, f"{error_message}. Réessayer ?")
            if retry:
                logger.debug(
                    f"Nouvelle tentative d'instruction du numéro de la ligne mobile : {phone_number}"
                )
            else:
                logger.info("Programme arrêté manuellement")
                sys.exit(0)
        else:
            break


def enter_top_up(top_up):
    logger.debug(f"Instruction du code de recharge : {top_up}")
    while True:
        try:
            entry = driver.find_element(By.NAME, "codeCoupon")
            entry.send_keys(cltRec)
            driver.find_element(By.CSS_SELECTOR, "#code_coupon_btn_valider").click()
        except (NoSuchElementException, ElementNotInteractableException):
            error_message = f"Erreur avec le code de recharge : {top_up}"
            logger.error(error_message)
            retry = askretrycancel(app_name, f"{error_message}. Réessayer ?")
            if retry:
                logger.debug(
                    f"Nouvelle tentative d'instruction du code de recharge : {top_up}"
                )
            else:
                logger.info("Programme arrêté manuellement")
                sys.exit()
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
        elem = driver.find_element(By, CSS_SELECTOR, ".nonValide")
    except NoSuchElementException:
        results_logger.info(
            f"{organisation_name} - Ligne rechargée avec succès : {phone_number} / {top_up}"
        )
        return true
    else:
        results_logger.warning(
            f"{organisation_name} - Ligne non rechargée : {phone_number} / {top_up} ({elem.text})"
        )
        return false


def create_no_cache_profile():
    logger.debug("Création du profil Firefox")
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

    app_name = "Recharges"
    url = "https://www.sfr.fr/espace-client/rechargement/saisie-ligne.html"
    logger, results_logger = create_loggers()

    phone_numbers_and_top_ups = get_phone_numbers_and_top_ups()
    organisation_name = askstring(app_name, "Nom de la structure")

    logger.info("Ouverture du navigateur Firefox")
    options = create_no_cache_profile()
    driver = webdriver.Firefox(options=options)
    driver.set_window_size(1024, 950)

    logger.debug("Navigation sur la page de recharge")
    driver.get(url)

    accept_cookies(driver)

    success_count = 0
    for phone_number, top_up in phone_numbers_and_top_ups:
        if recharge(phone_number, top_up):
            success_count += 1

    total_count = len(phone_numbers_and_top_ups)
    if success_count == total_count:
        results_logger.info(
            f"{organisation_name} - Toutes les lignes ({total_count}) ont été rechargées"
        )
    else:
        results_logger.info(
            f"{organisation_name} - Seules {success_count} lignes ont été rechargées sur les {total_count} demandées"
        )
