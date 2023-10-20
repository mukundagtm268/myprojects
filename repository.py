#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

from NAS_Libraries.robotlogger import RobotLogger
from NAS_Libraries.robotkeyword import keyword
from HDP_Libraries.main import HDP
from HDP_Libraries.locators import Locators as Loc

LOGGER = RobotLogger(__name__)


class Repository:
    def __init__(self):
        self.hdp = HDP()

    @keyword('HDP: Repository: Detach repository')
    def detach_repository(self, driver, repo_name):
        """
        Lib to detach repository based on repo name

        Arguments
        | driver: Web driver of HDP
        | repo_name: Name of repository to be detached
        """
        LOGGER.info('|___Detach repository___|')

        driver.find_element(By.CSS_SELECTOR, Loc.HDP_REPOSITORY_CSS).click()

        # Detach Repository
        more_button = f"//span[contains(text(),'{repo_name}')]" \
                      f"/ancestor::div[3]/div[6]/div"
        driver.find_element(By.XPATH, more_button).click()
        driver.find_element(By.XPATH, Loc.HDP_DETACH_REPOSITORY_XPATH).click()
        driver.find_element(By.XPATH, Loc.HDP_OK_BUTTON_XPATH).click()
        self.hdp.validate_loading_page(driver)

        # Validate repository is detached
        driver.find_element(By.XPATH, more_button).click()
        validate_detach = driver.find_element(
            By.XPATH, Loc.HDP_REPOSITORY_DETACH_ATTACH_TEXT_XPATH).text
        if validate_detach == Loc.HDP_DETACH_TEXT:
            raise ValueError("Repository is not detached")

        LOGGER.info("Repository is detached successfully\n")
        return True

    @keyword('HDP: Repository: Attach repository')
    def attach_repository(self, driver, repo_name):
        """
        Lib to detach repository based on repo name

        Arguments
        | driver: Web driver of HDP
        | repo_name: Name of repository to be attached
        """
        LOGGER.info('|___Attach repository___|')

        driver.find_element(By.CSS_SELECTOR, Loc.HDP_REPOSITORY_CSS).click()

        # Attach Repository
        more_button = f"//span[contains(text(),'{repo_name}')]" \
                      f"/ancestor::div[3]/div[6]/div"
        driver.find_element(By.XPATH, more_button).click()
        driver.find_element(By.XPATH, Loc.HDP_ATTACH_REPOSITORY_XPATH).click()
        self.hdp.validate_loading_page(driver)

        # Validate repository is attached
        driver.find_element(By.XPATH, more_button).click()
        validate_attach = driver.find_element(
            By.XPATH, Loc.HDP_REPOSITORY_DETACH_ATTACH_TEXT_XPATH).text
        if validate_attach == Loc.HDP_ATTACH_TEXT:
            raise ValueError("Repository is not attached")

        LOGGER.info("Repository is attached successfully\n")
        return True

    @keyword('HDP: Repository: Delete repository')
    def delete_repository(self, driver, repo_name):
        """
        Lib to delete repository based on repo name

        Arguments
        | driver: Web driver of HDP
        | repo_name: Name of repository to be deleted
        """
        LOGGER.info('|___Delete repository___|')

        driver.find_element(By.CSS_SELECTOR, Loc.HDP_REPOSITORY_CSS).click()

        # Delete Repository
        more_button = f"//span[contains(text(),'{repo_name}')]" \
                      f"/ancestor::div[3]/div[6]/div"
        driver.find_element(By.XPATH, more_button).click()
        driver.find_element(By.XPATH, Loc.HDP_DELETE_REPOSITORY_XPATH).click()
        driver.find_element(By.XPATH,
                            Loc.HDP_DELETE_ACCEPT_REPOSITORY_XPATH).click()
        driver.find_element(By.XPATH, Loc.HDP_OK_BUTTON_XPATH).click()
        self.hdp.validate_loading_page(driver)

        # Validate repository is deleted
        WebDriverWait(driver, 20).until_not(ec.presence_of_element_located((
            By.XPATH, f"//span[contains(text(),'{repo_name}')]")))

        LOGGER.info("Repository is deleted successfully\n")
        return True

    @keyword('HDP: Repository: Delete all repositories')
    def delete_all_repositories(self, driver):
        """
        Lib to delete all repositories in HDP

        Arguments
        | driver: Web driver of HDP
        """
        LOGGER.info('|___Delete all repositories___|')

        driver.find_element(By.CSS_SELECTOR, Loc.HDP_REPOSITORY_CSS).click()
        # Delete all repositories
        total_repositories = driver.find_elements(
            By.CSS_SELECTOR, Loc.HDP_REPOSITORY_COUNT_CSS)
        for _ in range(1, len(total_repositories)+1):
            driver.find_element(By.CSS_SELECTOR,
                                Loc.HDP_REPOSITORY_MORE_BUTTON_CSS).click()
            driver.find_element(By.XPATH,
                                Loc.HDP_DELETE_REPOSITORY_XPATH).click()
            driver.find_element(By.XPATH,
                                Loc.HDP_DELETE_ACCEPT_REPOSITORY_XPATH).click()
            driver.find_element(By.XPATH, Loc.HDP_OK_BUTTON_XPATH).click()
            self.hdp.validate_loading_page(driver)

        # Validate all repositories deleted
        WebDriverWait(driver, 20).until(ec.visibility_of_element_located((
            By.XPATH, Loc.HDP_CREATE_REPOSITORY_XPATH)))

        LOGGER.info("Deleted all repositories\n")
        return True
