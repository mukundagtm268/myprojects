#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
from datetime import date
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import ElementNotInteractableException
from NAS_Libraries.robotlogger import RobotLogger
from NAS_Libraries.robotkeyword import keyword
from HDP_Libraries.main import HDP
from HDP_Libraries.locators import Locators as Loc

LOGGER = RobotLogger(__name__)


class BackupExplorer:
    def __init__(self):
        self.hdp = HDP()

    @keyword('HDP: Backup Explorer: Open backup explorer')
    def open_backup_explorer(self, driver):
        """
        Lib to open backup explorer from backup page

        Arguments
        | driver: Web driver of HDP
        """
        LOGGER.info('|___Open Backup Explorer___|')

        driver.switch_to.window(driver.window_handles[0])
        self.hdp.validate_loading_page(driver)
        # Select Backup Explorer from backup page
        driver.find_element(By.CSS_SELECTOR, Loc.HDP_BACKUP_CSS).click()
        driver.find_element(By.CSS_SELECTOR, Loc.HDP_BACKUP_MORE_BUTTON_CSS).\
            click()
        driver.find_element(By.XPATH, Loc.HDP_BACKUP_EXPLORER_XPATH).click()

        # Validate backup explorer page is opened
        driver.switch_to.window(driver.window_handles[1])
        WebDriverWait(driver, 20).until(ec.presence_of_element_located((
            By.XPATH, Loc.HDP_BACKUP_EXPLORER_SUBHEADER_XPATH)))
        driver.switch_to.window(driver.window_handles[0])

        LOGGER.info('Backup explorer is successfully opened\n')
        return True

    @keyword('HDP: Backup Explorer: Download file')
    def download_file(self, driver, mouse_driver, drive_letter,
                      path=None, filename=None):
        """
        Lib covers below scenarios:
        1. Download complete drive files
        2. Validate too many files pop up for step 1
        3. If pop up observed:
               1. download first random file available in sub folders in case
                  path and filename variables are not passed
               2. If path, filename variables are passed, download file
                  from specified path
        4. Covers scenario if no data present in folders/ sub folders,
           click back button and select folder
        5. Also, for the path specified, if element is not visible, then
           scroll to the path using mouse driver and scroll to first element in
           next sub folder, because move_to_element uses top to bottom approach

        Arguments
        | driver: Web driver of HDP
        | mouse_driver: Mouse Web Driver of HDP
        | drive_letter: Driver letter name for file download
        | path: Path of the file to be downloaded
        | filename: Name of the file to be downloaded
        """
        LOGGER.info('|___Downloading File___|')

        # Validate if drive letter argument is passed
        if drive_letter is None:
            raise ValueError(
                "Drive letter is required argument to download file")

        self.hdp.validate_loading_page(driver)
        # Select drive from which files to be downloaded
        driver.switch_to.window(driver.window_handles[1])
        LOGGER.debug(f"Window handles: {driver.window_handles}")
        LOGGER.debug(f"Current window: {driver.current_window_handle}")
        driver.find_element(
            By.XPATH, Loc.HDP_EXPLORER_SELECT_RADIO_LABEL_NAME_BASED_XPATH.
            format(f"{drive_letter}:\\")).click()

        # Click download to download the files
        driver.find_element(
            By.XPATH, Loc.HDP_EXPLORER_USER_DOWNLOAD_XPATH).click()
        self.hdp.validate_loading_page(driver, timeout=500)

        # Validate too many files to download pop up
        pop_up_flag = self.validate_too_files_pop_up(driver)
        if pop_up_flag:
            self.download_folders_files_from_drive(
                driver, mouse_driver, drive_letter, path, filename)
        driver.switch_to.window(driver.window_handles[0])

        LOGGER.info('Downloaded file from backup explorer successfully\n')
        return True

    @keyword('HDP: Backup Explorer: Validate too files pop up')
    def validate_too_files_pop_up(self, driver):
        """
        Lib to validate too many files to download pop up after selecting
        drive and clicking download option

        Arguments
        | driver: Web driver of HDP
        """
        LOGGER.info("|___Validate too files pop up___|")

        try:
            driver.find_element(By.CSS_SELECTOR,
                                Loc.HDP_EXPLORER_TOO_MANY_FILES_POP_UP_CSS)
        except NoSuchElementException:
            LOGGER.info("Too many files to download pop is not found")
            return False
        driver.find_element(By.XPATH, Loc.HDP_OK_BUTTON_XPATH).click()

        LOGGER.info("Too many files to download pop found\n")
        return True

    @keyword('HDP: Backup Explorer: Download folders files from drive')
    def download_folders_files_from_drive(
            self, driver, mouse_driver, drive_letter, path, filename):
        """
        Lib to download files based on path and filename
        If Path and filename are none, then downloads the first random file
        available in sub folders

        Arguments
        | driver: Web driver of HDP
        | mouse_driver: Mouse web driver of HDP
        | drive_letter: Driver letter name for file download
        | path: Path of the file to be downloaded
        | filename: Name of the file to be downloaded
        """
        LOGGER.info("|___Download folders/ Files from drive___| ")

        # Switch to Backup Explorer window
        driver.switch_to.window(driver.window_handles[1])

        # Select drive
        driver.find_element(
            By.XPATH, Loc.HDP_EXPLORER_SELECT_DRIVE_NAME_XPATH.format(
                drive_letter)).click()
        self.hdp.validate_loading_page(driver)

        # Select Random first file occurrence
        if path is None or filename is None:
            LOGGER.info("Validating downloading random file..")
            self.select_file_from_sub_folders(driver)
        # Select file from provided path
        else:
            self.select_file_from_expected_path(
                driver, mouse_driver, path, filename)

        # Click download to download the files
        driver.find_element(
            By.XPATH, Loc.HDP_EXPLORER_USER_DOWNLOAD_XPATH).click()
        self.hdp.validate_loading_page(driver, timeout=150)

        # Switch back to main window
        driver.switch_to.window(driver.window_handles[0])

        LOGGER.info("Downloaded folder files from drive\n")
        return True

    @keyword('HDP: Backup Explorer: Select file from expected path')
    def select_file_from_expected_path(
            self, driver, mouse_driver, path, filename):
        """
        Lib to select file based on path and filename provided by user

        Arguments
        | driver: Web driver of HDP
        | mouse_driver: Mouse Web Driver of HDP
        | path: Path of the file to be downloaded
        | filename: Name of the file to be downloaded
        """
        LOGGER.info("|___Select file from expected path___|")

        path = path.replace("\\", "/").split("/")
        LOGGER.debug(f"Paths to be selected: {path}")

        # Scrolling to expected paths and selecting elements
        for folder in path:
            LOGGER.debug(f"Selecting {folder}...")
            element = driver.find_element(
                By.XPATH, Loc.HDP_EXPLORER_SELECT_FOLDER_XPATH.format(folder))
            # Click element based on appearance
            try:
                element.click()
            except ElementNotInteractableException:
                mouse_driver.move_to_element(element).click().perform()
            self.hdp.validate_loading_page(driver)

            # Scroll to first element
            # move_to_element used only top to bottom approach,
            # so the elements present above are not found
            LOGGER.debug("Scroll to first element...")
            element = driver.find_element(
                By.XPATH, Loc.HDP_EXPLORER_SELECT_FIRST_DRIVE_FOLDER_XPATH)
            driver.execute_script("arguments[0].scrollIntoView();", element)

        # Scroll to filename and Select filename radio label
        LOGGER.debug(f"Selecting file {filename}...")
        element = driver.find_element(
            By.XPATH, Loc.HDP_EXPLORER_SELECT_RADIO_LABEL_NAME_BASED_XPATH.
            format(filename))
        # Click element based on appearance
        try:
            element.click()
        except ElementNotInteractableException:
            mouse_driver.move_to_element(element).click().perform()
        self.hdp.validate_loading_page(driver)

        # Validate file is selected to download
        try:
            WebDriverWait(driver, 30).until(ec.element_to_be_clickable((
                By.XPATH, Loc.HDP_EXPLORER_USER_DOWNLOAD_XPATH)))
        except TimeoutException:
            raise ValueError("File is not selected from path to download")

        LOGGER.info("Selected file from expected path\n")
        return True

    @keyword('HDP: Backup Explorer: Select file from sub folders')
    def select_file_from_sub_folders(self, driver):
        """
        Lib to select random file from folders and sub folders

        Arguments
        | driver: Web driver of HDP
        """
        LOGGER.info("|___Select file from sub folders___|")

        # Go to sub folders and check for first file occurrence
        while True:
            data_present = self.validate_data_present_in_folder(driver)
            if not data_present:
                # Click back button and set occurrence to 1
                driver.find_element(By.CSS_SELECTOR,
                                    Loc.HDP_EXPLORER_BACK_BUTTON_CSS).click()
                occurrence = 1
                break
            else:
                occurrence = self.get_file_occurrence_in_sub_folders(driver)
                if occurrence:
                    break
            LOGGER.info("Selecting folder...")
            driver.find_element(
                By.XPATH, Loc.HDP_EXPLORER_SELECT_FIRST_DRIVE_FOLDER_XPATH). \
                click()
            self.hdp.validate_loading_page(driver)

        # Select file based on occurrence
        driver.find_element(
            By.XPATH,
            Loc.HDP_EXPLORER_SELECT_RADIO_LABEL_FOR_FILE_OCCURRENCE_XPATH.
            format(occurrence)).click()

        # Validate file is selected to download
        try:
            WebDriverWait(driver, 30).until(ec.element_to_be_clickable((
                By.XPATH, Loc.HDP_EXPLORER_USER_DOWNLOAD_XPATH)))
        except TimeoutException:
            raise ValueError("File is not selected to download")

        LOGGER.info("Selected file from sub folders\n")
        return True

    @keyword('HDP: Backup Explorer: Get file occurrence in sub folders')
    def get_file_occurrence_in_sub_folders(self, driver):
        """
        Lib to get the file occurrence in the sub folder if exists,
        else returns False

        Arguments
        | driver: Web driver of HDP
        """
        LOGGER.info("|___Get file occurrence in sub folders___|")

        # Check the type for all the data available in sub folders
        folders_count = driver.find_elements(
            By.CSS_SELECTOR, Loc.HDP_EXPLORER_DRIVE_FOLDERS_COUNT_CSS)
        for i in range(1, len(folders_count)+1):
            file_type = driver.find_element(
                By.XPATH, Loc.HDP_EXPLORER_FILE_TYPE_XPATH.format(i)).text
            if file_type == Loc.FILE_TYPE_TEXT:
                file_occurrence = i
                break

        if not file_occurrence:
            LOGGER.info("No files exist in current folder")
            return False

        LOGGER.info(f"Retrieved file occurrence: {file_occurrence}\n")
        return file_occurrence

    @keyword('HDP: Backup Explorer: Validate data present in folder')
    def validate_data_present_in_folder(self, driver):
        """
        Lib to validate if sub folders/ files present in folder

        Arguments
        | driver: Web driver of HDP
        """
        LOGGER.info("|___Validate data present in folder___|")

        folders_count = driver.find_elements(
            By.CSS_SELECTOR, Loc.HDP_EXPLORER_DRIVE_FOLDERS_COUNT_CSS)
        if len(folders_count) == 0:
            LOGGER.info("No data present in folder")
            return False

        LOGGER.info("Folder has sub folder/ files present\n")
        return True

    @keyword("HDP: Validate Tooltip Job")
    def validate_tooltip_job(self, driver, count=1):
        """
        Lib to Validate tooltip for number of times job is run

        Arguments
        | driver: Web driver of HDP
        | count: count of tooltips to be validated
        |         ex. 1 for single job run verification
        |             2 for double job run verification

        """
        LOGGER.info('|___Validating Tooltip status___|')

        if not count:
            raise ValueError("Count value to validate tooltip not provided")

        driver.switch_to.window(driver.window_handles[1])
        backup_count = driver.find_element(
            By.XPATH, Loc.HDP_EXPLORER_BACKUP_COUNT).text

        # Validate tooltips based on count and job runs
        if int(backup_count) == 0 or int(backup_count) != count:
            raise ValueError("Expected tooltip count mismatch: \n"
                             f"Expected count: {count}\n"
                             f"Received count: {backup_count}")

        driver.switch_to.window(driver.window_handles[0])

        LOGGER.info(f"Validated tooltip for {count} runs\n")
        return True

    @keyword('HDP: Backup Explorer: Validate options in right Calendar')
    def validate_options_in_right_calendar(self, driver):
        """
        Lib to Validate options in right Calendar in backup explorer

        Arguments
        | driver: Web driver of HDP
        """
        LOGGER.info("|___Validate options in right Calendar___|")

        driver.switch_to.window(driver.window_handles[1])

        # Click right calendar, select year and validate
        self.select_option_from_right_calendar(driver, Loc.YEAR_TEXT)

        # Click right calendar, select month and validate
        self.select_option_from_right_calendar(driver, Loc.MONTH_TEXT)

        driver.switch_to.window(driver.window_handles[0])

        LOGGER.info("Validated options in right calendar\n")
        return True

    @keyword
    def select_option_from_right_calendar(self, driver, option):
        """
        Lib to select option (Month/ Year) from right calendar

        Arguments
        | driver: Web driver of HDP
        | option: Option to be selected ex. Month, Year
        """
        LOGGER.info(f"|___Select {option} from right calendar___|")

        if option not in Loc.RIGHT_CALENDAR_OPTIONS:
            raise ValueError("Option provided is not the expected option:\n"
                             f"Expected option: {Loc.RIGHT_CALENDAR_OPTIONS}\n"
                             f"Provided option: {option}")

        if option == Loc.YEAR_TEXT:
            i = 2
            expected_text = Loc.YEAR_TEXT
        else:
            i = 1
            expected_text = Loc.MONTH_TEXT

        # Click right calendar and select option (month/year)
        driver.find_element(
            By.CSS_SELECTOR,
            Loc.HDP_EXPLORER_RIGHT_CALENDAR_DROPDOWN_CSS).click()
        try:
            WebDriverWait(driver, 5).until(ec.presence_of_element_located((
                By.CSS_SELECTOR,
                Loc.HDP_EXPLORER_OPTION_SELECT_RIGHT_CALENDAR_CSS.format(1))))
        except TimeoutException:
            raise ValueError(
                "Right side calendar is not expanded after click")
        driver.find_element(
            By.CSS_SELECTOR,
            Loc.HDP_EXPLORER_OPTION_SELECT_RIGHT_CALENDAR_CSS.format(
                i)).click()

        # Validate expected option is selected from right calendar
        right_calendar_text = driver.find_element(
            By.CSS_SELECTOR, Loc.HDP_EXPLORER_RIGHT_CALENDAR_TEXT_CSS).text
        if right_calendar_text != expected_text:
            raise ValueError(f"{option} is not selected in right calendar")

        LOGGER.info(f"Validated {option} selection from right calendar\n")
        return True

    @keyword
    def get_today_date(self):
        """
        Lib to get today's date
        """
        LOGGER.info("|___Get today's date___|")

        today = int(str(date.today()).split("-")[-1])

        if not today:
            raise ValueError("Today's date not retrieved")

        LOGGER.info(f"Today's date retrieved: {today}\n")
        return today

    @keyword('HDP: Backup Explorer: Validate calendar scroll dates')
    def validate_calendar_scroll_dates(self, driver):
        """
        Lib to validate current date, ascending and descending dates in
        calendar scroll items

        Arguments
        | driver: Web driver of HDP
        """
        LOGGER.info("|___Validate Calendar scroll dates___|")

        driver.switch_to.window(driver.window_handles[1])
        self.hdp.validate_loading_page(driver)
        # Get Today's date
        today = self.get_today_date()

        # Get current date occurrence from Calendar
        dates_count = driver.find_elements(
            By.CSS_SELECTOR, Loc.HDP_EXPLORER_SCROLL_DATES_COUNT_CSS)
        LOGGER.debug(f"Total dates count: {len(dates_count)}")
        for i in range(1, len(dates_count)+1):
            date_text = driver.find_element(
                By.CSS_SELECTOR, Loc.HDP_EXPLORER_DATES_TEXT_CSS.format(
                    i)).text
            LOGGER.debug(f"Retrieved date text: {date_text}")
            if not date_text:
                continue
            if today == int(date_text):
                current_date = date_text
                ascending_date = driver.find_element(
                    By.CSS_SELECTOR, Loc.HDP_EXPLORER_DATES_TEXT_CSS.format(
                        i-1)).text
                descending_date = driver.find_element(
                    By.CSS_SELECTOR, Loc.HDP_EXPLORER_DATES_TEXT_CSS.format(
                        i+1)).text
                break

        # Validate current date, ascending date, descending date
        if ascending_date > current_date > descending_date:
            raise ValueError(f"Expected dates mismatch:\n"
                             f"Today's Date: {today}\n"
                             f"Current Date: {current_date}\n"
                             f"Ascending Date: {ascending_date}\n"
                             f"Descending Date: {descending_date}")

        # Switch back to main window
        driver.switch_to.window(driver.window_handles[0])

        LOGGER.info("Validated calendar scroll dates\n")
        return True

    @keyword('HDP: Backup Explorer: Validate current date in left calendar')
    def validate_current_date_in_left_calendar(self, driver):
        """
        Lib to validate current date and the date selected
        on the left side calendar

        Arguments
        | driver: Web driver of HDP
        """
        LOGGER.info("|___Validate Current date in left calendar___|")

        driver.switch_to.window(driver.window_handles[1])
        # Click to calendar on left to dropdown
        driver.find_element(
            By.CLASS_NAME, Loc.HDP_EXPLORER_LEFT_CALENDAR_DROPDOWN_CLS).click()
        try:
            WebDriverWait(driver, 5).until(ec.presence_of_element_located((
                By.CSS_SELECTOR,
                Loc.HDP_EXPLORER_SELECTED_DATE_LEFT_CALENDAR_CSS)))
        except TimeoutException:
            raise ValueError("Left side calendar not expanded after click")

        # Validate date selected in calendar is today's date
        today = self.get_today_date()
        date_selected = driver.find_element(
            By.CSS_SELECTOR,
            Loc.HDP_EXPLORER_SELECTED_DATE_LEFT_CALENDAR_CSS).text
        if today != int(date_selected):
            raise ValueError("Today date is not selected in calendar: \n"
                             f"Today date: {today}\n"
                             f"Date Selected: {date_selected}")

        # Switch back to main window
        driver.switch_to.window(driver.window_handles[0])

        LOGGER.info("Validated current date selected successfully\n")
        return True

    @keyword("HDP: Backup Explorer: Validate download disable")
    def validate_download_disable(self, driver):
        """
        Lib to Validate download button is disabled
        when no volume is selected to download.

        Arguments
        | driver: Web driver of HDP
        """
        LOGGER.info('|___Validate download button disable___|')

        driver.switch_to.window(driver.window_handles[1])
        try:
            driver.find_element(By.XPATH, Loc.HDP_EXPLORER_USER_DOWNLOAD_XPATH)
            raise ValueError(
                "Download button is enabled without selecting the volumes")
        except NoSuchElementException:
            pass
        driver.switch_to.window(driver.window_handles[0])

        LOGGER.info("Validated download button disabled successfully\n")
        return True

    @keyword("HDP: Backup Explorer: Validate No Data Popup")
    def validate_no_data_popup(self, driver):
        """
        Lib to Validate no data backup text

        Arguments
        | driver: Web driver of HDP
        """
        LOGGER.info('|___Validating no data backup text___|')

        driver.switch_to.window(driver.window_handles[1])
        no_data_text = driver.find_element(
            By.CSS_SELECTOR, Loc.HDP_EXPLORER_TOO_MANY_FILES_POP_UP_CSS).text
        LOGGER.info(f"Popup Message: {no_data_text}\n")
        driver.switch_to.window(driver.window_handles[0])

        if no_data_text not in Loc.NO_DATA_POPUP:
            raise ValueError(
                "Already backup jobs are present in backup explorer.")
        
        LOGGER.info('validated No Data Popup\n')
        return True
