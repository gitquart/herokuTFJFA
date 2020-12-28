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
from InternalControl import cInternalControl

objControl=cInternalControl()
idControl=objControl.idControl
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
    querySt="select query,page,fechaactual,fechafin from test.cjf_control where id_control="+str(idControl)+"  ALLOW FILTERING"
    resultSet=bd.getQuery(querySt)   
    if resultSet: 
        for row in resultSet:
            lsInfo.append(str(row[0]))
            lsInfo.append(str(row[1]))
            lsInfo.append(str(row[2]))
            lsInfo.append(str(row[3]))
            print('-----Cassandra values-----')
            print('Query:',str(lsInfo[0]))
            print('Start page:',str(lsInfo[1]))
            print('Fecha actual:',str(lsInfo[2]))
            print('Fecha fin:',str(lsInfo[3]))

    topic=str(lsInfo[0])
    page=str(lsInfo[1])
    strdates=str(lsInfo[2])
    strFechaFin=str(lsInfo[3])
    #Check if the limit is reached
    if strdates==strFechaFin:
        print('The code has reached the limit of dates, bye bye...')
        os.sys.exit(0)

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
    toggleAdvancedBtn=tool.devuelveElemento('//*[@id="formBusqueda:inSwOpcAdv"]/div[3]',browser)
    toggleAdvancedBtn.click()
    #strSearch=" "
    #txtBuscar=browser.find_elements(By.XPATH,"//*[@id='formBusqueda:textToSearch']")[0].send_keys(strSearch)
    #Get dates

    lsDates=tool.getDatesForSearch(strdates)
    strdtInit=lsDates[0]
    strdtFin=lsDates[1]
    
    #Initial date (dd/mm/yyyy)
    dtInit=tool.devuelveElemento('//*[@id="formBusqueda:fchIni_input"]',browser)
    dtInit.send_keys(strdtInit)
    #Final date
    dtFinal=tool.devuelveElemento('//*[@id="formBusqueda:fchFin_input"]',browser)
    dtFinal.send_keys(strdtFin)
    btnBuscar=tool.devuelveElemento('//*[@id="formBusqueda:btnBuscar"]',browser)
    btnBuscar.click()
    #WAit X secs until query is loaded.
    time.sleep(10)
    #Mechanism to change to current page
    if startPage>1:
        for x in range(1,startPage):
            btnNext=tool.devuelveElemento("//*[@id='dtRresul_paginator_top']/span[4]",browser)
            res=btnNext.is_enabled()
            if res:
                btnNext.click()
            else:
                print('Click button is not enabled...then query is over, bye...')  
                print('All pages done, bye!...Heroku will turn me on again')
                #strdates = 11/1997 for example
                chunks=strdates.split('/')
                month=int(chunks[0])
                year=int(chunks[1])
                #Case if month is december
                if month==12:
                    year+=1
                    month=1
                else:
                    month+=1    
            
                strMonth=str(month).zfill(2)
                strYear=str(year)
                dateval=strMonth+'/'+strYear
                st="update test.cjf_control set page=1,fechaactual='"+str(dateval)+"' where id_control="+str(idControl)+";"
                bd.executeStatement(st)
                os.sys.exit(0)      
    
    print('Start reading the page...')
    #Control the page
    #Page identention
    tableRows=tool.devuelveListaElementos('//*[@id="dtRresul_data"]/tr',browser)
    countTableRows=len(tableRows)
    #Len 1 may mean it is empty, check the message.
    bNoResults=False
    if countTableRows==1:
        firstRow=tool.devuelveElemento('//*[@id="dtRresul_data"]/tr[1]/td',browser)
        val=firstRow.text
        if val=='No se encontraron resultados.':
            bNoResults=True

    if bNoResults==False:        
        countRow=0
        for row in range(1,countTableRows+1):
            tool.processRows(browser,row)
            countRow+=1

        #Page control
        print('Count of Rows:',str(countRow)) 
        #Update the info in file
        print('Page already done:...',str(startPage)) 
        nPage=startPage+1
        st="update test.cjf_control set page="+str(nPage)+" where  id_control="+str(idControl)+";"  
        bd.executeStatement(st)
        #Change the page with next
        btnNext=tool.devuelveElemento("//*[@id='dtRresul_paginator_top']/span[4]",browser)
        res=btnNext.is_enabled()
        if res==False:
            print('All pages done, bye!...Heroku will turn me on again')
            #strdates = 11/1997 for example
            chunks=strdates.split('/')
            month=int(chunks[0])
            year=int(chunks[1])
            #Case if month is december
            if month==12:
                year+=1
                month=1
            else:
                month+=1    
            
            strMonth=str(month).zfill(2)
            strYear=str(year)
            dateval=strMonth+'/'+strYear
            st="update test.cjf_control set page=1,fechaactual='"+str(dateval)+"' where id_control="+str(idControl)+";"
            bd.executeStatement(st)
            os.sys.exit(0)    
        else:    
            btnNext=tool.devuelveElemento("//*[@id='dtRresul_paginator_top']/span[4]",browser)
            btnNext.click()
            time.sleep(5) 
    else:
        #No results for this date search
        chunks=strdates.split('/')
        month=int(chunks[0])
        year=int(chunks[1])
        #Case if month is december
        if month==12:
            year+=1
            month=1
        else:
            month+=1    
            
        strMonth=str(month).zfill(2)
        strYear=str(year)
        dateval=strMonth+'/'+strYear
        st="update test.cjf_control set page=1,fechaactual='"+str(dateval)+"' where  id_control="+str(idControl)+";"
        bd.executeStatement(st)
        print('------------No results-------------')
        os.sys.exit(0)    
      

browser.quit()
                           