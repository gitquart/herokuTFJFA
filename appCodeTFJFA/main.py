from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium import webdriver
import utils as tool
import chromedriver_autoinstaller
import json
import textract
import time
import os
import requests
import sys
import PyPDF2
import uuid
import cassandraSent as bd
import base64

pathToHere = os.getcwd()
print('Current path:', pathToHere)

options = webdriver.ChromeOptions()

download_dir = '/app/DownloadTFJFA'

profile = {"plugins.plugins_list": [{"enabled": False, "name": "Chrome PDF Viewer"}],  # Disable Chrome's PDF Viewer
           "download.default_directory": download_dir,
           "download.prompt_for_download": False,
           "download.directory_upgrade": True,
           "download.extensions_to_open": "applications/pdf",
           # It will not show PDF directly in chrome
           "plugins.always_open_pdf_externally": True
           }

# Erase every file in download folder at the beginning to avoid mixed files
print('Checking if download folder exists...')
isdir = os.path.isdir(download_dir)
if isdir == False:
    print('Creating download folder...')
    os.mkdir(download_dir)
print('Download directory created...')
for file in os.listdir(download_dir):
    os.remove(download_dir+'/'+file)

print('Download folder empty...')
# Chrome configuration for heroku

chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_experimental_option("prefs", profile)

browser = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
# End of Chrome configuration for heroku

url = "http://sentencias.tfjfa.gob.mx:8080/SICSEJLDOC/faces/content/public/consultasentencia.xhtml"
response = requests.get(url)
status = response.status_code
if status == 200:
    # Read the information of query and page
    lsInfo = []
    # 1.Topic, 2. Page
    lsInfo = bd.getPageAndTopic()
    topic = str(lsInfo[0])
    page = str(lsInfo[1])
    startPage = int(page)
    browser.get(url)
    time.sleep(3)
    # class names for li: rtsLI rtsLast
    btnBuscar = browser.find_elements_by_xpath("//*[@id='formBusqueda:btnBuscar']")[0].click()
    time.sleep(6)
    strSearch = " "
    txtBuscar = browser.find_elements(By.XPATH, "//*[@id='formBusqueda:textToSearch']")[0].send_keys(strSearch)
    btnBuscaTema = browser.find_elements(By.XPATH, '//*[@id="formBusqueda:btnBuscar"]')[0].click()
    # WAit X secs until query is loaded.
    time.sleep(10)
    #Mechanism to change to current page
    if startPage>1:
        for x in range(1,startPage):
            btnNext=browser.find_elements_by_xpath("//*[@id='dtRresul_paginator_top']/span[4]")[0].click()
            time.sleep(5)
    print('Start reading the page...')
    # Control the page
    # Page identention
    while (startPage <= 143):
        countRow = 0
        for row in range(1, 8):
            tool.processRows(browser, row, strSearch)
            countRow = countRow+1

        # Page control
        print('Count of Rows:', str(countRow))
        # Update the info in file
        print('Page already done:...', str(startPage))
        print('------------------------END--------------------------------------------')
        currentPage=int(browser.find_elements_by_css_selector('#dtRresul_paginator_top > span.ui-paginator-pages > span.ui-paginator-page.ui-state-default.ui-corner-all.ui-state-active')[0].text) 
        bd.updatePage(currentPage+1)
        startPage=currentPage+1
        #Change the page with next
        btnNext=browser.find_elements_by_xpath("//*[@id='dtRresul_paginator_top']/span[4]")[0].click()
        time.sleep(5) 


browser.quit()
