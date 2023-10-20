#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from NAS_Libraries.robotlogger import RobotLogger
from NAS_Libraries.robotkeyword import keyword
from HDP_Libraries.locators import Locators as Loc
from HDP_Libraries.main import HDP

LOGGER = RobotLogger(__name__)


class Login:
    def __init__(self):
        self.hdp = HDP()

    @keyword('HDP: Login: Enter values by ID')
    def enter_values_by_id(self, driver, web_element, text):
        """
        Lib to enter (write) values as strings based on web element

        Arguments
        | driver: Web driver of HDP
        | web_element: Web element where value to be entered
        | text: text string to be entered in web element
        """
        LOGGER.info(f'|___Entering {text} in web element___|')

        element = driver.find_element(By.ID, web_element)
        element.clear()
        element.send_keys(text)

        LOGGER.info(f'Updated {text} in web element\n')
        return True

    @keyword('HDP: Login: Skip guide')
    def skip_guide(self, driver):
        """
        Lib to skip guide in HDP welcome page

        Arguments
        | driver: Web driver of HDP
        """
        LOGGER.info('|___Skip guide___|')

        driver.find_element(By.XPATH, Loc.HDP_SKIP_GUIDE_XPATH).click()
        driver.find_element(By.XPATH, Loc.HDP_YES_BUTTON_XPATH).click()

        LOGGER.info("Skipped guide successfully\n")
        return True

    @keyword('HDP: Login: Login HDP')
    def login_hdp(self, driver, username, password):
        """
        Lib to log in to HDP

        Arguments:
        | chromedriver_path: Executable path of chromedriver
        | url: URL to be opened
        | driver: Web driver element for HDP
        | username: NAS username to login
        | password: NAS password to login
        """
        LOGGER.info('|___Login to HDP___|')

        # Validate URL is loaded in browser
        self.validate_url_is_loaded(driver, timeout=240)
        nas_title = driver.title
        if Loc.NAS_TITLE not in nas_title and \
                not driver.find_element(By.ID, Loc.NAS_USERNAME_ID):
            raise ValueError("HDP Login page is not loaded in URL")

        # Submit credentials
        self.enter_values_by_id(driver, Loc.NAS_USERNAME_ID, username)
        driver.find_element(By.CSS_SELECTOR, Loc.NAS_NEXT_BUTTON_CSS).click()
        self.enter_values_by_id(driver, Loc.NAS_PASSWORD_ID, password)
        driver.find_element(By.ID, Loc.NAS_SUBMIT_BUTTON_ID).click()

        # Validate HDP logged in and skip guide
        self.validate_hdp_logged_in(driver, timeout=300)
        hdp_title = driver.title
        if hdp_title != Loc.HDP_TITLE:
            raise ValueError("HDP page is not loaded in URL")

        self.skip_guide(driver)

        LOGGER.info("Logged in to HDP successfully\n")
        return True

    @keyword('HDP: Login: Validate URL is loaded')
    def validate_url_is_loaded(self, driver, timeout=None):
        """
        Lib to validate if HDP URL is loaded in browser or in loading screen

        Arguments
        driver: Web driver element for HDP
        | timeout: time in sec to validate if URL is loaded
        """
        LOGGER.info("|___Validate URL is loaded___|")

        timeout = timeout or self.hdp.check_timeout
        start_time = time.time()
        while True:
            if time.time() - start_time > int(timeout):
                raise ValueError("URL is not loaded in browser")

            try:
                WebDriverWait(driver, 2).until(ec.presence_of_element_located((
                    By.ID, Loc.NAS_USERNAME_ID)))
                break
            except TimeoutException:
                LOGGER.info("URL is not loaded yet, pending retry...")

            time.sleep(2)

        LOGGER.info("URL is loaded successfully\n")
        return True

    @keyword('HDP: Login: Validate HDP logged in')
    def validate_hdp_logged_in(self, driver, timeout=None):
        """
        Lib to validate if HDP is logged in and skip guide is loaded

        Arguments
        | driver: Web driver element for HDP
        | timeout: time in sec to validate if HDP is logged in
        """
        LOGGER.info("|___Validate HDP is logged in___|")

        timeout = timeout or self.hdp.check_timeout
        start_time = time.time()
        while True:
            if time.time() - start_time > int(timeout):
                raise ValueError("URL is not loaded in browser")

            try:
                WebDriverWait(driver, 2).until(ec.presence_of_element_located((
                    By.XPATH, Loc.HDP_SKIP_GUIDE_XPATH)))
                break
            except TimeoutException:
                LOGGER.info("HDP is not logged in yet, pending retry...")

            time.sleep(2)

        LOGGER.info("HDP is logged in successfully\n")
        return True
