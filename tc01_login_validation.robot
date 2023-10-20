*** Settings ***
Documentation  A test suite to validate netback app
...            Created by Sachin
Resource     ../Keywords/Main.robot
Library      Selenium2Library

Test Setup   NetBak: Launch app  ${CHROMEDRIVER_PATH}  ${APP_PATH}
Test Teardown  NetBak: Close app

*** Variables ***
# App Paths
${CHROMEDRIVER_PATH}  C:\\Users\\Dell\\Netback_Agent\\timeback_automation\\chromedriver.exe
${APP_PATH}  C:\\Program Files\\QNAP\\NetBakPCAgent\\App\\NetBak PC Agent.exe

# NAS data
${NAS_IP}      ${None}
${NAS_IP2}     ${None}
${NAS_USER}    admin
${NAS_USER2}   admin
${NAS_PWD}     ${None}
${NAS_PWD2}     ${None}
${NAS_IP_WITH_PORT}      ${NAS_IP}:8000

# HDP data
${BROWSER}  Chrome
${URL}      http://${NAS_IP}:8080/HyperDataProtector/#/
${REMOTE_EXECUTION}  ${False}

# Invalid IPs
@{CHAR_IPS}    10.24.ab.cd  abc.12.14.c  abcdefghijkl
@{FORMAT256_IPS}  256.24.56.152  10.256.56.152  10.56.256.152  10.24.56.256  256.256.256.256
@{FORMAT0_IPS}    0.0.0.0  0.1.0.0  0.0.1.0  0.0.0.1  0.1.0.1  0.1.1.1

# Invalid credentials
@{INVALID_USERNAME}   abcdef  1234abcd  abcd1234xyz
@{INVALID_PASSWORD}   12345  abcdef  qwerasdf  !@#$%%^^

*** Test Cases ***
Clean HDP data
    Clean HDP Environment
    ...  url=${URL}
    ...  chromedriverPath=${CHROMEDRIVER_PATH}
    ...  nasUser=${NAS_USER}
    ...  nasPwd=${NAS_PWD}

Login to netback app
    NetBak: Login app
    ...  nas_ip=${NAS_IP}
    ...  username=${NAS_USER}
    ...  password=${NAS_PWD}

Login to netback app with invalid port
    NetBak: Validate invalid port alert
    ...  nas_ip=${NAS_IP_WITH_PORT}

Validate invalid NAS IPs
    NetBak: Validate invalid NAS IPs
    ...  nas_ips=@{CHAR_IPS}
    NetBak: Validate invalid NAS IPs
    ...  nas_ips=@{FORMAT256_IPS}
    NetBak: Validate invalid NAS IPs
    ...  nas_ips=@{FORMAT0_IPS}

Validate LAN Fields
    NetBak: Validate LAN fields

Validate back button from LAN field
    NetBak: Select NAS IP from LAN and press back
    ...  nas_ip=${NAS_IP}

Login to NAS from LAN
    NetBak: Login app using LAN
    ...  nas_ip=${NAS_IP}
    ...  username=${NAS_USER}
    ...  password=${NAS_PWD}

Validate invalid credentials
    NetBak: Validate invalid usernames
    ...  nas_ip=${NAS_IP}
    ...  invalid_usernames=@{INVALID_USERNAME}
    ...  password=${NAS_PWD}

    NetBak: Validate invalid passwords
    ...  nas_ip=${NAS_IP}
    ...  username=${NAS_USER}
    ...  invalid_passwords=@{INVALID_PASSWORD}

Validate start page string
    NetBak: Validate start string

Validate password eye button
    NetBak: Validate password eye button
    ...  nas_ip=${NAS_IP}
    ...  username=${NAS_USER}
    ...  password=${NAS_PWD}

Validate refresh button in LAN
    NetBak: Validate refresh button in LAN

Validate NAS IP page description strings
    NetBak: Validate NAS IP page description strings

Validate NAS IP page tooltip string
    NetBak: Validate NAS IP page tooltip string

Validate NetBak login with multiple NAS
    NetBak: Validate NB login with multiple NAS
    ...  nas_ip=${NAS_IP}
    ...  username=${NAS_USER}
    ...  password=${NAS_PWD}
    ...  nas_ip2=${NAS_IP2}
    ...  username2=${NAS_USER2}
    ...  password2=${NAS_PWD2}
    ...  chromedriver_path=${CHROMEDRIVER_PATH}
    ...  app_path=${APP_PATH}
