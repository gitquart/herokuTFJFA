from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert 
import utils as tool
import json
import time
import os
import requests 
import sys
import cassandraSent as bd

tool.initialDownloadDirCheck()
browser=tool.returnChromeSettings()
#Since here both versions (heroku and desktop) are THE SAME
url="http://sentencias.tfjfa.gob.mx:8080/SICSEJLDOC/faces/content/public/consultasentencia.xhtml"
response= requests.get(url)
status= response.status_code
if status==200:  
    #Read the information of query and page 
    lsInfo=[]
    #1.Topic, 2. Page
    lsInfo=bd.getPageAndTopic()
    topic=str(lsInfo[0])
    page=str(lsInfo[1])
    startPage=int(page)
    browser.get(url)
    time.sleep(3)  
    #Select all fields for query in page
    btnField=tool.devuelveElemento('//*[@id="formBusqueda:btnSelectColumn"]/span[1]',browser)
    btnField.click()
    time.sleep(10)
    tool.checkAllFields(browser)
    btnOkFields=tool.devuelveElemento('//*[@id="formCheckBox:btnColumnsDialog"]/span',browser)
    btnOkFields.click()
    time.sleep(6)
    #Advanced search
    #toggleAdvancedBtn=tool.devuelveElemento('//*[@id="formBusqueda:inSwOpcAdv"]/div[3]',browser)
    #toggleAdvancedBtn.click()
    strSearch=" "
    txtBuscar=browser.find_elements(By.XPATH,"//*[@id='formBusqueda:textToSearch']")[0].send_keys(strSearch)
    btnBuscar=tool.devuelveElemento('//*[@id="formBusqueda:btnBuscar"]',browser)
    btnBuscar.click()
    #WAit X secs until query is loaded.
    time.sleep(10)
    #Mechanism to change to current page
    if startPage>1:
        for x in range(1,startPage):
            btnNext=browser.find_elements_by_xpath("//*[@id='dtRresul_paginator_top']/span[4]")[0].click()
    
    print('Start reading the page...')
    #Control the page
    #Page identention
    while (startPage<=143):
        countRow=0
        for row in range(1,8):
            tool.processRows(browser,row,strSearch)
            countRow=countRow+1

        #Page control
        print('Count of Rows:',str(countRow)) 
        #Update the info in file
        print('Page already done:...',str(startPage))  
        currentPage=startPage
        bd.updatePage(currentPage+1)
        startPage=currentPage+1
        #Change the page with next
        btnNext=browser.find_elements_by_xpath("//*[@id='dtRresul_paginator_top']/span[4]")[0].click()
        time.sleep(5) 
    
    if startPage>143:
        print('All pages done, bye!')
        os.sys.exit(0)    
        

browser.quit()
                           