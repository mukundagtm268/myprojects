#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from NAS_Libraries.robotlogger import RobotLogger
from NAS_Libraries.robotkeyword import keyword
from HDP_Libraries.main import HDP
from HDP_Libraries.locators import Locators as Loc

LOGGER = RobotLogger(__name__)


class Inventory:
    def __init__(self):
        self.hdp = HDP()

    @keyword('HDP: Inventory: Delete inventory')
    def delete_inventory(self, driver, inventory_name):
        """
        Lib to delete inventory from HDP based on inv name

        Arguments
        | driver: Web driver of HDP
        | inventory_name: Name of inventory to be deleted
        """
        LOGGER.info('|___Delete inventory___|')

        driver.find_element(By.CSS_SELECTOR, Loc.HDP_INVENTORY_CSS).click()
        self.hdp.validate_loading_page(driver)
        try:
            driver.find_element(By.XPATH, Loc.HDP_WINDOWS_INV_XPATH).click()
        except NoSuchElementException:
            LOGGER.info('No inventory present in HDP, skipping delete')
            return True

        # Delete Inventory
        delete_xpath = f"//span[contains(text(),'{inventory_name}')]" \
                       f"/ancestor::div[3]/div[6]/div[1]/div[2]"
        driver.find_element(By.XPATH, delete_xpath).click()
        driver.find_element(By.XPATH, Loc.HDP_INV_DELETE_ACCEPT_XPATH).click()
        driver.find_element(By.XPATH, Loc.HDP_OK_BUTTON_XPATH).click()
        self.hdp.validate_loading_page(driver)

        # Validate Inventory is deleted
        WebDriverWait(driver, 20).until_not(ec.presence_of_element_located((
            By.XPATH, f"//span[contains(text(),'{inventory_name}')]")))

        LOGGER.info("Deleted inventory successfully\n")
        return True

    @keyword('HDP: Inventory: Delete all inventories')
    def delete_all_inventories(self, driver):
        """
        Lib to delete all inventories from HDP

        Arguments
        | driver: Web driver of HDP
        """
        LOGGER.info('|___Delete all inventories___|')

        driver.find_element(By.CSS_SELECTOR, Loc.HDP_INVENTORY_CSS).click()
        self.hdp.validate_loading_page(driver)
        try:
            driver.find_element(By.XPATH, Loc.HDP_WINDOWS_INV_XPATH).click()
        except NoSuchElementException:
            LOGGER.info('No inventory present in HDP, skipping delete')
            return True

        # Get inventory count and delete them
        inv_count = driver.find_elements(By.CSS_SELECTOR,
                                         Loc.HDP_INV_COUNT_CSS)
        for _ in range(1, len(inv_count)+1):
            driver.find_element(By.XPATH, Loc.HDP_DELETE_INV_XPATH).click()
            driver.find_element(By.XPATH,
                                Loc.HDP_INV_DELETE_ACCEPT_XPATH).click()
            driver.find_element(By.XPATH, Loc.HDP_OK_BUTTON_XPATH).click()
            self.hdp.validate_loading_page(driver)

        # Validate all inventories deleted
        WebDriverWait(driver, 20).until(ec.presence_of_element_located((
            By.XPATH, Loc.HDP_ADD_INVENTORY_XPATH)))

        LOGGER.info('Deleted all inventories successfully\n')
        return True
