import base64
import json
download_dir='C:\\Users\\1098350515\\Documents\\pruebasPDF'


"""
Experiencias:

Caso PDF texto:
1)Sin aplicar decode('utf-8'): Traté de guardar el contenido en Bytes en un JSON pero manda error , 
byte se puede convertir a JSON (Object of type bytes is not JSON serializable)
2)Sin aplicar decode('utf-8'):Añadir contenido de bytes convertido a string a un JSON, funciona, JSON
lo serializa pero tanto con ensure_ascii en True y False deja esto - b\' -, esto casusa error de inserción en cassandra
3) Aplicando decode('utf-8') , sin convertir a string: Perfecto, sin convertir a 
string se guarda algo así "JBVJF==", sin "b'JBVJF=='

Caso Pdf imagen:
1) Sin aplicar decode ('utf-8'), sin convertir en string: Objero byte no es serializable
2) Sin aplicar decode ('utf-8'), convertir en string: con ensure_ascii en True y False ambos guardan en JSON 'B'==asasa'
lo cual causa error en insertado en cassandra

Conclusiones: 

1) bContent = base64.b64encode(pdf_file.read()).decode('utf-8') en pdf texto e imagen

"""
with open(download_dir+'\\texto.pdf', "rb") as pdf_file:
    bContent = base64.b64encode(pdf_file.read()).decode('utf-8')
    with open('test.json') as json_file:
        json_test = json.load(json_file)

    json_test['pdf']=bContent
    jsonS=json.dumps(json_test)   

    #Caso imagen
    #Eejemplo de bs4='HFDJDSHJDHFSJD'
    #Tutorial : https://base64.guru/developers/python/examples/decode-pdf
    bytes = base64.b64decode(bContent, validate=True)
    # Write the PDF contents to a local file
    f = open(download_dir+'\\result.pdf', 'wb')
    f.write(bytes)
    f.close()
    print('...')

 """
 bContent must be result from:
 bContent = base64.b64encode(pdf_file.read()).decode('utf-8')
 """   

def getPDFfromBase64(bContent):
    #Tutorial : https://base64.guru/developers/python/examples/decode-pdf
    bytes = base64.b64decode(bContent, validate=True)
    # Write the PDF contents to a local file
    f = open(download_dir+'\\result.pdf', 'wb')
    f.write(bytes)
    f.close()

   
    
    