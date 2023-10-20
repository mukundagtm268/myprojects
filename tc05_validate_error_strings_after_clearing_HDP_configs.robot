*** Settings ***
Documentation  A test suite to validate netback app
...            Created by Sachin
Resource     ../Keywords/Main.robot
Library      Selenium2Library

Test Setup   Run Keywords
...          Clean HDP Environment  ${URL}  ${CHROMEDRIVER_PATH}  ${NAS_USER}  ${NAS_PWD}
...    AND   NetBak: Launch app  ${CHROMEDRIVER_PATH}  ${APP_PATH}
...    AND   NetBak: Login app  ${NAS_IP}  ${NAS_USER}  ${NAS_PWD}
...    AND   NetBak: Create backup job  ${SHARED_FOLDER}  ${REPO_NAME}  ${DRIVE_LETTER}

Test Teardown  NetBak: Close app

*** Variables ***
# App Paths
${CHROMEDRIVER_PATH}  C:\\Users\\Dell\\Netback_Agent\\timeback_automation\\chromedriver.exe
${APP_PATH}  C:\\Program Files\\QNAP\\NetBakPCAgent\\App\\NetBak PC Agent.exe

# NAS data
${NAS_IP}      ${None}
${NAS_USER}    admin
${NAS_PWD}     ${None}

# HDP data
${BROWSER}  Chrome
${URL}      http://${NAS_IP}:8080/HyperDataProtector/#/
${REMOTE_EXECUTION}  ${False}

# Repository data
${DRIVE_LETTER}     ${None}
${SHARED_FOLDER}    Netbak_Repo
${REPO_NAME}        netbak_repo

*** Test Cases ***
Validate error string after deleting Inventry from HDP
    ${jobName}  ${repositoryName}  ${inventoryName}=  NetBak: Get backup job details
    ${webDriver}  ${mouseDriver}=  HDP: Launch browser
    ...  url=${URL}
    ...  chromedriver_path=${CHROMEDRIVER_PATH}
    HDP: Login: Login HDP
    ...  driver=${webDriver}
    ...  username=${NAS_USER}
    ...  password=${NAS_PWD}
    HDP: Inventory: Delete inventory
    ...  driver=${webDriver}
    ...  inventory_name=${inventoryName}
    HDP: Close browser
    ...  driver=${webDriver}
    NetBak: Validate config broken dialog content

Validate error string after deleting Repository from HDP
    ${jobName}  ${repositoryName}  ${inventoryName}=  NetBak: Get backup job details
    Clean HDP Environment
    ...  url=${URL}
    ...  chromedriverPath=${CHROMEDRIVER_PATH}
    ...  nasUser=${NAS_USER}
    ...  nasPwd=${NAS_PWD}
    NetBak: Validate config broken dialog content
