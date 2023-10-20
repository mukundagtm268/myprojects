*** Settings ***
Documentation  A test suite to validate netback app
...            Created by Sachin
Resource     ../Keywords/Main.robot
Library      Selenium2Library

Suite Setup   Run Keywords
...          Clean HDP Environment  ${URL}  ${CHROMEDRIVER_PATH}  ${NAS_USER}  ${NAS_PWD}
...    AND   NetBak: Launch app  ${CHROMEDRIVER_PATH}  ${APP_PATH}
...    AND   NetBak: Login app  ${NAS_IP}  ${NAS_USER}  ${NAS_PWD}
...    AND   NetBak: Create backup job  ${SHARED_FOLDER}  ${REPO_NAME}  ${DRIVE_LETTER}
...    AND   NetBak: Close app

Test Setup   Run Keywords
...          NetBak: Launch app  ${CHROMEDRIVER_PATH}  ${APP_PATH}
...    AND   NetBak: Login app  ${NAS_IP}  ${NAS_USER}  ${NAS_PWD}

Test Teardown  NetBak: Close app

*** Variables ***
# App Paths
${CHROMEDRIVER_PATH}  C:\\Users\\Dell\\Netback_Agent\\timeback_automation\\chromedriver.exe
${APP_PATH}  C:\\Program Files\\QNAP\\NetBakPCAgent\\App\\NetBak PC Agent.exe

# NAS data
${NAS_IP}      ${None}
${NAS_USER}    admin
${NAS_PWD}     ${None}

# Volume and REPO data
${DRIVE_LETTER}     ${None}
${SHARED_FOLDER}    NB_SharedFolder
${REPO_NAME}    NB_REPO

# NB Help page content
${NB_TUTORIAL_TITLE}  How to Back Up and Import HDP Repositories to a Remote QNAP NAS | QNAP
${ABOUT_NB_TITLE}  Master your digital files for work and daily life | QNAP (IN)
${EXP_VERSION}  1.0.0

# Browser data
${URL}   http://${NAS_IP}:8080/HyperDataProtector/#/
${URL2}  https://www.qnap.com/en/how-to/tutorial/article/how-to-back-up-and-import-hdp-repositories-to-a-remote-qnap-nas
${URL3}  https://www.qnap.com/en-in
${BROWSER}  Chrome
${REMOTE_EXECUTION}  ${False}

*** Test Cases ***
Validate quick start in Help page
    NetBak: Validate quick start

Download Netbak PC Agent debug report
    NetBak: Download debug report

Validate Netbak PC Agent tutorial
    NetBak: Validate tutorial tab in help page
    ${webDriver}  ${mouseDriver}=  HDP: Launch browser
    ...  url=${URL2}
    ...  chromedriver_path=${CHROMEDRIVER_PATH}
    HDP: Validate current page title  ${webDriver}  ${NB_TUTORIAL_TITLE}
    HDP: Close browser  ${webDriver}

Validate About Netbak PC Agent
    NetBak: Validate about tab in help page  ${EXP_VERSION}
    ${webDriver}  ${mouseDriver}=  HDP: Launch browser
    ...  url=${URL3}
    ...  chromedriver_path=${CHROMEDRIVER_PATH}
    HDP: Validate current page title  ${webDriver}  ${ABOUT_NB_TITLE}
    HDP: Close browser  ${webDriver}

Validate Job History Plus Minus Buttons with no logs
    NetBak: Validate job history plus minus button with no logs

Validate Job History Plus Minus Buttons with logs
    NetBak: Start backup job
    NetBak: Check backup job status
    NetBak: Stop backup job
    NetBak: Validate job history plus minus button with logs

Validate Job History results filter
    NetBak: Start backup job
    NetBak: Check backup job status
    NetBak: Validate filter result in job history
    NetBak: Stop backup job
