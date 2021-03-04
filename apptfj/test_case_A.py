"""
Test_case_A.py

Tests for TFJFA

-Program to read from thesis.tbcourtdecisiontfjfa in datastax
-Read the base64 pdf value and decode here
-This table has text/pdf and image/pdf, so it's needed to know how are they shown decoded

Results:
1) If I try to read a pdf with images with .decode('utf-8'), fails
1) If I try to read a pdf with images with NO .decode('utf-8'), works

Conlusion: read pdf with text or image with NO .decode('utf-8'), works

Test for CJF

Results:
1) If I try to read a pdf with text with .decode('utf-8'), works
1) If I try to read a pdf with text with NO .decode('utf-8'), works

Conlusion: read pdf with text or image with NO .decode('utf-8'), works
"""

import json
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement
import os
import utils as tool
import base64

pathToHere=os.getcwd()

def main():
    objCC=CassandraConnection()
    cloud_config= {
        'secure_connect_bundle': pathToHere+'\\secure-connect-dbquart.zip'
    }
    #Connect to Cassandra
    auth_provider = PlainTextAuthProvider(objCC.cc_user,objCC.cc_pwd)
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    session = cluster.connect()
    session.default_timeout=70
    row=''
    #Check wheter or not the record exists, check by numberFile and date
    #Date in cassandra 2020-09-10T00:00:00.000+0000
    op='tfjfa'
    querySt=''
    if(op=='tfjfa'):
        querySt="select lspdfcontent from thesis.tbcourtdecisiontfjfa where year=2020 ALLOW FILTERING"
    else:
        querySt="select lspdfcontent from thesis.tbcourtdecisioncjf where year=2019 ALLOW FILTERING"

    future = session.execute_async(querySt)
    resultSet=future.result()
        

    if resultSet:
        for row in resultSet:
            for bContent in row[0]:
                res=tool.TextOrImageFromBase64(bContent)
                print(res)
                
        
    cluster.shutdown()



class CassandraConnection():
    cc_user='quartadmin'
    cc_keyspace='thesis'
    cc_pwd='P@ssw0rd33' 

if __name__ == "__main__":
    main()



              



