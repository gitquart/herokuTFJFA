from selenium.webdriver.common.by import By
import cassandraSent as bd
import PyPDF2
import uuid
import base64
import time
import json
import os
import sys
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from textwrap import wrap

#Local
#download_dir='C:\\DownloadsTFJFA'

#Heroku
download_dir='/app/DownloadsTFJFA'


def appendInfoToFile(path,filename,strcontent):
    txtFile=open(path+filename,'a+')
    txtFile.write(strcontent)
    txtFile.close()


"""
processRows:

//*[@id="dtRresul_data"]/tr[1]/td[1]
//*[@id="dtRresul_data"]/tr[1]/td[2]
//*[@id="dtRresul_data"]/tr[1]/td[3]
...
//*[@id="dtRresul_data"]/tr[1]/td[5]
"""

def processRows(browser,row,strSearch):
    pdfDownloaded=False
    for col in range(1,16):
        if col==2:
            numExp=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==3:
            viaTram=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==4:
            tipoJuicio=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==5:
            fechaPres=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==6:
            resolImp=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==7:
            leyQueFunda=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==8:
            sentDeLaSent=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==9:
            subject=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==10:
            sub_subject=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==11:
            region=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==12:
            court=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==13:
            title=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==14:
            namePDF=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==15:
            dt_date=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==1:
            #This is the xpath of the link : //*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']/a
            #This find_element method works!
            time.sleep(5)
            pdfButton=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0]
            pdfButton.click()
            time.sleep(100)
            #The file is downloaded rare, then just renaming it solves the issue
            for file in os.listdir(download_dir):
                pdfDownloaded=True
                os.rename(download_dir+'/'+file,download_dir+'/00000.pdf')

    
       
    #Build the json by row               
    json_sentencia = devuelveJSON('/app/CodeTFJFA/json_sentencia.json')
    #Start of JSON filled
    json_sentencia['id']=str(uuid.uuid4())
    json_sentencia['num_exp']=numExp
    json_sentencia['via_tramit']=viaTram
    json_sentencia['type_judge']=tipoJuicio
    json_sentencia['dt_demandfeature']=fechaPres
    json_sentencia['resolimpugnada']=resolImp
    json_sentencia['ley_base_res_impug']=leyQueFunda
    json_sentencia['sentido_sent']=sentDeLaSent
    json_sentencia['subject']=subject
    json_sentencia['sub_subject']=sub_subject
    json_sentencia['region']=region
    json_sentencia['court_room']=court
    json_sentencia['title']=title
    json_sentencia['pdfname']=namePDF
    #Working with the date, this field will deliver:
    #1.Date field,2. StrField and 3.year
    # timestamp accepted for cassandra: 
    # yyyy-mm-dd  , yyyy-mm-dd HH:mm:ss
    #In web site, the date comes as 27-10-2020 14:38:00
    data=''
    data=dt_date.split(' ')
    dDate=str(data[0]).split('-')
    dDay=dDate[0]
    dMonth=dDate[1]
    dYear=dDate[2]
    dTime=data[1]
    fullTimeStamp=dYear+'-'+dMonth+'-'+dDay+' '+dTime;
    json_sentencia['year']=int(dYear)
    json_sentencia['publication_datetime']=fullTimeStamp
    json_sentencia['strpublicationdatetime']=fullTimeStamp                  
                   
    #Insert information to cassandra
    res=bd.cassandraBDProcess(json_sentencia)
    if res:
        print('Sentencia added:',str(namePDF))         
    else:
        print('Keep going...sentencia existed:',str(namePDF)) 

    #First the metadata of document is inserted, then the PDF, hence the PDF must be validated by chunks
    if pdfDownloaded==True:
        processPDF(json_sentencia)   
        for file in os.listdir(download_dir):
            os.remove(download_dir+'/'+file)     
                    
"""
readPDF is done to read a PDF no matter the content, can be image or UTF-8 text
"""
def readPDF(file):  
    with open(download_dir+'/'+file, "rb") as pdf_file:
        bContent = base64.b64encode(pdf_file.read()).decode('utf-8')
    
    return bContent  
    

"""
This is the method to call when fetching the pdf enconded from cassandra which is a list of text
but that text is really bytes.
"""
def decodeFromBase64toNormalTxt(b64content):
    normarlText=base64.b64decode(b64content).decode('utf-8')
    return normarlText


def getPDFfromBase64(bContent):
    #Tutorial : https://base64.guru/developers/python/examples/decode-pdf
    bytes = base64.b64decode(bContent, validate=True)
    # Write the PDF contents to a local file
    f = open(download_dir+'\\result.pdf', 'wb')
    f.write(bytes)
    f.close()
    return "PDF delivered!"

def TextOrImageFromBase64(bContent):
    #If sData got "EOF" is an image, otherwise is TEXT
    sData=str(bContent)
    if "EOF" in sData:
        res=getPDFfromBase64(bContent) 
    else:
        res=decodeFromBase64toNormalTxt(bContent)

    return res 

def devuelveJSON(jsonFile):
    with open(jsonFile) as json_file:
        jsonObj = json.load(json_file)
    
    return jsonObj 

def processPDF(json_sentencia):
    lsContent=[]  
    for file in os.listdir(download_dir): 
        strFile=file.split('.')[1]
        if strFile=='PDF' or strFile=='pdf':
            strContent=readPDF(file) 
            print('Start wrapping text...') 
            lsContent=wrap(strContent,1000)  
            json_documento=devuelveJSON('json_documento.json')
            json_documento['idDocumento']=json_sentencia['id']
            json_documento['documento']=json_sentencia['pdfname']
            json_documento['fuente']='tfjfa'
            totalElements=len(lsContent)
            insertPDFChunks(0,0,0,totalElements,lsContent,json_documento)       
           
        
def insertPDFChunks(startPos,contador,secuencia,totalElements,lsContent,json_documento):
    json_documento['lspdfcontent'].clear()
    json_documento['id']=str(uuid.uuid4())
    for i in range(startPos,totalElements):
        if contador<=20:
            json_documento['lspdfcontent'].append(lsContent[i])
            contador=contador+1
        else:
            currentSeq=secuencia=secuencia+1
            json_documento['secuencia']=currentSeq
            res=bd.insertPDF(json_documento) 
            if res:
                print('Chunk of pdf added')  
            insertPDFChunks(i,0,currentSeq,totalElements,lsContent,json_documento) 
    print('PDF COMPLETE')         
       
                    

def readPyPDF(file):
    #This procedure produces a b'blabla' string, it has UTF-8
    #PDF files are stored as bytes. Therefore to read or write a PDF file you need to use rb or wb.
    lsContent=[]
    pdfFileObj = open(download_dir+'/'+file, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    pags=pdfReader.numPages
    for x in range(0,pags):
        pageObj = pdfReader.getPage(x)
        #UTF-8 is the right encodeing, I tried ascii and didn't work
        #1. bContent is the actual byte from pdf with utf-8, expected b'bla...'
        bcontent=base64.b64encode(pageObj.extractText().encode('utf-8'))
        lsContent.append(str(bcontent.decode('utf-8')))
                         
    pdfFileObj.close()    
    return lsContent 

def returnChromeSettings():
    chromedriver_autoinstaller.install()
    options = Options()
    profile = {"plugins.plugins_list": [{"enabled": True, "name": "Chrome PDF Viewer"}], # Disable Chrome's PDF Viewer
               "download.default_directory": download_dir , 
               "download.prompt_for_download": False,
               "download.directory_upgrade": True,
               "download.extensions_to_open": "applications/pdf",
               "plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
               }           

    options.add_experimental_option("prefs", profile)
    browser=webdriver.Chrome(options=options)  

    return browser    

def initialDownloadDirCheck():
    print('Checking if download folder exists...')
    isdir = os.path.isdir(download_dir)
    if isdir==False:
        print('Creating download folder...')
        os.mkdir(download_dir)
        print('Download directory created...')
    for file in os.listdir(download_dir):
        os.remove(download_dir+'/'+file)
        print('Download folder empty...')   

def devuelveElemento(xPath, browser):
    cEle=0
    while (cEle==0):
        cEle=len(browser.find_elements_by_xpath(xPath))
        if cEle>0:
            ele=browser.find_elements_by_xpath(xPath)[0]

    return ele  

def checkAllFields(browser):
    for col in range(1,4):
        if col!=2:
            for row in range(1,8):
                if (col==1 and row==6) or (col==1 and row==7) or (col==3 and row==5) or (col==3 and row==7):
                    pass    
                else:
                    ckCol=devuelveElemento('//*[@id="formCheckBox:gridColCheck"]/tbody/tr['+str(row)+']/td['+str(col)+']/div/div[2]/span',browser)
                    ckCol.click()                  


    
                               
                                         