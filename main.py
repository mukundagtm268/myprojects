#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import selenium
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException

from NAS_Libraries.robotlogger import RobotLogger
from NAS_Libraries.robotkeyword import keyword
from HDP_Libraries.locators import Locators as Loc

LOGGER = RobotLogger(__name__)


class HDP:
    def __init__(self):
        self.hdp_driver = None
        self.check_timeout = 120
        self.hdp_mouse_pointer = None

    @property
    def _get_selenium_version(self):
        return selenium.__version__

    def _load_mouse_pointer(self):
        """
        Lib to load mouse pointer with launch of HDP in browser
        """
        LOGGER.info('|___Load mouse pointer___|')

        self.hdp_mouse_pointer = ActionChains(self.hdp_driver)

        LOGGER.info('Loaded mouse pointer\n')
        return True

    @keyword('HDP: Launch browser')
    def launch_browser(self, url, chromedriver_path):
        """
        Lib to open URL in the browser and load driver and mouse pointers

        Arguments
        | url: URL to be opened
        | chromedriver_path: Executable path of chromedriver
        """
        LOGGER.info('|___Launch Browser___|')

        if self._get_selenium_version < '4.0.0':
            self.hdp_driver = webdriver.Chrome(
                executable_path=chromedriver_path)
        else:
            service = Service(executable_path=chromedriver_path)
            self.hdp_driver = webdriver.Chrome(service=service)
        self.hdp_driver.implicitly_wait(10)
        self.hdp_driver.maximize_window()
        self.hdp_driver.get(url)
        self._load_mouse_pointer()
        navigation_start = self.hdp_driver.execute_script(
            "return window.performance.timing.navigationStart")
        response_start = self.hdp_driver.execute_script(
            "return window.performance.timing.responseStart")
        dom_complete = self.hdp_driver.execute_script(
            "return window.performance.timing.domComplete")

        backend_performance = response_start - navigation_start
        frontend_performance = dom_complete - response_start

        LOGGER.debug(f"Back end: {backend_performance}")
        LOGGER.debug(f"Front end: {frontend_performance}")

        LOGGER.info('Launched browser\n')
        return self.hdp_driver, self.hdp_mouse_pointer

    @keyword('HDP: Validate current page title')
    def validate_current_page_title(self, driver, exp_title):
        """
        Lib to validate current web page title

        Arguments
        | driver: Web driver of HDP
        | exp_title: expected title to validate with current web page title
        """
        LOGGER.info('|___Validate current page title___|')

        webpage_title = driver.title
        if webpage_title not in exp_title:
            raise ValueError(f"Expected Title: {exp_title}"
                             f"Recieved Title: {webpage_title}")

        LOGGER.info("Current page title validated\n")
        return True

    @keyword('HDP: Validate loading page')
    def validate_loading_page(self, driver, timeout=None):
        """
        Lib to validate loading screen observed after any operations

        Arguments
        | driver: Web driver of HDP
        | timeout: time (in sec) to validate if screen is still loading
        """
        LOGGER.info('|___Validate loading page___|')

        timeout = timeout or self.check_timeout
        start_time = time.time()

        while True:
            if time.time() - start_time > int(timeout):
                raise ValueError("Screen is still loading after waiting")

            try:
                WebDriverWait(driver, 3).until(ec.presence_of_element_located((
                    By.CSS_SELECTOR, Loc.HDP_LOADING_PAGE_CSS)))
            except TimeoutException:
                break

            LOGGER.debug("Screen is still loading, retrying..")

        LOGGER.info("Screen loading is completed\n")
        return True

    @keyword('HDP: Close browser')
    def close_browser(self, driver):
        """
        Lib to close all tabs in the browser

        Arguments
        | driver: Web driver of HDP
        """
        LOGGER.info('|___Close browser___|')

        driver.quit()

        LOGGER.info('Successfully closed browser\n')
        return True
