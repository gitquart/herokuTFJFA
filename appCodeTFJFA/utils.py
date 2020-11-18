from selenium.webdriver.common.by import By
import cassandraSent as bd
from textwrap import wrap
import PyPDF2
import uuid
import base64
import time
import json
import os
import sys

download_dir = '/app/DownloadTFJFA'

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
    for col in range(1,6):
        if col==2:
            namePDF=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==3:
            dt_date=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==4:
            region=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text
        if col==5:
            court=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0].text                    

        if col==1:
            #This is the xpath of the link : //*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']/a
            #This find_element method works!
            pdfButton=browser.find_elements_by_xpath('//*[@id="dtRresul_data"]/tr['+str(row)+']/td['+str(col)+']')[0]
            pdfButton.click()
            time.sleep(20)
            #The file is downloaded rare, then just renaming it solves the issue
            for file in os.listdir(download_dir):
                os.rename(download_dir+'/'+file,download_dir+'/00000.pdf')

  
    #Build the json by row            
    json_sentencia=devuelveJSON('/app/appCodeTFJFA/json_sentencia.json')
    json_sentencia['id']=str(uuid.uuid4())
    json_sentencia['court_room']=court
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
    json_sentencia['region']=region
    json_sentencia['publication_datetime']=fullTimeStamp
    json_sentencia['strpublicationdatetime']=fullTimeStamp
    #Check if a pdf exists  

    #Insert information to cassandra                     
    lsRes=bd.cassandraBDProcess(json_sentencia) 
    if lsRes[0]:
        print('Sentencia added:',str(namePDF))
    else:
        print('Keep going...sentencia existed:',str(namePDF))              
 
    for file in os.listdir(download_dir):
        pdfDownloaded=True
        processPDF(json_sentencia,lsRes)
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
    f = open(download_dir+'/result.pdf', 'wb')
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

def processPDF(json_sentencia,lsRes):
    lsContent=[]  
    for file in os.listdir(download_dir): 
        strFile=file.split('.')[1]
        if strFile=='PDF' or strFile=='pdf':
            strContent=readPDF(file) 
            print('Start wrapping text...') 
            lsContent=wrap(strContent,1000)  
            json_documento=devuelveJSON('/app/appCodeTFJFA/json_documento.json')
            if lsRes[0]:
                json_documento['idDocumento']=json_sentencia['id']
            else:
                json_documento['idDocumento']=lsRes[1]

            json_documento['documento']=json_sentencia['pdfname']
            json_documento['fuente']='tfjfa'
            totalElements=len(lsContent)
            result=insertPDFChunks(0,0,0,totalElements,lsContent,json_documento,0)
            if result==False:
                print('PDF Ended!')       
           
        
def insertPDFChunks(startPos,contador,secuencia,totalElements,lsContent,json_documento,done):
    if done==0:
        json_documento['lspdfcontent'].clear()
        json_documento['id']=str(uuid.uuid4())
        for i in range(startPos,totalElements):
            if i!=totalElements-1:
                if contador<=20:
                    json_documento['lspdfcontent'].append(lsContent[i])
                    contador=contador+1
                else:
                    currentSeq=secuencia+1
                    json_documento['secuencia']=currentSeq
                    res=bd.insertPDF(json_documento) 
                    if res:
                        print('Chunk of pdf added:',str(i),'from ',str(totalElements),' sequence:',str(currentSeq))  
                    else:
                        print('Chunk of pdf already existed:',str(i),'from ',str(totalElements),' sequence:',str(currentSeq)) 

                    return insertPDFChunks(i,0,currentSeq,totalElements,lsContent,json_documento,0) 
            else:
                json_documento['lspdfcontent'].append(lsContent[i])
                currentSeq=secuencia+1
                json_documento['secuencia']=currentSeq
                res=bd.insertPDF(json_documento) 
                if res:
                    print('Last Chunk of pdf added:',str(i),'from ',str(totalElements),' sequence:',str(currentSeq))
                else:
                    print('Last Chunk of pdf already existed:',str(i),'from ',str(totalElements),' sequence:',str(currentSeq))

                return  insertPDFChunks(i,0,currentSeq,totalElements,lsContent,json_documento,1)
    else:
        return False            

                             
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