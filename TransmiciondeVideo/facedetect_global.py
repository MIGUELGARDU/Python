#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2, numpy as np, time, sys, base64, requests, json
from threading import Thread
from datetime import datetime, date, time, timedelta
from time import strftime
import lib_face

class faceident(Thread):
	def __init__(self, self_padre, token, nombre_equipo, acceso, url_server, url_face, tiempo_espera, tiempo_actualiza, frame, min_det, med_det, max_det):
		Thread.__init__(self)
		self.setName("Reconocimiento")
		self.padre = self_padre
		self.token = token
		self.nombre_equipo = nombre_equipo
		self.acceso = acceso
		self.url_server = url_server+"/registro-alerta"
		self.url_face = url_face
		self.headers = {"content-type":"image/jpeg"}
		self.tiempo_espera = tiempo_espera
		self.tiempo_actualiza = tiempo_actualiza
		self.frame = frame
		self.min_det = min_det
		self.med_det = med_det
		self.max_det = max_det
		self.face_detector = lib_face.FaceDetectorDlib()
		self.funciona = True
		self.ret = False
		self.ejecutandose = False
		self.estadisticos = {}
		self.error = "Declarado pero no iniciado"



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



	def detect(self,imagen):
		self.historico["envio"] = datetime.now() + timedelta(seconds=int(self.tiempo_actualiza))

		boxes = self.face_detector.detect(imagen)
		fecha_captura = strftime("%Y/%m/%d")
		hora_captura = strftime("%H:%M:%S")
		for i, box in enumerate(boxes):
			crop = lib_face.get_aligned_face(imagen, box)
			_, img_encoded = cv2.imencode('.jpg', crop)
			b64= base64.standard_b64encode(img_encoded)
			resp = requests.post(self.url_face,data=b64, headers=self.headers,timeout=10)
			#print(resp.text)
			ident  = json.loads(resp.text)
			id_persona = ident["idgf"]
			if id_persona:
				if not id_persona in self.historico:
					similitud = ident["sim"]
					if similitud > self.min_det:
						nivel = 1
						if similitud > self.med_det:
							nivel = 2
						if similitud > self.max_det:
							nivel = 3
						self.historico[id_persona] = datetime.now() + timedelta(seconds=int(self.tiempo_espera))
						im = imagen.copy()
						ima = cv2.rectangle(im, box[0], box[1], (0, 255, 0), 1)
						##ima = cv2.resize(ima,(200,300))
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
						"genero": ident["gender"],
						"edad": int(ident["age"]),
						"emocion": ident["emotion"]
						}
						resp = requests.post(self.url_server,datos)
						##print self.url_server, datos, resp.text
						file = open("error.txt","wb")
						file.write(str(resp).encode("utf-8"))
						file.close()
			##else:


			##print("Identificado en %s :\n %s \n"%(self.acceso, json.dumps(ident,indent=4)))

	##def estadist(self, datos):

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
				error = "%s\t%s"%(self.name,e)
				self.ejecutandose = False
				self.padre.alert_error(error)

	def stop(self):
		self.funciona = False

	def get_estado(self):
		return "%s \t %s"%(self.name,self.ejecutandose)