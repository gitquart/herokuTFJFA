"""
Test.py
-Program to read from thesis.tbcourtdecisiontfjfa in datastax
-Read the base64 pdf value and decode here
-This table has text/pdf and image/pdf, so it's needed to know how are they shown decoded
"""

import json
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement
import os

pathToHere=os.getcwd()

cloud_config= {
        'secure_connect_bundle': pathToHere+'\\secure-connect-dbquart.zip'
    }
              
def cassandraBDProcess(year):
     
    record_added=False

    #Connect to Cassandra
    objCC=CassandraConnection()
    auth_provider = PlainTextAuthProvider(objCC.cc_user,objCC.cc_pwd)
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    session = cluster.connect()
    session.default_timeout=70
    row=''
    #Check wheter or not the record exists, check by numberFile and date
    #Date in cassandra 2020-09-10T00:00:00.000+0000
    querySt="select lspdfcontent from thesis.tbcourtdecisiontfjfa where year="+str(value)+"  ALLOW FILTERING"
                
    future = session.execute_async(querySt)
    row=future.result()
        
    if row: 
        
        cluster.shutdown()



class CassandraConnection():
    cc_user='quartadmin'
    cc_keyspace='thesis'
    cc_pwd='P@ssw0rd33'        