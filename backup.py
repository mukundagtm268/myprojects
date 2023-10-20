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


class Backup:
    def __init__(self):
        self.hdp = HDP()

    @keyword('HDP: Backup: Get job status')
    def get_job_status(self, driver, mouse_driver, job_name):
        """
        Lib to get backup job status from HDP based on job name

        Arguments
        | driver: Web driver of HDP
        | mouse_driver: Mouse web driver of HDP
        | job_name: Name of backup job to be deleted
        """
        LOGGER.info('|___Get job status___|')

        self.hdp.validate_loading_page(driver)
        driver.find_element(By.CSS_SELECTOR, Loc.HDP_BACKUP_CSS).click()
        # Select backup job
        driver.find_element(
            By.XPATH, Loc.HDP_SELECT_JOB_NAME_XPATH.format(job_name)).click()
        self.hdp.validate_loading_page(driver)
        element = driver.find_element(By.CSS_SELECTOR,
                                      Loc.HDP_MOUSE_OUT_BACKUP_CSS)
        mouse_driver.move_to_element(element).click().perform()

        # Click hyperlink and get status
        link_xpath = f"//div[@class='job-list']//span[@data-tooltip=" \
                     f"'{job_name}']/ancestor::div[2]//span[@role='button']"
        try:
            driver.find_element(By.XPATH, link_xpath).click()
            job_status = driver.find_element(
                By.XPATH, Loc.HDP_BACKUP_HYPERLINK_STATUS_XPATH).text
        except NoSuchElementException:
            job_status = "Not started"

        LOGGER.info(f"Retrieved job status: {job_status}\n")
        return job_status

    @keyword('HDP: Backup: Validate job is stopped')
    def validate_job_is_stopped(self, driver, timeout=None):
        """
        Lib to validate if backup job is stopped

        Arguments
        | driver: Web driver of HDP
        | timeout: Time (in sec) to wait till job is stopped
        """
        LOGGER.info('|___Validate job is stopped___|')

        start_time = time.time()
        timeout = timeout or self.hdp.check_timeout
        driver.find_element(By.CSS_SELECTOR,
                            Loc.HDP_BACKUP_MORE_BUTTON_CSS).click()

        while True:
            if time.time() - start_time > int(timeout):
                raise ValueError("Job is not stopped")

            try:
                driver.find_element(By.XPATH, Loc.HDP_STOP_BACKUP_XPATH)
            except NoSuchElementException:
                break

            LOGGER.info("Job is still running, pending retry..")
            time.sleep(2)

        # Click back more button
        driver.find_element(By.CSS_SELECTOR,
                            Loc.HDP_BACKUP_MORE_BUTTON_CSS).click()

        LOGGER.info("Job is stopped successfully\n")
        return True

    @keyword('HDP: Backup: stop backup job')
    def stop_backup_job(self, driver, mouse_driver, job_name):
        """
        Lib to stop the running backup job

        Arguments
        | driver: Web driver of HDP
        | mouse_driver: Mouse web driver of HDP
        | job_name: Name of backup job to be deleted
        """
        LOGGER.info('|___Stop backup job___|')

        job_status = self.get_job_status(driver, mouse_driver, job_name)
        if job_status != Loc.HDP_JOB_RUNNING:
            LOGGER.info("Job is already stopped\n")
            return True

        # Select job
        driver.find_element(By.CSS_SELECTOR, Loc.HDP_BACKUP_CSS).click()
        driver.find_element(
            By.XPATH, Loc.HDP_SELECT_JOB_NAME_XPATH.format(job_name)).click()
        self.hdp.validate_loading_page(driver)

        # Stop job
        driver.find_element(By.CSS_SELECTOR,
                            Loc.HDP_BACKUP_MORE_BUTTON_CSS).click()
        driver.find_element(By.XPATH, Loc.HDP_STOP_BACKUP_XPATH).click()
        driver.find_element(By.XPATH, Loc.HDP_YES_BUTTON_XPATH).click()
        self.hdp.validate_loading_page(driver)

        # Validate job is stopped
        self.validate_job_is_stopped(driver)

        LOGGER.info("Job is stopped successfully\n")
        return True

    @keyword('HDP: Backup: Validate job is deleted')
    def validate_job_deleted(self, driver, job_name, timeout=None):
        """
        Lib to validate backup job is deleted

        Arguments
        | driver: Web driver of HDP
        | job_name: Name of backup job to be deleted
        | timeout: Time (in sec) to wait till job is deleted
        """
        LOGGER.info('|___Validate job is deleted___|')

        timeout = timeout or self.hdp.check_timeout
        start_time = time.time()

        while True:
            if time.time() - start_time > int(timeout):
                raise ValueError("Job is not deleted")

            try:
                driver.find_element(
                    By.XPATH,
                    Loc.HDP_SELECT_JOB_NAME_XPATH.format(job_name)).click()
            except NoSuchElementException:
                break

            LOGGER.info("Job is not deleted yet, pending retry..")
            time.sleep(2)

        LOGGER.info("Job is deleted successfully\n")
        return True

    @keyword('HDP: Backup: Delete backup job')
    def delete_backup_job(self, driver, mouse_driver, job_name):
        """
        Lib to delete backup job from HDP based on job name

        Arguments
        | driver: Web driver of HDP
        | mouse_driver: Mouse web driver of HDP
        | job_name: Name of backup job to be deleted
        """
        LOGGER.info('|___Delete backup job___|')

        driver.find_element(By.CSS_SELECTOR, Loc.HDP_BACKUP_CSS).click()
        # Select backup job
        driver.find_element(
            By.XPATH, Loc.HDP_SELECT_JOB_NAME_XPATH.format(job_name)).click()
        self.hdp.validate_loading_page(driver)
        element = driver.find_element(By.CSS_SELECTOR,
                                      Loc.HDP_MOUSE_OUT_BACKUP_CSS)
        mouse_driver.move_to_element(element).click().perform()

        # Stop the job if running
        self.stop_backup_job(driver, mouse_driver, job_name)

        # Delete Job
        driver.find_element(By.CSS_SELECTOR, 
                            Loc.HDP_BACKUP_MORE_BUTTON_CSS).click()
        driver.find_element(By.XPATH, Loc.HDP_DELETE_BACKUP_XPATH).click()
        driver.find_element(By.ID, Loc.HDP_ACCEPT_DELETE_BACKUP_ID).click()
        driver.find_element(By.XPATH, Loc.HDP_OK_BUTTON_XPATH).click()
        self.hdp.validate_loading_page(driver)

        # Validate job is deleted
        self.validate_job_deleted(driver, job_name)

        LOGGER.info('Job is deleted successfully\n')
        return True

    @keyword('HDP: Backup: Delete all backup jobs')
    def delete_all_backup_jobs(self, driver, mouse_driver):
        """
        Lib to delete all backup jobs

        Arguments
        | driver: Web driver of HDP
        | mouse_driver: Mouse web driver of HDP
        """
        LOGGER.info('|___Delete all backup jobs___|')

        self.hdp.validate_loading_page(driver)
        driver.find_element(By.CSS_SELECTOR, Loc.HDP_BACKUP_CSS).click()
        jobs_count = driver.find_elements(By.XPATH,
                                          Loc.HDP_BACKUP_JOBS_COUNT_XPATH)
        for _ in range(1, len(jobs_count)-1):
            job_name = driver.find_element(By.XPATH,
                                           Loc.HDP_JOB_NAME_XPATH).text
            self.delete_backup_job(driver, mouse_driver, job_name)

        LOGGER.info("Deleted all jobs successfully\n")
        return True

    @keyword('HDP: Backup: Get HDP job volumes')
    def get_hdp_job_volumes(self, driver, job_name):
        """
        Lib to get volumes in backup job page

        Arguments
        | driver: Web driver of HDP
        | job_name: Backup Job name
        """
        LOGGER.info("|___Get HDP job volumes___|")

        # Select backup job
        driver.find_element(By.CSS_SELECTOR, Loc.HDP_BACKUP_CSS).click()
        driver.find_element(
            By.XPATH, Loc.HDP_SELECT_JOB_NAME_XPATH.format(job_name)).click()
        self.hdp.validate_loading_page(driver)

        # Get Volumes and Volumes count used in backup job
        volumes_count = driver.find_elements(
            By.XPATH, Loc.HDP_BACKUP_VOLUME_COUNT_XPATH)
        LOGGER.debug(f"Volumes count: {volumes_count}")
        volumes = []
        for volume in range(1, len(volumes_count)+1):
            volumes.append(driver.find_element(
                By.XPATH, Loc.HDP_BACKUP_VOLUMES_TEXT_XPATH.format(volume)).
                           text)
            LOGGER.info(f"Volumes: {volumes}")

        LOGGER.info(f"Retrieved HDP backup volumes: {volumes}\n")
        return volumes

    @keyword('HDP: backup: Disable backup job')
    def disable_backup_job(self, driver, job_name):
        """
         Lib is to disable the backup job

        Arguments
        | driver: Web driver of HDP
        | job_name: Backup Job name
        """
        LOGGER.info("|___Disable backup job___|")

        # Select backup job
        driver.find_element(By.CSS_SELECTOR, Loc.HDP_BACKUP_CSS).click()
        driver.find_element(
            By.XPATH, Loc.HDP_SELECT_JOB_NAME_XPATH.format(job_name)).click()
        self.hdp.validate_loading_page(driver)

        # Click back more button
        driver.find_element(By.CSS_SELECTOR,
                            Loc.HDP_BACKUP_MORE_BUTTON_CSS).click()

        # Click Disable button
        driver.find_element(By.XPATH, Loc.HDP_DISABLE_BACKUP_XPATH).click()
        driver.find_element(By.XPATH, Loc.HDP_OK_BUTTON_XPATH).click()
        self.hdp.validate_loading_page(driver)
        driver.find_element(By.XPATH, Loc.HDP_OK_BUTTON_XPATH).click()
        backup_status = driver.find_element(
            By.XPATH, Loc.HDP_DISABLED_BACKUP_STRING_XPATH).text
        if backup_status not in Loc.HDP_EXPECTED_JOB_STATUS:
            raise ValueError(f"Backup job not found in expected status,\n"
                             f"obtained backup job status {backup_status}\n"
                             f"Expected backup job status "
                             f"{Loc.HDP_EXPECTED_JOB_STATUS}")

        LOGGER.info("Disabled backup job")
        return True

    @keyword('HDP: backup: Enable backup job')
    def enable_backup_job(self, driver, job_name):
        """
         Lib is to enable the backup job

        Arguments
        | driver: Web driver of HDP
        | job_name: Backup Job name
        """
        LOGGER.info("|___Enable backup job___|")

        # Select backup job
        driver.find_element(By.CSS_SELECTOR, Loc.HDP_BACKUP_CSS).click()
        driver.find_element(
            By.XPATH, Loc.HDP_SELECT_JOB_NAME_XPATH.format(job_name)).click()
        self.hdp.validate_loading_page(driver)

        # Click back more button
        driver.find_element(By.CSS_SELECTOR,
                            Loc.HDP_BACKUP_MORE_BUTTON_CSS).click()

        # Click Enable button
        driver.find_element(By.XPATH, Loc.HDP_ENABLE_BACKUP_XPATH).click()
        driver.find_element(By.XPATH, Loc.HDP_OK_BUTTON_XPATH).click()
        self.hdp.validate_loading_page(driver)
        driver.find_element(By.XPATH, Loc.HDP_OK_BUTTON_XPATH).click()
        backup_status = driver.find_element(
            By.XPATH, Loc.HDP_ENABLED_BACKUP_STRING_XPATH).text
        if backup_status in Loc.HDP_EXPECTED_JOB_STATUS:
            raise ValueError(f"Backup job not found in expected status,\n"
                             f"obtained backup job status {backup_status}\n"
                             f"Expected backup job status "
                             f"{Loc.HDP_EXPECTED_JOB_STATUS}")

        LOGGER.info("Enabled backup job")
        return True
