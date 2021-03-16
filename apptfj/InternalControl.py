import os

class cInternalControl:
    idControl=2
    timeout=70
    heroku=True
    pdfOn=False
    download_dir='Download_tfja'
    hfolder='apptfj'   
    rutaHeroku='/app/'+hfolder
    rutaLocal=os.getcwd()+'\\'+hfolder+'\\'
    
    