#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from NAS_Libraries.robotlogger import RobotLogger
from NAS_Libraries.robotkeyword import keyword
from HDP_Libraries.main import HDP
from HDP_Libraries.locators import Locators as Loc

LOGGER = RobotLogger(__name__)


class System:
    def __init__(self):
        self.hdp = HDP()

    @keyword('HDP: System: Validate HDP logs after NetBak login')
    def validate_hdp_logs_after_netbak_login(
            self, driver, inv_name, repo_name):
        """
        Lib to validate refresh inv, repo logs generated after NetBak login

        Arguments
        | driver: Web driver of HDP
        | inv_name: Inventory name used in Backup job creation
        | repo_name: Repository name used in backup job creation
        """
        LOGGER.info("|___Validate HDP logs after NetBak login___|")

        driver.find_element(By.CSS_SELECTOR, Loc.HDP_SYSTEM_CSS).click()
        self.hdp.validate_loading_page(driver)

        # Validate logs generated
        try:
            driver.find_element(By.CSS_SELECTOR, Loc.HDP_SYSTEM_LOGS_COUNT_CSS)
        except NoSuchElementException:
            raise ValueError("No HDP logs generated after NetBak login")

        # Get logs count
        logs_count = driver.find_elements(
            By.CSS_SELECTOR, Loc.HDP_SYSTEM_LOGS_COUNT_CSS)
        count = 0
        for i in range(1, len(logs_count)+1):
            if count == 2:
                break
            content = driver.find_element(
                By.XPATH, Loc.HDP_SYSTEM_LOGS_CONTENT_XPATH.format(i)).text
            if content in Loc.INV_REFRESH_LOGS.format(inv_name) or \
                    content in Loc.REPO_REFRESH_LOGS.format(repo_name):
                LOGGER.debug(f"Found expected HDP logs: {content}")
                count += 1

        # Validate both refresh logs generated
        if count != 2:
            raise ValueError("Expected HDP logs not generated")

        LOGGER.info("Validated HDP logs after NetBak login\n")
        return True

    @keyword('HDP: System: Get date time for HDP logs after NetBak login')
    def get_date_time_for_hdp_logs(self, driver, inv_name, repo_name):
        """
        Lib to get date time for the refresh logs generated after netBak login

        Arguments
        | driver: Web driver of HDP
        | inv_name: Inventory name used in Backup job creation
        | repo_name: Repository name used in backup job creation
        """
        LOGGER.info("|___Get date time for HDP logs after NetBak login___|")

        driver.find_element(By.CSS_SELECTOR, Loc.HDP_SYSTEM_CSS).click()
        self.hdp.validate_loading_page(driver)

        # # Get date time for refresh logs
        logs_count = driver.find_elements(
            By.CSS_SELECTOR, Loc.HDP_SYSTEM_LOGS_COUNT_CSS)
        count = 0
        date_time_logs = []
        for i in range(1, len(logs_count)+1):
            if count == 2:
                break
            content = driver.find_element(
                By.XPATH, Loc.HDP_SYSTEM_LOGS_CONTENT_XPATH.format(i)).text
            if content in Loc.INV_REFRESH_LOGS.format(inv_name) or \
                    content in Loc.REPO_REFRESH_LOGS.format(repo_name):
                LOGGER.debug(f"Found expected HDP logs: {content}")
                date_time = driver.find_element(
                    By.XPATH, Loc.HDP_SYSTEM_LOGS_DATE_TIME_XPATH.format(
                        i)).text
                date_time_logs.append(date_time)
                count += 1

        # Validate if date time logs are retrieved
        if len(date_time_logs) == 0:
            raise ValueError("Date time for HDP logs not retrieved")

        LOGGER.info(f"Date time for HDP logs retrieved: {date_time_logs}\n")
        return date_time_logs
