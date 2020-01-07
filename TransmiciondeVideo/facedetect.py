#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
import cv2, numpy as np, time, sys, base64, requests, json
from threading import Thread
from datetime import datetime, date, time, timedelta
from time import strftime

class faceident(Thread):
	def __init__(self, self_padre, token, nombre_equipo, acceso, url_server, url_goface,
	 key_goface, tiempo_espera, tiempo_actualiza, frame, min_det, med_det, max_det):
		Thread.__init__(self)
		self.setName("Reconocimiento")
		self.padre = self_padre
		self.token = token
		self.nombre_equipo = nombre_equipo
		self.acceso = acceso
		self.url_server = url_server+"/registro-alerta"
		self.url_goface = url_goface
		self.headers = {'Authorization': key_goface}##
		self.tiempo_espera = tiempo_espera
		self.tiempo_actualiza = tiempo_actualiza
		self.frame = frame
		self.min_det = float(min_det)
		self.med_det = float(med_det)
		self.max_det = float(max_det)
		self.funciona = True
		self.ret = False
		self.ejecutandose = False
		self.error = "Declarado pero no iniciado"
		self.face_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_default.xml')
		self.masculino = 0
		self.femenino = 0
		self.rango_edades = [0, 16, 31, 46, 61]
		self.emociones = ["neutral", "sad", "happy", "surprise", "angry", "disgust", "fear"]
		self.estadisticos = {}
		self.estadisticos["male"] = {}
		self.estadisticos["male"]["edad"] = {}
		self.estadisticos["male"]["emocion"] = {}
		self.estadisticos["male"]["total"] = 0
		for i in range(len(self.rango_edades)):
			self.estadisticos["male"]["edad"][str(i)] = 0
		for i in self.emociones:
			self.estadisticos["male"]["emocion"][i] = 0
		self.estadisticos["female"] = {}
		self.estadisticos["female"]["edad"] = {}
		self.estadisticos["female"]["emocion"] = {}
		self.estadisticos["female"]["total"] = 0
		for i in range(len(self.rango_edades)):
			self.estadisticos["female"]["edad"][str(i)] = 0
		for i in self.emociones:
			self.estadisticos["female"]["emocion"][i] = 0


	def buscarostro(self, imagen):
		gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
		faces = self.face_cascade.detectMultiScale(gris, 1.3, 5)
		if len(faces) > 0:
			fecha_captura = strftime("%Y/%m/%d")
			hora_captura = strftime("%H:%M:%S")
			cnt = cv2.imencode('.jpg',imagen)[1]
			b64= base64.standard_b64encode(cnt)
			#print self.url_goface, self.headers, b64
			resp_goface = json.loads(requests.post(self.url_goface, headers=self.headers, data = {'photo64':"data:image/jpeg;base64,"+b64}).text.replace("}{",","))
			## requests.post(self.url_face, headers={"content-type":"image/jpeg"}, data = b64)
			#resp_goface = requests.post(self.url_goface, headers=self.headers, data = {'photo64':"data:image/jpeg;base64,"+b64}).text
			print "Respuesta Go_Face\n", resp_goface
			self.historico["envio"] = datetime.now() + timedelta(seconds=int(self.tiempo_actualiza)) 
			if "results" in resp_goface:
				lista_rostros = resp_goface["results"].keys()
				for i in range(len(lista_rostros)):
					if len(resp_goface["results"][lista_rostros[i]])>0:
						#print lista_rostros[i]
						#print resp_goface["faces"][i]
						id_persona = str(resp_goface["results"][lista_rostros[i]][0]["face"]["person_id"])
						if not id_persona in self.historico:
							self.historico[id_persona] = datetime.now() + timedelta(seconds=int(self.tiempo_espera)) 
							confidence = resp_goface["results"][lista_rostros[i]][0]["confidence"]
							if confidence > self.min_det:
								nivel = 1
								if confidence > self.med_det:
									nivel = 2
								if confidence > self.max_det:
									nivel = 3
								ima = cv2.rectangle(imagen,(resp_goface["faces"][i]["x1"],resp_goface["faces"][i]["y1"]),(resp_goface["faces"][i]["x2"],resp_goface["faces"][i]["y2"]),(0,255,0),2)
								cnt = cv2.imencode('.jpg',ima)[1]
								b64= base64.standard_b64encode(cnt)
								datos = {
								"tienda_token": self.token,
								"fecha_captura" : fecha_captura,
								"hora_captura" : hora_captura,
								"img_captura" : b64,
								"nombre_equipo" : self.nombre_equipo,
								"acceso" : self.acceso,
								"persona_detectada" : id_persona,
								"nivel_confianza" : str(nivel),
								"genero": resp_goface["faces"][i]["gender"],
								"edad": int(resp_goface["faces"][i]["age"]),
								"emocion": resp_goface["faces"][i]["emotions"][0]
								}
								#print datos
								resp = requests.post(self.url_server,datos)
								#print resp.text
								file = open("error.txt","wb")
								file.write(resp.text.encode("utf-8"))
								file.close()
			if "faces" in resp_goface:
				for j in range(len(resp_goface["faces"])):
					for i in range(len(self.rango_edades)):
						if int(resp_goface["faces"][j]["age"]) >= self.rango_edades[i]:
							edad_registrada = i
					self.estadisticos[resp_goface["faces"][j]["gender"]]["edad"][str(edad_registrada)] += 1
					self.estadisticos[resp_goface["faces"][j]["gender"]]["emocion"][resp_goface["faces"][j]["emotions"][0]] += 1
					self.estadisticos[resp_goface["faces"][j]["gender"]]["total"] += 1






				#estadisticos[resp_goface["faces"]["gender"]]


	def run(self):
		self.historico = {}
		while self.funciona:
			try:
				for i in self.historico.keys():
					if self.historico[i] < datetime.now():
						del self.historico[i]
				if not "envio" in self.historico:
					self.ret, imagen = self.frame.get_image()
					if self.ret:
						self.buscarostro(imagen)
				self.ejecutandose = True
			except Exception as e:
				error = "%s\t%s"%(self.name, e)
				self.ejecutandose = False
				self.padre.alert_error(error)


	def get_estado(self):
		return "%s \t %s"%(self.name,self.ejecutandose)

	def get_datos(self):
		datos = self.estadisticos
		self.estadisticos["male"]["total"] = 0
		for i in range(len(self.rango_edades)):
			self.estadisticos["male"]["edad"][str(i)] = 0
		for i in self.emociones:
			self.estadisticos["male"]["emocion"][i] = 0
		self.estadisticos["female"]["total"] = 0
		for i in range(len(self.rango_edades)):
			self.estadisticos["female"]["edad"][str(i)] = 0
		for i in self.emociones:
			self.estadisticos["female"]["emocion"][i] = 0
		return datos

	def stop(self):
		self.funciona = False"""
import cv2, numpy as np, time, sys, base64, requests, json
from threading import Thread
from datetime import datetime, date, time, timedelta
from time import strftime
from FaceAlign import get_aligned_face




class faceident(Thread):
	def __init__(self, self_padre, token, nombre_equipo, acceso, url_server, url_goface,
	 key_goface, tiempo_espera, tiempo_actualiza, frame, min_det, med_det, max_det):
		Thread.__init__(self)
		self.setName("Reconocimiento")
		self.padre = self_padre
		self.token = token
		self.nombre_equipo = nombre_equipo
		self.acceso = acceso
		self.url_server = url_server+"/registro-alerta"
		self.url_goface = url_goface
		self.headers = {'Authorization': key_goface}
		self.tiempo_espera = tiempo_espera
		self.tiempo_actualiza = tiempo_actualiza
		self.frame = frame
		self.min_det = float(min_det)
		self.med_det = float(med_det)
		self.max_det = float(max_det)
		self.funciona = True
		self.ret = False
		self.ejecutandose = False
		self.error = "Declarado pero no iniciado"

	def detect(self, image):
		self.historico["envio"] = datetime.now() + timedelta(seconds=int(self.tiempo_actualiza)) 
		if "results" in resp_goface:
			lista_rostros = resp_goface["results"].keys()
			fecha_captura = strftime("%Y/%m/%d")
			hora_captura = strftime("%H:%M:%S")
			boxes = face_detector.detect(image)
			for i, box in enumerate(boxes):
				id, sim, age, gender, emotion = get_face_id(get_aligned_face(frame, box))
				print('\n{} @ {}\nEdad: {}\nGénero: {}\nEmoción: {}'.format(id, sim, age, gender, emotion))
				##if id and sim > 0.7:
				##	print 
				##	vis = frame.copy()
				#	cv2.rectangle(vis, box[0], box[1], (0, 255, 0), 1)
				"""
				if not id in self.historico:
					self.historico[id_persona] = datetime.now() + timedelta(seconds=int(self.tiempo_espera)) 

					if sim > self.min_det:
						im = imagen.copy()
						nivel = 1
						if sim > self.med_det:
							nivel = 2
						if sim > self.max_det:
							nivel = 3
						cv2.rectangle(im, box[0], box[1], (0, 255, 0), 1)
						cnt = cv2.imencode('.jpg',ima)[1]
						b64= base64.standard_b64encode(cnt)
						datos = {
						"tienda_token": self.token,
						"fecha_captura" : fecha_captura,
						"hora_captura" : hora_captura,
						"img_captura" : b64,
						"nombre_equipo" : self.nombre_equipo,
						"acceso" : self.acceso,
						"persona_detectada" : id_persona,
						"nivel_confianza" : str(nivel),
						"genero": resp_goface["faces"][i]["gender"],
						"edad": int(resp_goface["faces"][i]["age"]),
						"emocion": resp_goface["faces"][i]["emotions"][0]
						}
						#print datos
						resp = requests.post(self.url_server,datos)
						#print resp.text
						file = open("error.txt","wb")
						file.write(resp.text.encode("utf-8"))
						file.close()
						# timestamp =  strftime("%Y_%m_%d %H_%M_%S")
						# timestamp =  strftime("%Y %m %d - %H %M")
						# simstr = "%0.2f" %sim
						# pic = os.path.join(detections_path, "{} - {}.jpg".format(timestamp, id))

						# cv2.imwrite(pic, vis)
						# print('\n{}\n{} @ {}\nEdad: {}\nGénero: {}\nEmoción: {}'.format(timestamp, id, sim, age, gender, emotion))

						"""



	def run(self):
		self.historico = {}
		while self.funciona:
			try:
				for i in self.historico.keys():
					if self.historico[i] < datetime.now():
						del self.historico[i]
				if not "envio" in self.historico:
					self.ret, imagen = self.frame.get_image()
					if self.ret:
						self.detect(imagen)
				self.ejecutandose = True
			except Exception as e:
				error = "%s\t%s"%(self.name, e)
				self.ejecutandose = False
				self.padre.alert_error(error)