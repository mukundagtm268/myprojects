#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import time
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.common.exceptions import InvalidSessionIdException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys

from NetBak_Libraries.locators import NetBakLocators as Loc

from NAS_Libraries.robotlogger import RobotLogger
from NAS_Libraries.robotkeyword import keyword

LOGGER = RobotLogger(__name__)


class NetBak:
    def __init__(self):
        self.driver = None
        self.check_timeout = 120
        self.mouse_pointer = None

    @property
    def _get_selenium_version(self):
        return selenium.__version__

    def _load_mouse_pointer(self):
        """
        Lib to load mouse pointer with launch of NetBak app
        """
        LOGGER.info('|___Load mouse pointer___|')

        self.mouse_pointer = ActionChains(self.driver)

        LOGGER.info('Loaded mouse pointer\n')
        return True

    @keyword('NetBak: Launch app')
    def launch_app(self, chromedriver_path, app_path):
        """
        Lib to launch (start) Netback app
        Arguments
        | chromedriver_path: Executable path of chromedriver
        | app_path: Executable path of NetBak app
        """
        LOGGER.info('|___Launching app___|')

        opts = Options()
        opts.binary_location = app_path
        if self._get_selenium_version < '4.0.0':
            self.driver = webdriver.Chrome(executable_path=chromedriver_path,
                                           options=opts)
        else:
            service = Service(executable_path=chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=opts)
        self._load_mouse_pointer()

        # Validate app is launched
        try:
            WebDriverWait(self.driver, 20).until(
                ec.presence_of_element_located((
                    By.CLASS_NAME, Loc.START_BUTTON_CLS)))
        except TimeoutException:
            raise ValueError("App is not launched")

        LOGGER.info('App launched successfully\n')
        return True

    def _enter_values(self, web_element, text):
        """
        Lib to enter (write) values as strings based on web element

        Arguments
        | web_element: Web element where value to be entered
        | text: text string to be entered in web element
        """
        LOGGER.info(f'|___Entering {text} in web element___|')

        element = self.driver.find_element(By.NAME, web_element)
        element.clear()
        element.send_keys(text)

        LOGGER.info(f'Updated {text} in web element\n')
        return True

    @keyword('NetBak: Login app')
    def login_app(self, nas_ip, username, password):
        """
        Lib to log in to NetBak app

        Arguments
        | nas_ip: NAS IP to be entered to connect to app
        | username: Username of the NAS
        | password: Password of the NAS
        """
        LOGGER.info('|___Login to app___|')

        # Enter NAS IP
        self.driver.find_element(By.CLASS_NAME, Loc.START_BUTTON_CLS).click()
        self._enter_values(Loc.NAS_IP_NAME, nas_ip)
        self.driver.find_element(By.XPATH, Loc.START_PAGE_NEXT_BUTTON).click()
        WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((
            By.NAME, Loc.PASSWORD_NAME)))

        # Enter NAS credentials and submit
        self._enter_values(Loc.NAS_IP_NAME, username)
        self._enter_values(Loc.PASSWORD_NAME, password)
        self.driver.find_element(By.CLASS_NAME, Loc.LOGIN_BUTTON_CLS).click()

        self.validate_different_ip_alert()
        # Validate app logged in
        try:
            WebDriverWait(self.driver, 60).until(ec.element_to_be_clickable((
                By.CSS_SELECTOR, Loc.DEVICE_TARGET_TAB_CSS)))
        except TimeoutException:
            LOGGER.info('Backup job is already created, '
                        'validating through backup overview page element')
            # First time login takes 1 min to go to inventory screen
            try:
                WebDriverWait(self.driver, 30).until(
                    ec.element_to_be_clickable((By.CSS_SELECTOR,
                                                Loc.OVERVIEW_TAB_CSS)))
            except TimeoutException:
                raise ValueError("Not able to login to app")

        LOGGER.info('Logged in to app successfully\n')
        return True

    @keyword('NetBak: Validate invalid port alert')
    def validate_invalid_port_alert(self, nas_ip):
        """
        Lib to identify the invalid ip alerts

        Arguments
        | nas_ip: NAS IP to be entered to connect to app
        """
        LOGGER.info('|___Validating the invalid port alert___|')

        self.driver.find_element(By.CLASS_NAME, Loc.START_BUTTON_CLS).click()
        self._enter_values(Loc.NAS_IP_NAME, nas_ip)
        self.driver.find_element(By.XPATH, Loc.START_PAGE_NEXT_BUTTON).click()

        # Validate Alert window present
        try:
            WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((
                    By.CLASS_NAME, Loc.ALERT_WINDOW_CLS)))
        except TimeoutException:
            raise ValueError("Invalid port alert window not present")

        # Validate invalid port alert text
        alert = self.driver.find_element(By.CLASS_NAME,
                                         Loc.ALERT_CONTENT_CLS).text
        if alert != Loc.FAIL_TO_CONNECT_NAS_TEXT:
            raise ValueError('Alert retrieved is not the expected alert'
                             f'Expected alert: {Loc.FAIL_TO_CONNECT_NAS_TEXT}'
                             f'Retrieved alert: {alert}')

        LOGGER.info('Expected alert text found successfully\n')
        return True

    @keyword('NetBak: Validate different IP alert')
    def validate_different_ip_alert(self):
        """
        lib to validate alert after trying to log in with new IP when
        NetBak is already logged in with different IP
        """
        LOGGER.info('|___Validate different IP alert___|')

        try:
            WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located(
                    (By.CLASS_NAME, "alert-window")))
            self.driver.find_element(
                By.CLASS_NAME, "qcss-button.ok-button.Remember-Me").click()

            LOGGER.info("Logging with different NAS IP\n")
        except TimeoutException:
            LOGGER.info("Logging into same NAS\n")

        return True

    @keyword('NetBak: Close app')
    def close_app(self):
        """
        Lib to close the driver and app
        """
        LOGGER.info('|___Close app___|')

        try:
            windows = self.driver.window_handles
        except InvalidSessionIdException:
            LOGGER.info("No app window open currently to close")
            return True
        LOGGER.debug(f"Open windows: {windows}")
        self.driver.close()

        LOGGER.info('App closed successfully\n')
        return True

    @keyword('NetBak: Validate invalid NAS IPs')
    def validate_invalid_ip(self, nas_ips):
        """
        Lib to validate invalid NAS IPs

        Arguments
        | nas_ips: List of invalid ips to be validated
        |          eg: [10.24.ab.cd, abc.12.14.c ]
        """
        LOGGER.info('|___Validate invalid NAS IPs___|')

        # Validate if app is started or already in login screen
        try:
            self.driver.find_element(By.CLASS_NAME,
                                     Loc.START_BUTTON_CLS).click()
        except NoSuchElementException:
            LOGGER.info('App is already in log in screen')
        for nas_ip in nas_ips:
            # Enter NAS IP
            self._enter_values("NAS IP", nas_ip)
            self.driver.find_element(By.XPATH,
                                     Loc.START_PAGE_NEXT_BUTTON).click()
            # Validate loading screen
            self.validate_nb_loading_page()

            # Validate invalid IP text
            invalid_text = self.driver.find_element(
                By.CSS_SELECTOR, Loc.INVALID_IP_ALERT_CSS).text

            if invalid_text not in (Loc.FAIL_TO_CONNECT_NAS_TEXT,
                                    Loc.INVALID_IP_TEXT,
                                    Loc.NAS_NOT_CONNECT_TEXT):
                raise ValueError(f'Invalid IP text does not match:'
                                 f'Received text: {invalid_text}')

            # Click cancel button
            self.driver.find_element(By.CSS_SELECTOR,
                                     Loc.NO_BUTTON_CSS).click()

        LOGGER.info('Validated list of invalid IPs successfully\n')
        return True

    @keyword("NetBak: Select volume for backup")
    def select_volume(self, drive_letter):
        """
        Lib for Selecting Volumes For Backup

        Arguments
        | drive_letter: Drive Letter To Backup Ex: D,E etc..
        """
        LOGGER.info("|___Selecting the required volume to be backed up___|")

        drives = drive_letter.split(",")
        # Deselect all volumes and select the required volumes
        self.driver.find_element(By.XPATH, Loc.ALL_VOLUMES_XPATH).click()
        for drive in drives:
            drive = drive.upper()
            self.driver.find_element(
                By.XPATH, Loc.USER_VOLUME_XPATH.format(drive)).click()

        LOGGER.info(f"Volume {drive_letter} Selected\n")
        return True

    @keyword("NetBak: Create repository")
    def create_repository(self, shared_folder, repo_name):
        """
        Lib for Creating Repository

        Arguments
        | shared_folder: Shared folder name to create repository
        | repo_name: Repository name to be created
        """
        LOGGER.info("|___Creating Repository___|")

        # Navigating to repository page
        self.driver.find_element(By.CSS_SELECTOR,
                                 Loc.SELECT_REPO_BUTTON_CSS).click()
        # Select browse button
        self.validate_nb_loading_page()
        self.driver.find_element(By.CLASS_NAME,
                                 Loc.CREATE_NEW_REPO_BUTTON_CLS).click()
        self.driver.find_element(By.XPATH,
                                 Loc.BROWSE_SHARED_FOLDER_BUTTON_XPATH).click()

        # Validate repo list is loaded
        self.validate_nb_loading_page()
        try:
            WebDriverWait(self.driver, 60).until(
                ec.presence_of_element_located((
                    By.XPATH, Loc.PUBLIC_SHARED_FOLDER_XPATH)))
        except TimeoutException:
            raise ValueError("Public shared folder is not loaded in list")

        # Selecting SharedFolder
        self.driver.find_element(By.XPATH,
                                 Loc.SELECT_USER_SHARED_FOLDER_XPATH.format(
                                     shared_folder)).click()
        self.driver.find_element(By.XPATH,
                                 Loc.SELECT_SHARED_FOLDER_BUTTON_XPATH).click()

        # Enter repository name and click add
        self._enter_values("name", repo_name)
        self.driver.find_element(By.XPATH, Loc.CREATE_REPO_BUTTON).click()
        # Validate repo selected after click add
        try:
            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((
                    By.CSS_SELECTOR, Loc.CHECK_REPO_SELECTED_CSS)))
        except TimeoutException:
            raise ValueError("Repo is not selected")

        # Select repository and validate home page
        self.driver.find_element(By.XPATH,
                                 Loc.SELECT_CREATED_REPO_BUTTON_XPATH).click()
        try:
            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((
                    By.CSS_SELECTOR, Loc.REPO_SELECTED_VALIDATION_CSS)))
        except TimeoutException:
            raise ValueError("Repo is not reflected in home page")

        LOGGER.info('Repository selected successful\n')
        return True

    @keyword("NetBak: Create backup job")
    def create_backup_job(self, shared_folder, repo_name, drive_letter=None):
        """
        Lib for Creating Backup Job

        Arguments
        | drive_letter: Drive Letter To Backup Ex: D,E etc..
        | shared_folder: Shared folder name to create repository
        | repo_name: Repository name to be created
        """
        LOGGER.info("|___Creating Backup Job___|")

        # Validate configs are cleared and job is not present
        try:
            if self.driver.find_element(By.CSS_SELECTOR, Loc.OVERVIEW_TAB_CSS):
                raise ValueError(
                    "Configs are not cleared and job already present")
        except NoSuchElementException:
            pass
        # If there is no partition or user only wants to back up C drive
        # So need not select any drive, C is selected by default
        if drive_letter is not None:
            self.select_volume(drive_letter)
        # Select Repository
        self.create_repository(shared_folder, repo_name)
        # Wait for the next button to be clickable
        try:
            WebDriverWait(self.driver, 60).until(
                ec.element_to_be_clickable((
                    By.CSS_SELECTOR, Loc.REPO_SELECTED_VALIDATION_CSS)))
        except TimeoutException:
            raise ValueError("Repo is not reflected in home page, "
                             "next button not clickable")

        # Click next button till job is created
        [self.driver.find_element(
            By.CLASS_NAME, Loc.BACKUP_NEXT_BUTTON).click() for _ in range(5)]

        # Validate job is created
        try:
            WebDriverWait(self.driver, 60).until(
                ec.presence_of_element_located((
                    By.CSS_SELECTOR, Loc.OVERVIEW_TAB_CSS)))
        except TimeoutException:
            raise ValueError("Job is not reflected in home page")

        LOGGER.info("Backup job created\n")
        return True

    @keyword("NetBak: Schedule daily backup job")
    def schedule_daily_backup_job(self, schedule_option, shared_folder,
                                  repo_name, drive_letter=None):
        """
        Lib for Schedule daily backup job

        Arguments
        | schedule_option: Scheduling option for the backup job
        |                  eg "Every day", "Every weekday", "Every weekend"
        | drive_letter: Drive Letter To Backup Ex: D,E etc..
        | shared_folder: Shared folder name to create repository
        | repo_name: Repository name to be created
        """
        LOGGER.info("|___Schedule daily backup job___|")

        # Validate configs are cleared and job is not present
        try:
            if self.driver.find_element(By.CSS_SELECTOR, Loc.OVERVIEW_TAB_CSS):
                raise ValueError(
                    "Configs are not cleared and job already present")
        except NoSuchElementException:
            pass
        # If there is no partition or user only wants to back up C drive
        # So need not select any drive, C is selected by default
        if drive_letter is not None:
            self.select_volume(drive_letter)
        # Select Repository
        self.create_repository(shared_folder, repo_name)

        # Validate Next button is available and click button
        try:
            WebDriverWait(self.driver, 20).until(
                ec.element_to_be_clickable((
                    By.CLASS_NAME, Loc.BACKUP_NEXT_BUTTON)))
        except TimeoutException:
            raise ValueError("Next button is not clickable")
        self.driver.find_element(By.CLASS_NAME, Loc.BACKUP_NEXT_BUTTON).click()

        # Select daily schedule option
        self._select_daily_schedule_options(schedule_option)

        # Click on next buttons till job is created
        [self.driver.find_element(By.CLASS_NAME,
                                  Loc.BACKUP_NEXT_BUTTON).click()
         for _ in range(4)]

        # Validate if job is created
        try:
            WebDriverWait(self.driver, 50).until(
                ec.element_to_be_clickable((
                    By.CSS_SELECTOR, Loc.OVERVIEW_TAB_CSS)))
        except TimeoutException:
            raise ValueError("Job is not created")

        LOGGER.info("Schedule daily backup job successful\n")
        return True

    def _select_daily_schedule_options(self, schedule_option):
        """
        Lib to select daily schedule options

        Arguments
        | schedule_option: Scheduling option for the backup job
        |                  eg "Every day", "Every weekday", "Every weekend"
        """
        LOGGER.info('|___Select daily schedule options___|')

        self.driver.find_element(By.CSS_SELECTOR, 
                                 Loc.SCHEDULE_DAILY_BACKUP_OPTION_CSS).click()
        self.driver.find_element(By.XPATH,
                                 Loc.DAILY_TIME_DROPDOWN_XPATH).click()
        self.driver.find_element(By.CSS_SELECTOR,
                                 Loc.SELECT_DAILY_TIME_CSS).click()
        self.driver.find_element(By.CSS_SELECTOR,
                                 Loc.SELECT_WEEKDAY_DROPDOWN_CSS).click()
        self.driver.find_element(
            By.XPATH, Loc.SELECT_WEEKDAY_XPATH.format(schedule_option)).click()

        LOGGER.info('Selected schedule options\n')
        return True

    @keyword("NetBak: Schedule monthly backup job")
    def schedule_monthly_backup_job(
            self, shared_folder, repo_name, drive_letter=None):
        """
        Lib for Schedule Monthly backup job

        Arguments
        | drive_letter: Drive Letter To Backup Ex: D,E etc..
        | shared_folder: Shared folder name to create repository
        | repo_name: Repository name to be created
        """
        LOGGER.info("|___Schedule monthly backup job___|")

        # Validate configs are cleared and job is not present
        try:
            if self.driver.find_element(By.CSS_SELECTOR, Loc.OVERVIEW_TAB_CSS):
                raise ValueError(
                    "Configs are not cleared and job already present")
        except NoSuchElementException:
            pass
        # If there is no partition or user only wants to back up C drive
        # So need not select any drive, C is selected by default
        if drive_letter is not None:
            self.select_volume(drive_letter)
        # Select Repository
        self.create_repository(shared_folder, repo_name)

        # Wait till next button is available and click
        try:
            WebDriverWait(self.driver, 20).until(
                ec.element_to_be_clickable((
                    By.CLASS_NAME, Loc.BACKUP_NEXT_BUTTON)))
        except TimeoutException:
            raise ValueError("Next Button is not clickable")
        self.driver.find_element(By.CLASS_NAME, Loc.BACKUP_NEXT_BUTTON).click()

        # Select monthly schedule
        self._select_monthly_schedule_options()

        # Click on next buttons till job is created
        [self.driver.find_element(By.CLASS_NAME,
                                  Loc.BACKUP_NEXT_BUTTON).click()
         for _ in range(4)]

        # Validate job is created
        try:
            WebDriverWait(self.driver, 50).until(
                ec.element_to_be_clickable((
                    By.CSS_SELECTOR, Loc.OVERVIEW_TAB_CSS)))
        except TimeoutException:
            raise ValueError("Job is not created")

        LOGGER.info("Scheduling monthly backup job successful\n")
        return True

    def _select_monthly_schedule_options(self):
        """
        Lib to select monthly schedule options
        """
        LOGGER.info('|___Select monthly schedule options___|')

        self.driver.find_element(By.CSS_SELECTOR,
                                 Loc.SELECT_MONTHLY_OPTION_CSS).click()
        self.driver.find_element(By.XPATH,
                                 Loc.MONTHLY_TIME_DROPDOWN_XPATH).click()
        self.driver.find_element(By.CSS_SELECTOR, Loc.MONTHLY_TIME_CSS)
        self.driver.find_element(By.XPATH,
                                 Loc.MONTHLY_DATE_DROPDOWN_XPATH).click()
        self.driver.find_element(By.CSS_SELECTOR,
                                 Loc.SELECT_MONTHLY_DATE_XPATH).click()

        LOGGER.info('Selected monthly schedule options\n')
        return True

    @keyword("NetBak: Start backup job")
    def start_backup_job(self, rerun=False):
        """
        Lib to start the backup job

        Arguments
        | rerun: multiple backup job handled with optional argument
        """
        LOGGER.info("|___Start Running Backup Job___|")

        # Validate loading screen
        self.validate_nb_loading_page()

        # Validate job already running
        status = self.driver.find_element(By.CLASS_NAME,
                                          Loc.BACKUP_STATUS_CLS).text
        if status == Loc.BACKUP_JOB_RUNNING_TEXT:
            LOGGER.info("Job already running, skipping start job")
            return True

        # Click button to run job
        self.driver.find_element(By.CLASS_NAME,
                                 Loc.START_BACKUP_BUTTON_CLS).click()
        # Validate job has started running
        if rerun:
            self.validate_expected_backup_job_status(
                timeout=150, expected_status='Finalizing')
        else:
            self.validate_expected_backup_job_status(timeout=150)

        LOGGER.info("Backup Job Started\n")
        return True

    @keyword('NetBak: Validate expected backup job status')
    def validate_expected_backup_job_status(self, timeout=None,
                                            expected_status="Running"):
        """
        Lib to validate if backup job has started running

        Arguments
        | timeout: Time to wait till job status is reflected as running
        | expected_status: Expected status of the backup job to be validated
        """
        LOGGER.info('|___Validate expected backup job status___|')

        timeout = timeout or self.check_timeout
        start_time = time.time()
        while True:
            if time.time() - start_time > int(timeout):
                raise ValueError(f"Backup job is not in "
                                 f"{expected_status} state")
            job_status = self.driver.find_element(By.CLASS_NAME,
                                                  Loc.BACKUP_STATUS_CLS).text
            LOGGER.debug(f'Current job status:{job_status}')
            if expected_status in job_status:
                break
            LOGGER.info(f"Backup job is still not found in {expected_status} "
                        f"state, pending retry...")
            time.sleep(2)

        LOGGER.info(f'Job is found in {expected_status} state\n')
        return True

    @keyword("NetBak: Check backup job status")
    def check_backup_job_status(self):
        """
        Lib for checking backup job status
        """
        LOGGER.info("|___Check Backup Job Status___|")

        status = self.driver.find_element(By.CLASS_NAME,
                                          Loc.BACKUP_STATUS_CLS).text
        backup_size = self.driver.find_element(By.CLASS_NAME,
                                               Loc.BACKUP_SIZE_CLS).text
        last_backup_time = self.driver.find_element(
            By.CLASS_NAME, Loc.LAST_BACKUP_TIME_CLS).text
        LOGGER.debug(f"Status is {status}")
        LOGGER.debug(f'Backup size is {backup_size}')
        LOGGER.debug(f'Last Backup time is {last_backup_time}')

        LOGGER.info("checking backup job status completed\n")
        return True

    @keyword("NetBak: Stop backup job")
    def stop_backup_job(self):
        """
        Lib to stop the backup job
        """
        LOGGER.info("|___Stop Backup Job___|")

        # Validate job already stopped
        status = self.driver.find_element(By.CLASS_NAME,
                                          Loc.BACKUP_STATUS_CLS).text
        if status == Loc.BACKUP_JOB_STOPPED_TEXT:
            LOGGER.info("Job already stopped, skipping stop job")
            return True

        # Wait until the text "Stop Backup" appears in the span tag
        try:
            WebDriverWait(self.driver, 30).until(
                ec.text_to_be_present_in_element((
                    By.TAG_NAME, "span"), "Stop Backup"))
        except TimeoutException:
            raise ValueError("Stop backup is not reflected")
        # Click on the element with the text "Stop Backup"
        self.driver.find_element(By.XPATH,
                                 Loc.STOP_BACKUP_XPATH).click()
        try:
            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((
                    By.XPATH, Loc.JOB_STOPPED_XPATH)))
        except TimeoutException:
            raise ValueError("Job is not stopped after clicking stop button")

        LOGGER.info("Backup job is stopped\n")
        return True

    @keyword('NetBak: Validate LAN fields')
    def validate_lan_fields(self):
        """
        Lib to validate LAN field names
        """
        LOGGER.info('|___Validate LAN field names___|')

        expected_fields = ['NAS Name', 'IP Address', 'Model',
                           'Firmware Version']

        self.driver.find_element(By.CLASS_NAME, Loc.START_BUTTON_CLS).click()
        # Click LAN button
        self.driver.find_element(By.CSS_SELECTOR, Loc.LAN_BUTTON_CSS).click()
        try:
            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((
                    By.CSS_SELECTOR, Loc.LAN_HEADERS_CSS)))
        except TimeoutException:
            raise ValueError("LAN headers are not reflected")

        # Validate LAN fields
        lan_fields = self.driver.find_elements(By.CSS_SELECTOR,
                                               Loc.LAN_HEADERS_CSS)
        for count in range(1, len(lan_fields)+1):
            element_text = self.driver.find_element(
                By.XPATH, Loc.LAN_EACH_HEADER_TEXT_XPATH.format(count)).text
            if element_text not in expected_fields:
                raise ValueError("LAN fields are not the expected fields")

        # Validate MAC Address field
        mac_element = self.driver.find_element(
            By.XPATH, Loc.LAN_MACADDRESS_HEADER_TEXT_XPATH).text
        if mac_element != 'MAC Address':
            raise ValueError('LAN field MAC is not the expected field')

        LOGGER.info('Validated LAN fields successfully!!\n')
        return True

    @keyword('NetBak: Login app using LAN')
    def login_app_using_lan(self, nas_ip, username, password):
        """
        Lib to log in to NAS using LAN option

        Arguments
        | nas_ip: IP of NAS
        | username: Username of NAS
        | password: Password of NAS
        """
        LOGGER.info('|___Login app using LAN___|')

        # Check app is already launched
        try:
            self.driver.find_element(By.CLASS_NAME,
                                     Loc.START_BUTTON_CLS).click()
        except NoSuchElementException:
            LOGGER.info("App is already launched, skipping click start button")

        # Click LAN button
        self.driver.find_element(By.CSS_SELECTOR, Loc.LAN_BUTTON_CSS).click()

        # Validate NAS IPs are populated in LAN
        try:
            WebDriverWait(self.driver, 50).until(ec.element_to_be_clickable((
                By.CSS_SELECTOR, Loc.LAN_NAS_DATA_CSS)))
        except TimeoutException:
            raise ValueError("NAP IPs are not present in LAN option, connect "
                             "LAN to login through LAN option")

        # Scroll to NAS IP and select IP
        element = self.driver.find_element(
            By.XPATH, Loc.LAN_SELECT_NAS_IP_XPATH.format(nas_ip))
        self.mouse_pointer.move_to_element(element).click().perform()
        self.driver.find_element(By.CSS_SELECTOR,
                                 Loc.LAN_SELECT_BUTTON_CSS).click()
        # Validate loading screen
        self.validate_nb_loading_page()

        # Enter NAS credentials and submit
        self._enter_values(Loc.NAS_IP_NAME, username)
        self._enter_values(Loc.PASSWORD_NAME, password)
        self.driver.find_element(By.CLASS_NAME, Loc.LOGIN_BUTTON_CLS).click()

        # Accept SSL certificate alert
        self._accept_ssl_certificate_alert()

        # Validate login is successful
        try:
            WebDriverWait(self.driver, 50).until(
                ec.presence_of_element_located((
                    By.CSS_SELECTOR, Loc.DEVICE_TARGET_TAB_CSS)))
        except TimeoutException:
            LOGGER.info('Backup job is already created, '
                        'validating through backup overview page element')
            try:
                WebDriverWait(self.driver, 50).until(
                    ec.presence_of_element_located((
                        By.CSS_SELECTOR, Loc.OVERVIEW_TAB_CSS)))
            except TimeoutException:
                raise ValueError("App is not logged in using LAN")

        LOGGER.info('Logged in to NAS using LAN\n')
        return True

    def _accept_ssl_certificate_alert(self):
        """
        Lib to accept SSL certificate alert popped up if we try to log in
        using LAN
        """
        LOGGER.info('|___Accept SSL certificate___|')

        try:
            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((
                    By.CLASS_NAME, Loc.ALERT_CONTENT_CLS)))
        except TimeoutException:
            raise ValueError("SSL alert is not present")
        self.driver.find_element(By.CSS_SELECTOR, Loc.OK_BUTTON_CSS).click()

        try:
            WebDriverWait(self.driver, 10).until(
                ec.invisibility_of_element_located((
                    By.CLASS_NAME, Loc.ALERT_CONTENT_CLS)))
        except TimeoutException:
            raise ValueError("Alert content is still visible after accept")

        LOGGER.info("Accepted SSL certificate alert\n")
        return True

    @keyword('NetBak: Validate invalid usernames')
    def validate_invalid_usernames(self, nas_ip, invalid_usernames, password):
        """
        Lib to validate invalid usernames of NAS

        Arguments
        | nas_ip: IP of NAS
        | invalid_usernames: List of invalid usernames to be validated
        | password: Password for NAS
        """
        LOGGER.info('|___Validate invalid usernames___|')

        # Validate if app is already launched
        try:
            # Enter NAS IP
            self.driver.find_element(By.CLASS_NAME,
                                     Loc.START_BUTTON_CLS).click()
            self._enter_values(Loc.NAS_IP_NAME, nas_ip)
            self.driver.find_element(By.XPATH,
                                     Loc.START_PAGE_NEXT_BUTTON).click()
            WebDriverWait(self.driver, 20).until(
                ec.presence_of_element_located((
                    By.NAME, Loc.PASSWORD_NAME)))
        except NoSuchElementException:
            LOGGER.info('Start button not found, app is already launched, '
                        'Skipping entering NAS login details')

        # Validate invalid usernames
        for username in invalid_usernames:
            self._enter_values(Loc.NAS_IP_NAME, username)
            self._enter_values(Loc.PASSWORD_NAME, password)
            self.driver.find_element(By.CLASS_NAME,
                                     Loc.LOGIN_BUTTON_CLS).click()
            try:
                WebDriverWait(self.driver, 120).until(
                    ec.presence_of_element_located((
                        By.CLASS_NAME, Loc.ALERT_WINDOW_CLS)))
            except TimeoutException:
                raise ValueError("Invalid user alert window is not located")
            # Validate invalid credential alert
            invalid_alert = self.driver.find_element(
                By.CSS_SELECTOR, Loc.INVALID_CREDENTIALS_ALERT_CSS).text

            if Loc.FAILED_TO_AUTHENTICATE_TEXT not in invalid_alert:
                raise ValueError('Invalid credentials alert not found')
            self.driver.find_element(By.CSS_SELECTOR,
                                     Loc.NO_BUTTON_CSS).click()

        LOGGER.info('Validated invalid usernames successfully\n')
        return True

    @keyword('NetBak: Validate invalid passwords')
    def validate_invalid_passwords(self, nas_ip, username, invalid_passwords):
        """
        Lib to validate invalid passwords of NAS

        Arguments
        | nas_ip: IP of NAS
        | username: Username of NAS
        | invalid_passwords: List of invalid passwords to be validated
        """
        LOGGER.info('|___Validate invalid passwords___|')

        # Validate if app is already launched
        try:
            # Enter NAS IP
            self.driver.find_element(By.CLASS_NAME,
                                     Loc.START_BUTTON_CLS).click()
            self._enter_values(Loc.NAS_IP_NAME, nas_ip)
            self.driver.find_element(By.XPATH,
                                     Loc.START_PAGE_NEXT_BUTTON).click()
            WebDriverWait(self.driver, 20).until(
                ec.presence_of_element_located((By.NAME, Loc.PASSWORD_NAME)))
        except NoSuchElementException:
            LOGGER.info('Start button not found, app is already launched, '
                        'Skipping entering NAS login details')

        # Validate invalid passwords
        for password in invalid_passwords:
            self._enter_values(Loc.NAS_IP_NAME, username)
            self._enter_values(Loc.PASSWORD_NAME, password)
            self.driver.find_element(By.CLASS_NAME,
                                     Loc.LOGIN_BUTTON_CLS).click()
            try:
                WebDriverWait(self.driver, 240).until(
                    ec.presence_of_element_located((By.CLASS_NAME,
                                                    Loc.ALERT_WINDOW_CLS)))
            except TimeoutException:
                raise ValueError("Invalid alert window is not located")
            # Validate invalid credential alert
            invalid_alert = self.driver.find_element(
                By.CSS_SELECTOR, Loc.INVALID_CREDENTIALS_ALERT_CSS).text

            if Loc.FAILED_TO_AUTHENTICATE_TEXT not in invalid_alert:
                raise ValueError('Invalid credentials alert not found')
            self.driver.find_element(By.CSS_SELECTOR,
                                     Loc.NO_BUTTON_CSS).click()

        LOGGER.info('Validated invalid passwords successfully\n')
        return True

    def _validate_backup_job_name_in_overview_page(self, username):
        """
        Lib to validate backup job name in overview page

        Arguments
        | username: Username of NAS
        """
        LOGGER.info('|___Validate job name___|')

        self.driver.find_element(By.CSS_SELECTOR, Loc.OVERVIEW_TAB_CSS).click()
        job_name = self.driver.find_element(By.CSS_SELECTOR,
                                            Loc.OVERVIEW_JOB_NAME_CSS).text
        pc_name = self.driver.find_element(By.XPATH,
                                           Loc.OVERVIEW_PC_NAME_XPATH).text
        expected_job_name = f'{pc_name}_{username}'
        if expected_job_name not in job_name:
            raise ValueError('Job name is not in expected sequence')

        LOGGER.info('Backup job name validated successfully\n')
        return True

    def _validate_job_history_tab(self):
        """
        Lib to validate logs in job history tab
        """
        LOGGER.info('|___Validate job history tab___|')

        self.driver.find_element(By.CSS_SELECTOR,
                                 Loc.JOB_HISTORY_TAB_CSS).click()
        try:
            self.driver.find_element(By.CSS_SELECTOR, Loc.JOB_HISTORY_DATA_CSS)
        except NoSuchElementException:
            self.driver.find_element(By.CSS_SELECTOR,
                                     Loc.JOB_HISTORY_NO_ROWS_CSS)

        LOGGER.info('Validated job history tab\n')
        return True

    def _validate_logs_tab(self):
        """
        Lib to validate logs tab
        """
        LOGGER.info('|___Validate logs tab___|')

        self.driver.find_element(By.CSS_SELECTOR, Loc.LOGS_TAB_CSS).click()
        # Validate loading screen
        self.validate_nb_loading_page()
        logs_count = self.driver.find_elements(By.CSS_SELECTOR,
                                               Loc.LOGS_DATA_CSS)
        if logs_count == 0:
            raise ValueError("No logs found in logs tab")

        LOGGER.info('Validated logs count in logs tab\n')
        return True

    def _validate_help_tab(self):
        """
        Lib to validate help tab rows
        """
        LOGGER.info('|___Validate help tab rows___|')

        self.driver.find_element(By.CSS_SELECTOR, Loc.HELP_TAB_CSS).click()
        help_row_count = self.driver.find_elements(By.CSS_SELECTOR,
                                                   Loc.HELP_ROWS_CSS)
        if help_row_count == 0:
            raise ValueError('No rows found in help tab')

        LOGGER.info('Validated help tab rows successfully\n')
        return True

    @keyword('NetBak: Validate home tabs after backup job')
    def validate_home_tabs(self, username):
        """
        Lib to validate home tabs after creating backup job

        Arguments
        | username: Username of NAS
        """
        LOGGER.info('|___Validate home tabs after creating backup job___|')

        # Check loading page
        self.validate_nb_loading_page()

        # Validate job name in overview page
        self._validate_backup_job_name_in_overview_page(username)

        # Validate job history tab
        self._validate_job_history_tab()

        # Validate logs tab
        self._validate_logs_tab()

        # Validate help tab
        self._validate_help_tab()

        LOGGER.info('Validated home tabs after backup job successfully\n')
        return True

    def _validate_nas_details_in_overview_page(self, nas_ip, repository_name):
        """
        Lib to validate NAS details in overview page

        Arguments
        | nas_ip: IP of NAS
        | repository_name: Repository name used to create repository
        """
        LOGGER.info('|___Validate NAS details in overview pge___|')

        # Validate NAS IP
        ip_value = self.driver.find_element(By.CSS_SELECTOR,
                                            Loc.OVERVIEW_NAS_IP_CSS).text
        if ip_value != nas_ip:
            raise ValueError("NAS IP does not match")

        # Validate inventory
        inventory_value = self.driver.find_element(
            By.CSS_SELECTOR, Loc.OVERVIEW_INV_NAME_CSS).text
        pc_name = self.driver.find_element(By.XPATH,
                                           Loc.OVERVIEW_PC_NAME_XPATH).text
        if pc_name not in inventory_value:
            raise ValueError("Inventory value does not match sequence")

        # Validate repository
        repository_value = self.driver.find_element(
            By.CSS_SELECTOR, Loc.OVERVIEW_REPO_NAME_CSS).text
        if repository_name != repository_value:
            raise ValueError("Repository value does not match to the name")

        # Validate HDP version
        version_value = self.driver.find_element(
            By.CSS_SELECTOR, Loc.OVERVIEW_HDP_VERSION_CSS).text

        if "2.0.0" not in version_value:
            raise ValueError("HDP Version value is not 2.0.0")

        LOGGER.info('Validated NAS details in overview page successfully\n')
        return True

    def _validate_network_in_overview_page(self):
        """
        Lib to validate network field in overview page
        Shall be validated across 2 options ['Ethernet', 'WiFi']
        """
        LOGGER.info('|___Validate Network Field___|')

        expected_network = Loc.EXP_NETWORK
        # Network field takes some time to populate data
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((
            By.CSS_SELECTOR, Loc.OVERVIEW_NETWORK_CSS)))
        network = self.driver.find_element(By.CSS_SELECTOR,
                                           Loc.OVERVIEW_NETWORK_CSS).text

        if network not in expected_network:
            raise ValueError('Retrieved network text is not expected:'
                             f'Expected network: {expected_network}'
                             f'Retrieved network: {network}')

        LOGGER.info('Validated network field in overview page successfully\n')
        return True

    @keyword('NetBak: Validate overview page')
    def validate_overview_page(self, username, nas_ip, repository_name):
        """
        Lib to validate overview page rows

        Arguments
        | username: Username of NAS
        | nas_ip: IP of NAS
        | repository_name: Repository name used to create repository
        """
        LOGGER.info('|___Validate overview page___|')

        # Validate loading page
        self.validate_nb_loading_page()

        # Validate backup job name
        self._validate_backup_job_name_in_overview_page(username)

        # Validate NAS details
        self._validate_nas_details_in_overview_page(nas_ip, repository_name)

        # Validate network field
        self._validate_network_in_overview_page()

        LOGGER.info("Validated overview page details\n")
        return True

    @keyword('NetBak: Get backup job details')
    def get_backup_job_details(self):
        """
        Lib to get backup job, repository and inventory details
        These details required to validate in HDP app and delete data
        """
        LOGGER.info('|___Get backup job details___|')

        # Validate loading screen
        self.validate_nb_loading_page()
        self.driver.find_element(By.CSS_SELECTOR, Loc.OVERVIEW_TAB_CSS).click()
        job_name = self.driver.find_element(By.CSS_SELECTOR,
                                            Loc.OVERVIEW_JOB_NAME_CSS).text
        job_name = job_name.split()[-1]
        inventory_name = self.driver.find_element(
            By.CSS_SELECTOR, Loc.OVERVIEW_INV_NAME_CSS).text
        repository_name = self.driver.find_element(
            By.CSS_SELECTOR, Loc.OVERVIEW_REPO_NAME_CSS).text

        LOGGER.info('Retrieved backup job details:\n'
                    f'Job name: {job_name}\n'
                    f'Repository name: {repository_name}\n'
                    f'Inventory name: {inventory_name}\n')
        return job_name, repository_name, inventory_name

    @keyword('NetBak: Get network IP from overview page')
    def get_network_ip(self):
        """
        Lib to get network IP from overview page
        """
        LOGGER.info('|___Get network IP from overview page___|')

        # Validate loading screen
        self.validate_nb_loading_page()
        self.driver.find_element(By.CSS_SELECTOR, Loc.OVERVIEW_TAB_CSS).click()
        network_ip = self.driver.find_element(By.CLASS_NAME,
                                              Loc.OVERVIEW_INV_IP_CLS).text

        LOGGER.info('Retrieved network IP from overview page\n')
        return network_ip

    @keyword('NetBak: Validate network IP with host IP')
    def validate_network_ip_with_host_ip(self, network_ip):
        """
        Lib to validate network IP with host IP

        Arguments
        | network_ip: IP from overview page of NetBak
        """
        LOGGER.info('|___Validate network IP with host IP___|')

        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)

        if host_ip != network_ip:
            raise ValueError("Host IP and network IP mismatch:"
                             f"Host IP: {host_ip}"
                             f"Network IP: {network_ip}")

        LOGGER.info('Host IP and network IP matched successfully\n')
        return True

    @keyword('NetBak: Validate job history page fields')
    def validate_job_history_page_fields(self):
        """
        Lib to validate fields of job history page
        """
        LOGGER.info("|___Validate job history page fields___|")

        expected_fields = Loc.EXP_JOB_FIELDS_LIST
        # Validate loading screen
        self.validate_nb_loading_page()
        self.driver.find_element(By.CSS_SELECTOR, 
                                 Loc.JOB_HISTORY_TAB_CSS).click()
        field_elements = self.driver.find_elements(
            By.CLASS_NAME, Loc.JOB_HISTORY_HEADERS_CONTENT_CLS)
        LOGGER.info(f"Job history elements: {field_elements}")
        for element in field_elements:
            field_text = element.find_element(
                By.XPATH, Loc.JOB_HISTORY_HEADERS_TAG_CSS).text
            LOGGER.info(f"f'Field text: {field_text}")
            if field_text not in expected_fields:
                raise ValueError("Field text retrieved is not expected field")

        LOGGER.info("Validated job history page fields successfully\n")
        return True

    @keyword('NetBak: Validate logs page fields')
    def validate_logs_page_fields(self):
        """
        Lib to validate logs page fields
        """
        LOGGER.info('|___Validate logs page fields___|')

        expected_fields = Loc.LOGS_EXPECTED_FIELDS_LIST
        # Validate loading screen
        self.validate_nb_loading_page()
        self.driver.find_element(By.CSS_SELECTOR, Loc.LOGS_TAB_CSS).click()
        field_elements = self.driver.find_elements(By.XPATH,
                                                   Loc.LOGS_HEADERS_XPATH)
        for elem_iter in range(len(field_elements)):
            field_text = field_elements[elem_iter].find_element(
                By.XPATH, Loc.JOB_HISTORY_HEADERS_TAG_CSS).text
            if field_text not in expected_fields:
                raise ValueError("Field text retrieved is not expected field")

        LOGGER.info("Validated logs page fields successfully\n")
        return True

    @keyword('NetBak: Validate user name of logs')
    def validate_user_name_of_logs(self, nas_user):
        """
        Lib to validate username of retrieved logs in logs page

        Arguments
        | nas_user: User credential of NAS used for login
        """
        LOGGER.info('|___Validate user name of logs___|')

        # Validate if jobs tab is expanded already
        # If not, click and logs tab and wait till it is expanded
        try:
            WebDriverWait(self.driver, 20).until(
                ec.presence_of_element_located((
                    By.CLASS_NAME, Loc.LOGS_DATA_CLS)))
        except TimeoutException:
            LOGGER.info('Expanding logs tab...')
            self.driver.find_element(By.CSS_SELECTOR, Loc.LOGS_TAB_CSS).click()
            # Wait till logs page loads
            WebDriverWait(self.driver, 20).until(
                ec.presence_of_element_located((
                    By.CLASS_NAME, Loc.LOGS_DATA_CLS)))

        # Check if logs are populated
        name_elements = self.driver.find_elements(By.CLASS_NAME,
                                                  Loc.LOGS_DATA_CLS)
        if len(name_elements) < 2:
            LOGGER.info('No enough logs to validate user name')
            return True

        # Get usernames
        user1 = name_elements[1].find_element(By.XPATH,
                                              Loc.LOGS_USERNAME_CSS).text
        user2 = name_elements[2].find_element(By.XPATH,
                                              Loc.LOGS_USERNAME_CSS).text

        # Validate usernames
        if user1 != nas_user or user2 != nas_user:
            raise ValueError("User of logs does not match with NAS user:"
                             f"NAS User: {nas_user}"
                             f"Logs user: {user1}, {user2}")

        LOGGER.info('Validated logs user with NAS user successfully\n')
        return True

    def _select_ethernet_config(self):
        """
        Lib to select ethernet config for manual network type
        """
        LOGGER.info('|___Select Ethernet config___|')

        element = self.driver.find_element(
            By.CSS_SELECTOR, Loc.NETWORK_CONFIG_ETHERNET_CONFIG_CSS)
        if not element.is_enabled():
            LOGGER.info('Element to select ethernet is not enabled, '
                        'skipping selecting the element')
            return True
        element.click()

        LOGGER.info('Selected ethernet config\n')
        return True

    def _select_wifi_config(self):
        """
        Lib to select wi-fi config for manual network type
        """
        LOGGER.info('|___Select WiFi config___|')

        element = self.driver.find_element(
            By.CSS_SELECTOR, Loc.NETWORK_CONFIG_WIFI_CONFIG_CSS)
        if not element.is_enabled():
            LOGGER.info('Element to select wifi is not enabled, '
                        'skipping selecting the element')
            return True
        element.click()

        LOGGER.info('Selected wifi config\n')
        return True

    @keyword('NetBak: Select network configuration')
    def select_network_configuration(self, network_type, manual_config):
        """
        Lib to select network configuration for backup job

        Arguments
        | network_type: type of network to be selected  'Automatic' or 'Manual'
        | manual_config: Type of manual network config to be selected
        |                eg. Ethernet, WiFi
        """
        LOGGER.info('|___Select network configuration___|')

        # Validated expected network type
        network_type = network_type.lower()
        expected_network_type = Loc.EXP_NETWORK_TYPE
        if network_type not in expected_network_type:
            raise ValueError('Network type provided is not expected type, '
                             f'please select from {expected_network_type}')

        # Validate manual config for manual network
        if network_type == 'manual' and manual_config is None:
            raise ValueError('Manual config option is required to be selected '
                             'from ethernet or wifi for manual network')
        if network_type == 'manual':
            manual_config = manual_config.lower()

        # Select network type
        LOGGER.debug(f"Selecting {network_type} network config")
        if network_type == 'automatic':
            self.driver.find_element(
                By.CSS_SELECTOR, Loc.NETWORK_CONFIG_AUTOMATIC_BUTTON_CSS).\
                click()
        else:
            self.driver.find_element(
                By.CSS_SELECTOR, Loc.NETWORK_CONFIG_MANUAL_BUTTON_CSS).click()
            LOGGER.debug(f"Selecting {manual_config} manual config")
            if manual_config == 'ethernet':
                self._select_ethernet_config()
            else:
                self._select_wifi_config()

        LOGGER.info('Selected network configuration\n')
        return True

    @keyword('NetBak: Edit backup job')
    def edit_backup_job(self, drive_letter=None, network_type='automatic',
                        manual_config=None):
        """
        Lib to edit backup job. To edit individual options for different pages,
        sub-libs could be created and called here.

        Arguments
        | drive_letter: Drive Letter To Backup Ex: D,E etc..
        | network_type: type of network to be selected  'Automatic' or 'Manual'
        | manual_config: Type of manual network config to be selected
        |                eg. Ethernet, WiFi
        """
        LOGGER.info('|___Edit backup job___|')

        # Validate loading screen
        self.validate_nb_loading_page()
        # Click edit button and switch to edit job window
        try:
            WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((
                    By.CSS_SELECTOR, Loc.EDIT_BACKUP_BUTTON_CSS)))
        except TimeoutException:
            self.driver.find_element(
                By.CSS_SELECTOR, Loc.OVERVIEW_TAB_CSS).click()
        self.driver.find_element(By.CSS_SELECTOR,
                                 Loc.EDIT_BACKUP_BUTTON_CSS).click()
        self.driver.switch_to.window(self.driver.window_handles[1])

        # Device&Target page
        if drive_letter is not None:
            self.select_volume(drive_letter)
        self.driver.find_element(By.CLASS_NAME, Loc.BACKUP_NEXT_BUTTON).click()
        # Schedule page
        self.driver.find_element(By.CLASS_NAME, Loc.BACKUP_NEXT_BUTTON).click()
        # Version page
        self.driver.find_element(By.CLASS_NAME, Loc.BACKUP_NEXT_BUTTON).click()
        # Rule page
        self.select_network_configuration(network_type, manual_config)
        try:
            WebDriverWait(self.driver, 60).until(ec.element_to_be_clickable((
                By.CLASS_NAME, Loc.BACKUP_NEXT_BUTTON)))
        except TimeoutException:
            raise ValueError("Next button not clickable after network select")
        self.driver.find_element(By.CLASS_NAME, Loc.BACKUP_NEXT_BUTTON).click()
        # Summary page
        self.driver.find_element(By.CLASS_NAME, Loc.BACKUP_NEXT_BUTTON).click()

        # Validate edit job is clickable
        self.driver.switch_to.window(self.driver.window_handles[0])

        # Inventory automatically disconnects because of lib update at back end
        inventory_connected = self.validate_inventory_connected()
        if not inventory_connected:
            self.wait_till_inventory_connected(timeout=400)

        try:
            WebDriverWait(self.driver, 20).until(ec.element_to_be_clickable((
                By.CSS_SELECTOR, Loc.EDIT_BACKUP_BUTTON_CSS)))
        except TimeoutException:
            raise ValueError("Edit backup button is not visible")

        LOGGER.info('Edit backup job is successful\n')
        return True

    @keyword('NetBak: Validate inventory connected')
    def validate_inventory_connected(self):
        """
        Lib to validate if inventory is connected
        """
        LOGGER.info('|___Validate Inventory connected___|')

        try:
            # Check if warning icon is present
            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((
                    By.CSS_SELECTOR, Loc.INV_CONNECT_VALIDATION_CSS)))
            LOGGER.info('Inventory got disconnected')
            return False
        except TimeoutException:
            LOGGER.info('Inventory is connected')

        LOGGER.info('Validated inventory connected\n')
        return True

    @keyword('NetBak: Wait till inventory connected')
    def wait_till_inventory_connected(self, timeout=None):
        """
        Lib to allow inventory to connect back.
        In some scenarios, inventory automatically disconnects because of
        lib validation in the back end
        And, inventory automatically connects back after validation

        Arguments
        | timeout: Timeout to allow operation to happen
        """
        LOGGER.info('|___Wait till inventory is connected___|')

        timeout = timeout or self.check_timeout
        start_time = time.time()

        while True:
            if time.time() - start_time > int(timeout):
                raise ValueError("Inventory has not connected back "
                                 "after disconnecting")
            try:
                # Check if warning icon is present
                WebDriverWait(self.driver, 5).until(
                    ec.presence_of_element_located((
                        By.CSS_SELECTOR, Loc.INV_WARNING_ICON_CSS)))
            except TimeoutException:
                break

            LOGGER.info("Inventory has not connected back, retrying..")

        LOGGER.info("Inventory has connected back after waiting\n")
        return True

    @keyword('NetBak: Select NAS IP from LAN and press back')
    def select_nas_ip_from_lan_press_back(self, nas_ip):
        """
        Lib to select NAS IP after selecting LAN option to log in to NAS

        Arguments
        | nas_ip: IP of NAS
        """
        LOGGER.info('|___Select NAS IP from LAN and press back___|')

        self.driver.find_element(By.CLASS_NAME, Loc.START_BUTTON_CLS).click()
        # Click LAN button
        self.driver.find_element(By.CSS_SELECTOR,  Loc.LAN_BUTTON_CSS).click()
        try:
            WebDriverWait(self.driver, 50).until(ec.element_to_be_clickable((
                By.CSS_SELECTOR, Loc.LAN_NAS_DATA_CSS)))
        except TimeoutException:
            raise ValueError("NAS data is not loaded in LAN")

        # Scroll to NAS IP and select IP
        element = self.driver.find_element(
            By.XPATH, Loc.LAN_SELECT_NAS_IP_XPATH.format(nas_ip))
        self.mouse_pointer.move_to_element(element).click().perform()
        self.driver.find_element(By.CSS_SELECTOR,
                                 Loc.LAN_SELECT_BUTTON_CSS).click()

        # Press Back button
        self.press_back_button_in_credentials_page()

        LOGGER.info('Selected NAS IP from LAN and pressed back successfully\n')
        return True

    @keyword('NetBak: Validate start string')
    def validate_start_string(self):
        """
        Lib to validate start page NetBak string
        """
        LOGGER.info('|___Validate start page string___|')

        start_string = self.driver.find_element(By.CLASS_NAME,
                                                Loc.APP_START_DESC_CLS).text
        if start_string != Loc.NB_START_PAGE_TEXT:
            raise ValueError("Retrieved start string is not expected string")

        LOGGER.info('Validated start page string successfully\n')
        return True

    @keyword('NetBak: Validate password eye button')
    def validate_password_eye_button(self, nas_ip, username, password):
        """
        Lib to validate password eye button and read the password entered

        Arguments
        | nas_ip: NAS IP to be entered to connect to app
        | username: Username of the NAS
        | password: Password of the NAS
        """
        LOGGER.info('|___Validate password eye button___|')

        self.driver.find_element(By.CLASS_NAME, Loc.START_BUTTON_CLS).click()
        self._enter_values(Loc.NAS_IP_NAME, nas_ip)
        self.driver.find_element(By.XPATH, Loc.START_PAGE_NEXT_BUTTON).click()
        WebDriverWait(self.driver, 60).until(ec.presence_of_element_located((
            By.NAME, Loc.PASSWORD_NAME)))

        # Enter NAS credentials and submit
        self._enter_values(Loc.NAS_IP_NAME, username)
        self._enter_values(Loc.PASSWORD_NAME, password)

        # Click eye button
        self.driver.find_element(By.CSS_SELECTOR, Loc.PASSWORD_EYE_BUTTON_CSS)
        element = self.driver.find_element(
            By.CSS_SELECTOR, Loc.READ_PASSWORD_VALUE_CSS.format(password))
        if not element:
            raise ValueError('Not able to retrieve password after enabling '
                             'eye button')

        LOGGER.info('Validated password eye button\n')
        return True

    @keyword('NetBak: Refresh app')
    def refresh_app(self):
        """
        Lib to click refresh button and validate loading is completed
        """
        LOGGER.info('|___Refresh app___|')

        self.driver.find_element(By.CSS_SELECTOR,  "div.refresh svg").click()
        WebDriverWait(self.driver, 30).until(
            ec.invisibility_of_element_located((
                By.CLASS_NAME, 'qcss-message-item-detial')))

        LOGGER.info('App is refreshed\n')
        return True

    @keyword('NetBak: Validate config broken dialog content')
    def validate_config_broken_dialog_content(self):
        """
        Lib to validate dialog content observed after deleting inventory/
        Repository from HDP but not backup job
        """
        LOGGER.info('|___Validate config broken content___|')

        expected_content = Loc.BROKEN_DIALOG_CONTENT
        # Wait till dialog content is popped up
        dialog_content = self.driver.find_element(
            By.CLASS_NAME, Loc.BROKEN_DIALOG_CONTENT_CLS).text

        if dialog_content != expected_content:
            raise ValueError("Broken dialog content received is not the "
                             "expected content")

        LOGGER.info('Validated broken dialog content successfully\n')
        return True

    @keyword('NetBak: Logout app')
    def logout_app(self):
        """
        Lib to logout from the app.
        App could only be logged out if backup job is created
        """
        LOGGER.info("|___Logout app___|")

        # Validate if job is created
        self.validate_nb_loading_page()
        try:
            self.driver.find_element(By.CSS_SELECTOR, Loc.OVERVIEW_TAB_CSS)
        except TimeoutException:
            raise ValueError("Job is not created, logout is supported only "
                             "after job is created")

        # Logout from app
        self.driver.find_element(By.CSS_SELECTOR, Loc.MORE_BUTTON_CSS).click()
        self.driver.find_element(By.XPATH, Loc.LOGOUT_APP_XPATH).click()

        # Validate app is logged out
        try:
            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located((By.NAME, Loc.PASSWORD_NAME)))
        except TimeoutException:
            raise ValueError("App is not logged out")

        LOGGER.info("Logged out of app successfully\n")
        return True

    @keyword('NetBak: Press back button in credentials page')
    def press_back_button_in_credentials_page(self):
        """
        Lib to press back button in NAS credentials page
        """
        LOGGER.info('|___Press back button in NAS credentials page___|')

        # Press Back button
        WebDriverWait(self.driver, 20).until(ec.presence_of_element_located((
            By.CLASS_NAME, Loc.BACK_BUTTON_CLS)))
        self.driver.find_element(By.CLASS_NAME, Loc.BACK_BUTTON_CLS).click()

        # Validate back button press is successful
        try:
            WebDriverWait(self.driver, 20).until(
                ec.presence_of_element_located((
                    By.CSS_SELECTOR, Loc.LAN_BUTTON_CSS)))
        except TimeoutException:
            raise ValueError("Back button is not pressed")

        LOGGER.info("Pressed back button successfully\n")
        return True

    @keyword("NetBak: Validate quick start")
    def validate_quick_start(self):
        """
        Lib validating quick start in help page
        """
        LOGGER.info("|___Validating quick start in help page___|")

        # Validate loading screen
        self.validate_nb_loading_page()
        expected_texts = Loc.QUICK_START_STRINGS
        self.driver.find_element(By.CSS_SELECTOR, Loc.HELP_TAB_CSS).click()
        self.driver.find_element(By.XPATH, Loc.QUICK_START_XPATH).click()
        # Switching to Second window
        self.driver.switch_to.window(self.driver.window_handles[1])
        # Wait for the element in the new window
        WebDriverWait(self.driver, 10).until(ec.presence_of_element_located(
            (By.CLASS_NAME, Loc.QUICK_START_TEXT_CLS)))

        for expected_text in expected_texts:
            retrieved_text = self.driver.find_element(
                By.CLASS_NAME,  Loc.QUICK_START_TEXT_CLS).text
            if expected_text != retrieved_text:
                raise ValueError(f"Quick start texts mismatch, "
                                 f"expected text: {expected_text}, "
                                 f"retrieved text:{retrieved_text}")
            try:
                self.driver.find_element(By.XPATH,
                                         Loc.NEXT_BUTTON_XPATH).click()
            except NoSuchElementException:
                self.driver.find_element(By.XPATH,
                                         Loc.CLOSE_BUTTON_XPATH).click()
        # Switching back to main window
        self.driver.switch_to.window(self.driver.window_handles[0])

        LOGGER.info("Validated quick start in help page\n")
        return True

    @keyword("NetBak: Download debug report")
    def download_debug_report(self):
        """
        Lib to download debug report in help page
        """
        LOGGER.info("|___Download debug report___|")

        # Validate loading screen
        self.validate_nb_loading_page()
        self.driver.find_element(By.CSS_SELECTOR, Loc.HELP_TAB_CSS).click()
        self.driver.find_element(By.XPATH,
                                 Loc.Debug_report_XPATH).click()
        self.driver.find_element(By.XPATH,
                                 Loc.DOWNLOAD_BUTTON_XPATH).click()
        # Validate loading screen
        self.validate_nb_loading_page()

        # Simulate pressing the "Enter" key
        time.sleep(3)
        # Click download button on explorer window
        active_element = self.driver.switch_to.active_element
        active_element.send_keys(Keys.ENTER)

        LOGGER.info("Debug report downloaded\n")
        return True

    @keyword("NetBak: Validate tutorial tab in help page")
    def validate_tutorial_tab_in_help_page(self):
        """
        Lib to validate NetBak PC Agent tutorial tab in help page
        """
        LOGGER.info("|___Validate tutorial tab in help page___|")

        # Validate loading screen
        self.validate_nb_loading_page()
        self.driver.find_element(By.CSS_SELECTOR, Loc.HELP_TAB_CSS).click()
        self.driver.find_element(By.XPATH, Loc.NB_TUTORIAL_XPATH).click()
        # Skipping validation as browser will load webpage,
        # So validating in robot file test case

        LOGGER.info("Validated NB tutorial tab in help page\n")
        return True

    @keyword("NetBak: Validate about tab in help page")
    def validate_about_tab_in_help_page(self, exp_version):
        """
        Lib to validate About NetBak PC Agent

        Arguments
        | exp_version: NetBak version to validate with current version
        """
        LOGGER.info("|___Validating About tab of NetBak PC Agent___|")

        # Validate loading screen
        self.validate_nb_loading_page()

        self.driver.find_element(By.CSS_SELECTOR, Loc.HELP_TAB_CSS).click()
        self.driver.find_element(By.XPATH, Loc.ABOUT_NB_TAB_XPATH).click()

        self.driver.switch_to.window(self.driver.window_handles[1])
        received_text = self.driver.find_element(By.XPATH,
                                                 Loc.NB_VERSION_XPATH).text
        if exp_version not in received_text:
            raise ValueError(
                "Unexpected version, Please check version details")

        self.driver.find_element(By.CLASS_NAME, Loc.ABOUT_URL_CLS).click()
        # Skipping validation as browser will load webpage,
        # So validating in robot file test case
        self.driver.switch_to.window(self.driver.window_handles[0])

        LOGGER.info("Validated About tab of NetBak PC Agent\n")
        return True

    @keyword('NetBak: Validate next button after deselecting volumes')
    def validate_next_button_after_deselecting_volumes(
            self, shared_folder, repo_name):
        """
        Lib to validate next button greyed out after selecting repository but
        deselecting all volumes

        Arguments
        | shared_folder: Shared folder name to create repository
        | repo_name: Repository name to be created
        """
        LOGGER.info("|___Validate next button after deselecting volumes___|")

        # Validate configs are cleared and job is not present
        try:
            if self.driver.find_element(By.CSS_SELECTOR, Loc.OVERVIEW_TAB_CSS):
                raise ValueError(
                    "Configs are not cleared and job already present")
        except NoSuchElementException:
            pass

        # Select Repository
        self.create_repository(shared_folder, repo_name)
        # Deselect all volumes
        self.driver.find_element(By.XPATH, Loc.ALL_VOLUMES_XPATH).click()

        # Validate clicking next button
        try:
            WebDriverWait(self.driver, 30).until_not(
                ec.element_to_be_clickable((By.XPATH, Loc.NEXT_BUTTON_XPATH)))
        except TimeoutException:
            raise ValueError("Clicked Next Button without selecting volumes")

        # Validate Next button is greyed out
        try:
            if self.driver.find_element(
                    By.CSS_SELECTOR, Loc.SCHEDULE_DAILY_BACKUP_OPTION_CSS):
                raise ValueError("Next button not greyed out after "
                                 "deselecting all volumes")
        except NoSuchElementException:
            pass

        LOGGER.info("Validated next button after deselecting volumes\n")
        return True

    @keyword('NetBak: Validate refresh button in LAN')
    def validate_refresh_button_in_lan(self):
        """
        Lib to validate refresh button in LAN
        """
        LOGGER.info("|___Validate refresh button in LAN___|")

        # Check app is already launched
        try:
            self.driver.find_element(By.CLASS_NAME,
                                     Loc.START_BUTTON_CLS).click()
        except NoSuchElementException:
            LOGGER.info("App is already launched, skipping click start button")

        # Click LAN button
        self.driver.find_element(By.CSS_SELECTOR, Loc.LAN_BUTTON_CSS).click()

        # Validate NAS IPs are populated in LAN
        try:
            WebDriverWait(self.driver, 50).until(ec.element_to_be_clickable((
                By.CSS_SELECTOR, Loc.LAN_NAS_DATA_CSS)))
        except TimeoutException:
            raise ValueError("NAP IPs are not present in LAN option, connect "
                             "LAN to login through LAN option")

        # Click Refresh Button
        self.driver.find_element(By.XPATH, Loc.REFRESH_BUTTON_XPATH).click()
        self.validate_nb_loading_page()

        # Validate NAS data populated in LAN after refresh
        try:
            WebDriverWait(self.driver, 50).until(ec.element_to_be_clickable((
                By.CSS_SELECTOR, Loc.LAN_NAS_DATA_CSS)))
        except TimeoutException:
            raise ValueError("NAP data is not populated after refresh")

        LOGGER.info("Validated refresh button in LAN\n")
        return True

    @keyword('NetBak: Validate NB loading page')
    def validate_nb_loading_page(self, timeout=None):
        """
        Lib to validate loading page in NetBak application

        Arguments
        | timeout: Time in sec to wait till the page loads
        """
        LOGGER.info("|___Validate NB loading page___|")

        timeout = timeout or self.check_timeout
        start_time = time.time()

        while True:
            if time.time() - start_time > int(timeout):
                raise ValueError("NetBak page is still loading after waiting")

            try:
                self.driver.find_element(By.CLASS_NAME, Loc.LOADING_PAGE_CLS)
            except NoSuchElementException:
                break

            LOGGER.debug("NB page is still loading, pending retry...")
            time.sleep(2)

        LOGGER.info("NB page loaded successfully\n")
        return True

    @keyword('NetBak: Get NB job volumes')
    def get_nb_job_volumes(self):
        """
        Lib to get the volumes used in backup job
        """
        LOGGER.info("|___Get NB job Volumes___|")

        # Validate loading screen
        self.validate_nb_loading_page()

        # Wait overview tab expanded already
        try:
            WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((
                    By.CSS_SELECTOR, Loc.OVERVIEW_VOLUMES_COUNT_CSS)))
        except TimeoutException:
            self.driver.find_element(By.CSS_SELECTOR,
                                     Loc.OVERVIEW_TAB_CSS).click()
        # Get Volumes count used in backup job
        volumes_count = self.driver.find_elements(
            By.CSS_SELECTOR, Loc.OVERVIEW_VOLUMES_COUNT_CSS)
        LOGGER.debug(f"Volumes count: {volumes_count}")
        volumes = []
        for volume in range(1, len(volumes_count)+1):
            volumes.append(self.driver.find_element(
                By.XPATH, Loc.OVERVIEW_VOLUMES_TEXT_XPATH.format(volume)).text)

        LOGGER.info(f"Retrieved volumes in NB backup job: {volumes}\n")
        return volumes

    @keyword('NetBak: Validate NB and HDP job volumes sync')
    def validate_nb_and_hdp_job_volumes_sync(self, hdp_volumes):
        """
        Lib to validate job volumes sync in HDP and NB

        Arguments
        | hdp_volumes: List of volumes reflecting in job in HDP
        """
        LOGGER.info("|___Validate NB and HDP job volumes sync___|")

        nb_volumes = self.get_nb_job_volumes()
        if nb_volumes != hdp_volumes:
            raise ValueError(f"NB and HDP job volumes are not synced:"
                             f"NB volumes: {nb_volumes}"
                             f"HDP volumes: {hdp_volumes}")

        LOGGER.info("Validated NB and HDP job volumes sync successfully\n")
        return True

    @keyword('NetBak: Validate job history plus minus button with no logs')
    def validate_history_plus_minus_buttons_with_no_logs(self):
        """
        Lib to validate job history page plus minus buttons
        when no logs are generated
        """
        LOGGER.info('|___Validate history buttons with no logs___|')

        # Expand job history page
        self.validate_nb_loading_page()
        self.driver.find_element(
            By.CSS_SELECTOR, Loc.JOB_HISTORY_TAB_CSS).click()
        self.validate_nb_loading_page()

        # Validate no rows present in job history page
        try:
            self.driver.find_element(
                By.CSS_SELECTOR, Loc.JOB_HISTORY_NO_ROWS_CSS)
        except NoSuchElementException:
            raise ValueError("Logs are generated in history page")

        # Validate zoom out not clickable
        self.validate_zoom_out_button_not_clickable()

        # Validate zoom in not clickable
        self.validate_zoom_in_button_not_clickable()

        LOGGER.info("Validated buttons in history page with no logs\n")
        return True

    @keyword('NetBak: Validate job history plus minus button with logs')
    def validate_history_plus_minus_buttons_with_logs(self):
        """
        Lib to validate job history page plus minus buttons
        when logs are generated
        """
        LOGGER.info('|___Validate history buttons with logs___|')

        # Expand job history page
        self.validate_nb_loading_page()
        self.driver.find_element(
            By.CSS_SELECTOR, Loc.JOB_HISTORY_TAB_CSS).click()
        self.validate_nb_loading_page()

        # Validate logs present in history page
        try:
            self.driver.find_element(By.CSS_SELECTOR, Loc.JOB_HISTORY_DATA_CSS)
        except NoSuchElementException:
            raise ValueError("No logs present in history page")

        # Validate zoom in not clickable
        self.validate_zoom_in_button_not_clickable()

        # Date before clicking zoom out
        date_before_zoom_out = self.driver.find_element(
            By.CSS_SELECTOR, Loc.JOB_HISTORY_TIMELINE_DATE_CSS).text
        LOGGER.debug(f"Date before zoom out: {date_before_zoom_out}")

        # Click Zoom out till clickable
        self.click_zoom_out_till_clickable()
        # Date after clicking zoom out
        date_after_zoom_out = self.driver.find_element(
            By.CSS_SELECTOR, Loc.JOB_HISTORY_TIMELINE_DATE_CSS).text
        LOGGER.debug(f"Date after zoom out: {date_after_zoom_out}")

        # Validate dates before and after zoom out clicks
        if date_before_zoom_out == date_after_zoom_out:
            raise ValueError("Dates before and after zoom out clicks are same")

        # Click zoom in till clickable
        self.click_zoom_in_till_clickable()

        # Validate dates before and after zoom in clicks
        date_after_zoom_in = self.driver.find_element(
            By.CSS_SELECTOR, Loc.JOB_HISTORY_TIMELINE_DATE_CSS).text
        LOGGER.debug(f"Date after zoom in: {date_after_zoom_in}")
        if date_after_zoom_in == date_after_zoom_out:
            raise ValueError("Dates before and after zoom in clicks are same")

        LOGGER.info("Validated history plus minus buttons with logs\n")
        return True

    @keyword('NetBak: Validate Zoom in button not clickable')
    def validate_zoom_in_button_not_clickable(self):
        """
        Lib to validate zoom in button not clickable
        """
        LOGGER.info("|___Validate Zoom in button not clickable")

        # Validate zoom in not clickable
        try:
            self.driver.find_element(By.CSS_SELECTOR, Loc.ZOOM_IN_CSS)
            raise ValueError("Zoom in button clickable in job history page")
        except NoSuchElementException:
            LOGGER.debug("Zoom in button not clickable in job history page")

        LOGGER.info("Validated Zoom in button not clickable in history page\n")
        return True

    @keyword('NetBak: Validate Zoom out button not clickable')
    def validate_zoom_out_button_not_clickable(self):
        """
        Lib to validate zoom out button not clickable
        """
        LOGGER.info("|___Validate zoom out button not clickable___|")

        # Validate zoom out not clickable
        try:
            self.driver.find_element(By.CSS_SELECTOR, Loc.ZOOM_OUT_CSS)
            raise ValueError("Zoom out button clickable in job history page")
        except NoSuchElementException:
            LOGGER.debug("Zoom out button not clickable in job history page")

        LOGGER.info("Validated Zoom out button not clickable in page\n")
        return True

    @keyword('NetBak: Click zoom out button till clickable')
    def click_zoom_out_till_clickable(self):
        """
        Lib to click zoom out button till clickable
        """
        LOGGER.info("|___Click Zoom out till clickable___|")

        while True:
            try:
                self.driver.find_element(
                    By.CSS_SELECTOR, Loc.ZOOM_OUT_CSS).click()
            except NoSuchElementException:
                LOGGER.debug("Zoom out click reached max limit")
                break

        LOGGER.info("Clicked zoom out till max limit\n")
        return True

    @keyword('NetBak: Click zoom in button till clickable')
    def click_zoom_in_till_clickable(self):
        """
        Lib to click zoom in button till clickable
        """
        LOGGER.info("|___Click Zoom in till clickable___|")

        while True:
            try:
                self.driver.find_element(
                    By.CSS_SELECTOR, Loc.ZOOM_IN_CSS).click()
            except NoSuchElementException:
                LOGGER.debug("Zoom in click reached max limit")
                break

        LOGGER.info("Clicked zoom in till max limit\n")
        return True

    @keyword('NetBak: Validate filter result in job history')
    def validate_filter_result_in_job_history(self):
        """
        Lib to validate filtering the results in job history page
        """
        LOGGER.info("|___Validate filter result in job history___|")

        # Expand job history page
        self.validate_nb_loading_page()
        self.driver.find_element(
            By.CSS_SELECTOR, Loc.JOB_HISTORY_TAB_CSS).click()

        # Get the results from logs
        logs_results = self.get_results_from_logs()
        LOGGER.debug(f"Results in logs: {logs_results}")

        # De select all filter items
        self.deselect_all_filter_items()

        # Select each filter item and validate with data in job history page
        self.validate_logs_for_each_filter_item(logs_results)

        LOGGER.info("Validated filter result in job history page\n")
        return True

    @keyword('NetBak: Get results from logs in job history')
    def get_results_from_logs(self):
        """
        Lib to get results from logs in job history page
        """
        LOGGER.info("|___Get results from logs___|")

        logs_results = []
        self.validate_nb_loading_page()
        logs_count = self.driver.find_elements(
            By.CSS_SELECTOR, Loc.JOB_HISTORY_DATA_CSS)
        LOGGER.debug(f"Logs count in page: {logs_count}")
        for i in range(3, len(logs_count) + 3):
            result = self.driver.find_element(
                By.CSS_SELECTOR, Loc.JOB_HISTORY_RESULT_CSS.format(i)).text
            if "." in result:
                result = result.split(".")[0]
            if result not in logs_results:
                logs_results.append(result)

        if len(logs_results) == 0:
            raise ValueError("No results retrieved from logs")

        LOGGER.info("Got list of results from logs\n")
        return logs_results

    @keyword('NetBak: Deselect all filter items')
    def deselect_all_filter_items(self):
        """
        Lib to deselect all filter items for result in job history page
        """
        LOGGER.info("|___Deselect all filter items___|")

        self.driver.find_element(
            By.CSS_SELECTOR, Loc.JOB_HISTORY_RESULT_FILTER_CSS).click()
        result_items_count = self.driver.find_elements(
            By.CSS_SELECTOR, Loc.JOB_HISTORY_RESULT_FILTER_ITEMS_CSS)
        for i in range(1, len(result_items_count) + 1):
            self.driver.find_element(
                By.CSS_SELECTOR,
                Loc.JOB_HISTORY_FILTER_ITEMS_CLICK_CHECKBOX_CSS.
                format(i)).click()

        # Validate all items are deselected
        try:
            self.driver.find_element(
                By.CSS_SELECTOR, Loc.JOB_HISTORY_NO_ROWS_CSS)
        except NoSuchElementException:
            raise ValueError(f"All filter items are not deselected")

        LOGGER.info("Deselected all filter items successfully\n")
        return True

    @keyword('NetBak: Validate logs for each filter item')
    def validate_logs_for_each_filter_item(self, logs_results):
        """
        Lib to validate logs after selecting each filter
        items in job history page

        Arguments
        | logs_results: List of results from the logs in job history page
        """
        LOGGER.info("|___Validate logs after selecting filter items___|")

        result_items_count = self.driver.find_elements(
            By.CSS_SELECTOR, Loc.JOB_HISTORY_RESULT_FILTER_ITEMS_CSS)

        for i in range(1, len(result_items_count) + 1):
            # Select each filter item
            self.driver.find_element(
                By.CSS_SELECTOR,
                Loc.JOB_HISTORY_FILTER_ITEMS_CLICK_CHECKBOX_CSS.
                format(i)).click()
            item_name = self.driver.find_element(
                By.CSS_SELECTOR, Loc.JOB_HISTORY_FILTER_ITEMS_NAME_CSS.
                format(i)).text

            # Validate the filter items logs based on logs results
            if item_name in logs_results:
                try:
                    self.driver.find_element(
                        By.CSS_SELECTOR, Loc.JOB_HISTORY_DATA_CSS)
                    LOGGER.debug(f"Found data logs for {item_name}")
                except NoSuchElementException:
                    raise ValueError(f"No data found for {item_name} results")
            else:
                try:
                    self.driver.find_element(
                        By.CSS_SELECTOR, Loc.JOB_HISTORY_NO_ROWS_CSS)
                    LOGGER.debug(f"No data logs found for {item_name}")
                except NoSuchElementException:
                    raise ValueError(f"Data found for {item_name} results")

            # Deselect the filter item selected
            self.driver.find_element(
                By.CSS_SELECTOR,
                Loc.JOB_HISTORY_FILTER_ITEMS_CLICK_CHECKBOX_CSS.
                format(i)).click()

        LOGGER.info("Validated logs for each filter item\n")
        return True

    @keyword("NetBak: Download job status report")
    def download_job_status_report(self, expected_state=None):
        """
        Lib to download Job status report for expected job state

        Arguments
        | expected_state: Expected status of the backup job to be validated
        """
        LOGGER.info("|___Download the Job status report___|")

        self.driver.find_element(
            By.CSS_SELECTOR, Loc.JOB_HISTORY_TAB_CSS).click()
        self.validate_nb_loading_page()

        # Validate expected job status
        if expected_state:
            self.validate_expected_backup_job_status(
                expected_status=expected_state)

        # Validate data generated in job history page
        try:
            WebDriverWait(self.driver, 20).until(
                ec.presence_of_element_located((
                    By.CSS_SELECTOR, Loc.JOB_HISTORY_DATA_CSS)))
        except TimeoutException:
            raise ValueError("Job status data Not found in Job History")
        self.driver.find_element(By.CSS_SELECTOR,
                                 Loc.JOB_HISTORY_ACTION_BUTTON_CSS).click()

        # Download job status report
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.find_element(
            By.XPATH, Loc.JOB_HISTORY_DOWNLOAD_BUTTON_XPATH).click()
        active_element = self.driver.switch_to.active_element
        active_element.send_keys(Keys.ENTER)
        self.driver.find_element(
            By.XPATH, Loc.JOB_HISTORY_CLOSE_BUTTON_XPATH).click()

        LOGGER.info("Job status report downloaded successfully\n")
        return True

    @keyword('NetBak: Validate NAS IP page description strings')
    def validate_nas_ip_page_description_strings(self):
        """
        Lib to validate NAS IP page description strings
        """
        LOGGER.info("|___Validate NAS IP page description strings___|")

        self.driver.find_element(By.CLASS_NAME, Loc.START_BUTTON_CLS).click()
        try:
            WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((
                    By.CSS_SELECTOR, Loc.LAN_BUTTON_CSS)))
        except TimeoutException:
            raise ValueError(
                "NAP IP page is not loaded after clicking start button")

        # Validate plan string
        received_plan_string = self.driver.find_element(
            By.XPATH, Loc.START_PAGE_PLAN_STRING_XPATH).text
        if received_plan_string != Loc.START_PAGE_PLAN_STRING:
            raise ValueError(f"Received start page plan string mis-match,\n"
                             f"Received string: {received_plan_string}\n"
                             f"Expected string: "
                             f"{Loc.START_PAGE_PLAN_STRING}\n")

        # Validate NAS IP or LAN string
        received_nas_ip_lan_string = self.driver.find_element(
            By.CLASS_NAME, Loc.START_PAGE_NAS_IP_LAN_STRING_CLS).text
        if received_nas_ip_lan_string != Loc.START_PAGE_NAS_IP_LAN_STRING:
            raise ValueError(f"Received start page NAS IP LAN string "
                             f"mis-match\n Received string: "
                             f"{received_nas_ip_lan_string}\n"
                             f"Expected string: "
                             f"{Loc.START_PAGE_NAS_IP_LAN_STRING}\n")

        # Validate HDP version warning string
        received_hdp_version_warning = self.driver.find_element(
            By.XPATH, Loc.START_PAGE_HDP_VERSION_WARNING_XPATH).text
        if received_hdp_version_warning != Loc.START_PAGE_HDP_VERSION_WARNING:
            raise ValueError(f"HDP version warning string mis-match\n"
                             f"Received string: "
                             f"{received_hdp_version_warning}\n"
                             f"Expected string: "
                             f"{Loc.START_PAGE_HDP_VERSION_WARNING} ")

        LOGGER.info("Validated NetBak start page description string\n")
        return True

    @keyword('NetBak: Validate NAS IP page tooltip string')
    def validate_nas_ip_page_tooltip_string(self):
        """
        Lib to validate NAS IP page tooltip string
        """
        LOGGER.info("|___Validate NAS IP page tooltip string___|")

        self.driver.find_element(By.CLASS_NAME, Loc.START_BUTTON_CLS).click()
        try:
            WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((
                    By.CSS_SELECTOR, Loc.LAN_BUTTON_CSS)))
        except TimeoutException:
            raise ValueError(
                "NAS IP page is not loaded after clicking start button")

        # Get tooltip string
        tooltip_element = self.driver.find_element(
            By.XPATH, Loc.START_PAGE_TOOLTIP_XPATH)
        self.mouse_pointer.move_to_element(tooltip_element).click().perform()
        tooltip_text = WebDriverWait(self.driver, 10).until(
             ec.presence_of_element_located(
                 (By.CSS_SELECTOR, Loc.HOVER_INFO_CSS))).text

        # Validate tooltip string
        if tooltip_text != Loc.START_PAGE_TOOLTIP_INFO:
            raise ValueError(f"Tooltip info mis-match\n Received info"
                             f" {tooltip_text}\n Expected info "
                             f"{Loc.START_PAGE_TOOLTIP_INFO}\n ")

        LOGGER.info("Validated NAS IP page tooltip string\n")
        return True

    @keyword('NetBak: Validate NB login with multiple NAS')
    def validate_nb_login_with_multiple_nas(
            self, nas_ip, username, password, nas_ip2, username2, password2,
            chromedriver_path, app_path):
        """
        Lib is to validate behaviour of NB for login with multiple NAS

        Arguments
        | nas_ip: First NAS IP to be entered to connect to app
        | username: Username of the  first NAS
        | password: Password of the first NAS
        | nas_ip2: Second NAS IP to be entered to connect to app
        | username2: Username of the second NAS
        | password2: Password of the second NAS
        | chromedriver_path: Executable path of chromedriver
        | app_path: Executable path of NetBak app
        """
        LOGGER.info("|___Validate NB login with multiple NAS___|")

        # NB login with first NAS
        self.login_app(nas_ip, username, password)
        self.driver.close()

        # NB login with second NAS
        self.launch_app(chromedriver_path, app_path)
        response = self.login_app(nas_ip2, username2, password2)
        if response is not True:
            raise ValueError("Login to second NAS become fail")

        LOGGER.info("NetBak login with multiple NAS successful\n")
        return True

    @keyword('NetBak: Validate NB repo state after detach from HDP')
    def validate_nb_repo_state_after_detach_from_hdp(self):
        """
        Lib is to Validate NB repo state after detach from HDP
        """
        LOGGER.info("|___Validate NB repo state after detach from HDP___|")

        try:
            WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((
                    By.CSS_SELECTOR, Loc.OVERVIEW_DROPDOWN_BUTTON_CSS)))
        except TimeoutException:
            raise ValueError("NetBak application is not loaded")

        # Validate NB repo warning
        self.validate_nb_repo_warning()

        # Validate NetBak backup button
        self.validate_backup_button_grayed_out()

        # Validate NB backup button warning tooltip
        self.validate_nb_backup_button_warning_tooltip()

        LOGGER.info("Validate NetBak repository state after detach from HDP\n")
        return True

    @keyword
    def validate_nb_repo_warning(self):
        """
        Lib to Validate NB repo warning
        """
        LOGGER.info("|___Validate NB repo warning___|")

        self.driver.find_element(
            By.CSS_SELECTOR, Loc.OVERVIEW_DROPDOWN_BUTTON_CSS).click()
        self.validate_nb_loading_page()
        try:
            WebDriverWait(self.driver, 10).until(
                ec.element_to_be_clickable((
                    By.CSS_SELECTOR, Loc.REPO_WARNING_ICON_CSS)))
        except TimeoutException:
            raise ValueError("NetBak repo is not become warning state after"
                             "detaching from HDP")
        warning_icon_path = self.driver.find_element(
            By.CSS_SELECTOR, Loc.REPO_WARNING_ICON_CSS)
        self.mouse_pointer.move_to_element(warning_icon_path).click().perform()
        warning_hover_text = WebDriverWait(self.driver, 10).until(
             ec.presence_of_element_located(
                 (By.CSS_SELECTOR, Loc.HOVER_INFO_CSS))).text
        if warning_hover_text != Loc.REPO_WARNING_CONTENT:
            raise ValueError("NetBak repository is not found in warning "
                             "state")

        LOGGER.info("Validated NB repo warning after detach repo from HDP\n")
        return True

    @keyword('NetBak: Validate backup button grayed out')
    def validate_backup_button_grayed_out(self):
        """
        Lib to Validate NetBak backup button
        """
        LOGGER.info("|___Validate NetBak backup button___|")

        try:
            WebDriverWait(self.driver, 10).until_not(
                ec.element_to_be_clickable((
                    By.CSS_SELECTOR, Loc.START_BACKUP_BUTTON_CLS)))
        except TimeoutException:
            raise ValueError("Backup button is not grayed out")

        LOGGER.info("Validated NB backup button grayed out\n")
        return True

    @keyword
    def validate_nb_backup_button_warning_tooltip(self):
        """
        Lib to Validate NB backup button warning tooltip
        """
        LOGGER.info("|___Validate NB backup button warning tooltip___|")

        warning_tooltip_path = self.driver.find_element(
            By.CLASS_NAME, Loc.START_BACKUP_BUTTON_CLS)
        self.mouse_pointer.move_to_element(
            warning_tooltip_path).click().perform()
        backup_hover_text = WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located(
                (By.CSS_SELECTOR, Loc.BACKUP_BUTTON_WARNING_XPATH))).text

        if backup_hover_text not in Loc.BACKUP_WARNING_CONTENTS:
            raise ValueError("NetBak backup button is not found in warning "
                             "state")

        LOGGER.info("Validated NB backup button warning tooltip\n")
        return True

    @keyword('NetBak: Validate backup functionality after multiple login')
    def validate_backup_functionality_after_multiple_login(
            self, iteration, chromedriver_path, app_path, nas_ip,
            username, password):
        """
        Lib is to validate backup functionality after multiple login

        Arguments
        | iteration: Iteration count for multiple login to NetBak
        | chromedriver_path: Executable path of chromedriver
        | app_path: Executable path of NetBak app
        | nas_ip: First NAS IP to be entered to connect to app
        | username: Username of the NAS
        | password: Password of the NAS
        """
        LOGGER.info("|___Validate NB login with multiple NAS___|")

        # Validate Backup functionality after multiple login
        for index in range(1, int(iteration)):
            self.launch_app(chromedriver_path, app_path)
            self.login_app(nas_ip, username, password)
            self.start_backup_job()
            self.validate_expected_backup_job_status(expected_status='Running')
            self.stop_backup_job()
            self.close_app()
            LOGGER.debug(
                f'Validated backup functionality for {index} times')

        LOGGER.info(
            "Validated backup job functionality after multiple login\n")
        return True

    @keyword(
        'NetBak: Validate NetBak backup job state after disabled from HDP')
    def validate_netbak_backup_job_state_after_disabled_from_hdp(self):
        """
        Lib to Validate NetBak backup job state after disabled from HDP
        """
        LOGGER.info(
            "|___Validate NetBak backup job state after disabled from HDP___|")

        # Validate NetBak backup job status
        self.validate_expected_backup_job_status(
            expected_status=Loc.BACKUP_JOB_ABORTED_TEXT)

        # Validate Netbak backup button status
        self.validate_backup_button_grayed_out()

        # Validate NetBak backup button warning tooltip
        self.validate_nb_backup_button_warning_tooltip()

        LOGGER.info("Validated NetBak backup job state after disabled from "
                    "HDP\n")
        return True

    @keyword('NetBak: Validate NetBak backup job state after enabled from HDP')
    def validate_netbak_backup_job_state_after_enabled_from_hdp(self):
        """
        Lib to Validate NetBak backup job state after enabled from HDP
        """
        LOGGER.info(
            "|___Validate NetBak backup job state after enabled from HDP___|")

        # Validate NetBak backup job status
        self.validate_expected_backup_job_status(
            expected_status=Loc.BACKUP_JOB_NOT_YET_RUN_TEXT)

        # Validate Netbak backup button status
        self.validate_netbak_backup_button_is_clickable()

        LOGGER.info(
            "Validated NetBak backup job state after enabled from HDP\n")
        return True

    @keyword('Validate NetBak backup button is clickable')
    def validate_netbak_backup_button_is_clickable(self):
        """
        Lib is to validate the Netbak backup button is clickable or not
        """
        LOGGER.info("|___validate NetBak button is clickable___|")

        try:
            WebDriverWait(self.driver, 10).until(
                ec.element_to_be_clickable((
                    By.CLASS_NAME, Loc.START_BACKUP_BUTTON_CLS)))
        except TimeoutException:
            raise ValueError("Backup button is grayed out")

        LOGGER.info("Validated NetBak backup job button is clickable\n")
        return True
