#!/usr/bin/env python 
# -*- coding: utf-8 -*-

import httplib, urllib, base64, cv2


headers = {
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': '{subscription key}',
}

params = urllib.urlencode({
	'returnFaceId': 'true',
	'returnFaceLandmarks':'true',
	'returnFaceAttributes':'age'
	})

#params = urllib.urlencode({})

imagen = cv2.imread('/home/dell/Documentos/proyectos/General_hilos/Microsoft_api/Rostros/8197.jpg')
imagen = cv2.imencode('.jpg',imagen)[1]
#b64 = base64.standard_b64encode(imagen)

#print b64

try:
	conn = httplib.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
	conn.request("POST", "/face/v1.0/detect?%s" % params, imagen, headers)
	response = conn.getresponse()
	#print dir(conn)
	data = response.read()
	print(data)
	conn.close()

except Exception as e:
	print(e)