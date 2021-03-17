import json
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement
import os
from InternalControl import cInternalControl

objControl=cInternalControl()
idControl=objControl.idControl
hfolder=objControl.hfolder
keyspace='test'
timeOut=objControl.timeout  

def returnCluster():
    #Connect to Cassandra
    objCC=CassandraConnection()
    cloud_config=''
    if objControl.heroku:
        cloud_config= {'secure_connect_bundle': objControl.rutaHeroku+'/secure-connect-dbtest.zip'}
    else:
        cloud_config= {'secure_connect_bundle': objControl.rutaLocal+'secure-connect-dbtest.zip'}


    auth_provider = PlainTextAuthProvider(objCC.cc_user_test,objCC.cc_pwd_test)
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider) 

    return cluster  

def cassandraBDProcess(json_sentencia):
     
    sent_added=False
    cluster=returnCluster()
    session = cluster.connect()
    session.default_timeout=timeOut
    row=''
    pdfname=json_sentencia['pdfname']
    pubdate=json_sentencia['publication_datetime']
    numExp=json_sentencia['num_exp']
    #Check wheter or not the record exists, check by numberFile and date
    #Date in cassandra 2020-09-10T00:00:00.000+0000
    querySt="select id from "+keyspace+".tbcourtdecisiontfjfa where pdfname='"+str(pdfname)+"' and num_exp='"+str(numExp)+"' and publication_datetime='"+str(pubdate)+"'  ALLOW FILTERING"            
    future = session.execute_async(querySt)
    row=future.result()
    lsRes=[]
        
    if row: 
        sent_added=False
        valid=''
        for val in row:
            valid=str(val[0])
        lsRes.append(sent_added) 
        lsRes.append(valid)   
        cluster.shutdown()
    else:        
        #Insert Data as JSON
        jsonS=json.dumps(json_sentencia)           
        insertSt="INSERT INTO "+keyspace+".tbcourtdecisiontfjfa JSON '"+jsonS+"';" 
        future = session.execute_async(insertSt)
        future.result()  
        sent_added=True
        lsRes.append(sent_added)
        cluster.shutdown()     
                    
                         
    return lsRes

def executeStatement(st):

    cluster=returnCluster()
    session = cluster.connect()
    session.default_timeout=timeOut        
    future = session.execute_async(st)
    future.result()
    cluster.shutdown()
                         
    return True

def getQuery(query):    

    cluster=returnCluster()
    session = cluster.connect()
    session.default_timeout=timeOut
    row=''
    future = session.execute_async(query)
    row=future.result()
    cluster.shutdown()
                   
    return row  

def insertPDF(json_doc):
     
    record_added=False

    cluster=returnCluster()
    session = cluster.connect()
    session.default_timeout=timeOut

    iddocumento=str(json_doc['idDocumento'])
    documento=str(json_doc['documento'])
    fuente=str(json_doc['fuente'])
    secuencia=str(json_doc['secuencia'])
    querySt="select id from "+keyspace+".tbDocumento_tfjfa where iddocumento="+iddocumento+" and documento='"+documento+"' and fuente='"+fuente+"' AND secuencia="+secuencia+"  ALLOW FILTERING"          
    future = session.execute_async(querySt)
    row=future.result()

    if row:
        cluster.shutdown()
    else:    
        jsonS=json.dumps(json_doc)           
        insertSt="INSERT INTO "+keyspace+".tbDocumento_tfjfa JSON '"+jsonS+"';" 
        future = session.execute_async(insertSt)
        future.result()  
        record_added=True
        cluster.shutdown()     
                    
                         
    return record_added    



class CassandraConnection():
    cc_user='quartadmin'
    cc_pwd='P@ssw0rd33'
    cc_user_test='test'
    cc_pwd_test='testquart'
        

