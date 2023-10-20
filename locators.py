#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Locators:
    def __init__(self):
        pass

    # Data
    # NAS title
    NAS_TITLE = "NAS"
    HDP_TITLE = "Hyper Data Protector"
    HDP_DETACH_TEXT = "Detach"
    HDP_ATTACH_TEXT = "Attach"
    HDP_JOB_RUNNING = "Running"
    FILE_TYPE_TEXT = "file"
    YEAR_TEXT = "Year"
    MONTH_TEXT = "Month"
    RIGHT_CALENDAR_OPTIONS = ["Year", "Month"]
    NO_DATA_POPUP = ["Unable to restore this job. "
                     "This job has not finished successfully",
                     "Data not found please try again"]
    HDP_EXPECTED_JOB_STATUS = ["Disabled"]
    INV_REFRESH_LOGS = 'Refreshed NetBak PC Agent inventory "{}".'
    REPO_REFRESH_LOGS = 'Refreshed repository "{}".'

    # Locators
    # NAS Login
    NAS_USERNAME_ID = "username"
    NAS_PASSWORD_ID = "pwd"
    NAS_NEXT_BUTTON_CSS = ".pre-login"
    NAS_SUBMIT_BUTTON_ID = "submit"

    # HDP welcome page
    HDP_SKIP_GUIDE_XPATH = "//body//div[9]//*[local-name()='svg']"

    # HDP general
    HDP_LOADING_PAGE_CSS = "div.qcss-mask-loading"
    HDP_OK_BUTTON_XPATH = "//button[contains(text(),'OK')]"
    HDP_YES_BUTTON_XPATH = "//button[contains(text(),'Yes')]"
    HDP_DISABLE_BACKUP_XPATH = "//span[contains(text(),'Disable')]"
    HDP_ENABLE_BACKUP_XPATH = "//span[contains(text(),'Enable')]"

    # HDP Repository page
    HDP_REPOSITORY_CSS = "span.icon-sidemenu-storage"
    HDP_DETACH_REPOSITORY_XPATH = "//span[contains(text(),'Detach')]"
    HDP_ATTACH_REPOSITORY_XPATH = "//span[contains(text(),'Attach')]"
    HDP_DELETE_REPOSITORY_XPATH = "//span[contains(text(),'Delete')]"
    HDP_DELETE_ACCEPT_REPOSITORY_XPATH = "//div[@class='ux-radio']" \
                                         "//label//*[local-name()='svg']"
    HDP_REPOSITORY_DETACH_ATTACH_TEXT_XPATH = \
        "//div[@class='scrollbar-container ps']/div[1]/div[1]//span"
    HDP_REPOSITORY_COUNT_CSS = "span.text-elipses"
    HDP_REPOSITORY_MORE_BUTTON_CSS = "div.moreBtn svg"
    HDP_CREATE_REPOSITORY_XPATH = "//span[contains(text(),'Create')]"

    # HDP Inventory page
    HDP_INVENTORY_CSS = "span.icon-sidemenu-inventory"
    HDP_WINDOWS_INV_XPATH = "//span[contains(text(),'Windows PC/Server')]"
    HDP_INV_DELETE_ACCEPT_XPATH = "//input[@type='checkbox']"
    HDP_INV_COUNT_CSS = "div.rt-tr-group"
    HDP_ADD_INVENTORY_XPATH = "//span[contains(text(),'Add Inventory')]"
    HDP_DELETE_INV_XPATH = "//div[@class='rt-tr-group'][1]/div[1]" \
                           "/div[6]/div[1]/div[2]"

    # HDP Backup job page
    HDP_BACKUP_CSS = "span.icon-sidemenu-backup"
    HDP_SELECT_BACKUP_XPATH = "//div[@class='job-list']/div[1]/div[1]"
    HDP_BACKUP_MORE_BUTTON_CSS = "div.moreBtn"
    HDP_STOP_BACKUP_XPATH = "//div[@data-value='stop']"
    HDP_DELETE_BACKUP_XPATH = "//span[contains(text(),'Delete')]"
    HDP_ACCEPT_DELETE_BACKUP_ID = "checked"
    HDP_BACKUP_JOBS_COUNT_XPATH = "//div[@class='job-list']/div[1]/div"
    HDP_MOUSE_OUT_BACKUP_CSS = "div.Rigth-Arrow"
    HDP_JOB_NAME_XPATH = "//div[@class='job-list']/div[1]/div[1]" \
                         "/div[1]/div[1]//span"
    HDP_BACKUP_HYPERLINK_STATUS_XPATH = \
        "//div[@class='qcss-dialog-item-content']/div[3]/span[2]"
    HDP_BACKUP_VOLUME_COUNT_XPATH = "//div[@class='content']/div[2]/div[2]" \
                                    "/div[1]/div[1]/div[2]/div[1]/div[1]/div"
    HDP_BACKUP_VOLUMES_TEXT_XPATH = "//div[@class='content']/div[2]/div[2]/d" \
                                    "iv[1]/div[1]/div[2]/div[1]/div[1]/div[{}]"
    HDP_SELECT_JOB_NAME_XPATH = \
        "//div[@class='job-list']//span[@data-tooltip='{}']"
    HDP_DISABLED_BACKUP_STRING_XPATH = \
        "//div[@class='job-list']/div[1]/div[1]/div[1]/div[2]"
    HDP_ENABLED_BACKUP_STRING_XPATH = \
        "//div[@class='job-list']/div[1]/div[1]/div[1]/div[2]/span[1]/span[2]"

    # HDP Backup Explorer
    HDP_BACKUP_EXPLORER_XPATH = "//span[contains(text(),'Backup Explorer')]"
    HDP_EXPLORER_SELECT_RADIO_LABEL_NAME_BASED_XPATH = \
        "//div[contains(text(),'{}')]/ancestor::div[@class='rt-tr-group']" \
        "//div[@class='ux-radio']"
    HDP_EXPLORER_USER_DOWNLOAD_XPATH = "//div[@class ='tree-footer']" \
                                       "//button[@class='download-btn ']"
    HDP_BACKUP_EXPLORER_SUBHEADER_XPATH = \
        "//div[contains(text(),'Backup Explorer')]"
    HDP_EXPLORER_TOO_MANY_FILES_POP_UP_CSS = "div.qcss-dialog-item-content"
    HDP_EXPLORER_SELECT_DRIVE_NAME_XPATH = \
        "//span[@class='cell-jobName']//div[contains(text(), '{}:')]"
    HDP_EXPLORER_DRIVE_FOLDERS_COUNT_CSS = "div.rt-tr-group"
    HDP_EXPLORER_SELECT_FOLDER_XPATH = "//div[@class='rt-tr-group']" \
                                       "//div[contains(text(), '{}')]"
    HDP_EXPLORER_SELECT_FIRST_DRIVE_FOLDER_XPATH = \
        "//div[@class='rt-tr-group'][1]/div/div[2]//span"
    HDP_EXPLORER_FILE_TYPE_XPATH = "//div[@class='rt-tr-group'][{}]/div/div[4]"
    HDP_EXPLORER_SELECT_RADIO_LABEL_FOR_FILE_OCCURRENCE_XPATH = \
        "//div[@class='rt-tr-group'][{}]/div/div[1]/div"
    HDP_EXPLORER_BACK_BUTTON_CSS = "div.back-image svg"
    HDP_EXPLORER_BACKUP_COUNT = \
        "//div[@class= 'scroll-item selected']//div[@class= 'excPointstext']"
    HDP_EXPLORER_SCROLL_DATES_COUNT_CSS = "div.scroll-item"
    HDP_EXPLORER_DATES_TEXT_CSS = \
        "div.scroll-item:nth-of-type({}) span.scroll-date-text"
    HDP_EXPLORER_LEFT_CALENDAR_DROPDOWN_CLS = "monthsub"
    HDP_EXPLORER_SELECTED_DATE_LEFT_CALENDAR_CSS = \
        "div.DayPicker-Day--selected .dayPickCellDateNum"
    HDP_EXPLORER_RIGHT_CALENDAR_DROPDOWN_CSS = "div.dropdown_sub"
    HDP_EXPLORER_OPTION_SELECT_RIGHT_CALENDAR_CSS = \
        "div.droptext:nth-of-type({}) .opttext"
    HDP_EXPLORER_RIGHT_CALENDAR_TEXT_CSS = "div.dropText"

    # HDP System
    HDP_SYSTEM_CSS = "span.icon-sidemenu-system"
    HDP_SYSTEM_LOGS_COUNT_CSS = "div.rt-tr-group"
    HDP_SYSTEM_LOGS_CONTENT_XPATH = \
        "//div[@class='rt-tr-group'][{}]/div/div[4]/div[1]/div[1]/div[2]"
    HDP_SYSTEM_LOGS_DATE_TIME_XPATH = \
        "//div[@class='rt-tr-group'][{}]/div/div[1]/div[1]"
