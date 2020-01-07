#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time, random, cv2
from threading import Thread
from camararead import reading_cam
from conta import contador
from videostream import videostream
from facedetect_global import faceident
from mapcal import mapcalor
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class controlcamara(Thread):
	def __init__(self, self_padre, datos):
		Thread.__init__(self)
		self.datos = datos
		self.padre = self_padre
		self.setName(self.datos["operacion"])
		self.ready = self.check_camera()
		self.lista_apps = {}

	def run(self):
		if self.ready:
			try:
				camara_datos={}
				camara_datos["Ubicacion"] = self.datos["info_camara"]
				camara_datos["IPcamara"] = self.datos["IPcamara"]
				camara_datos["NumeroCamara"] = self.datos["NumeroCamara"]
				self.lista_apps["Camara"] = reading_cam(self, self.camara)
				if self.lista_apps["Camara"].funciona:
					for i in self.datos:
						if type(self.datos[i]) is bool:
							if self.datos[i]:
								camara_datos[i] = self.datos[i]
								if i == "transmicion":
									self.lista_apps["Transmicion"] = videostream(   self,
																					self.camara,
																					self.datos["Resolucion"], 
																					self.datos["Nombreequipo"], 
																					self.datos["operacion"], 
																					self.datos["App_nombre"], 
																					self.datos["URL_video"])
								elif i == "Contador":
									self.lista_apps["Contador"] = contador( self,
																			self.datos["Tienda_token"], 
																			self.datos["Nombreequipo"], 
																			self.datos["operacion"], 
																			self.datos["URL_servidor"], 
																			self.datos["puntos"], 
																			self.lista_apps["Camara"])
								elif i == "Mapacalor":
									self.lista_apps["Mapacalor"] = mapcalor( self,
																			self.datos["Tienda_token"], 
																			self.datos["Nombreequipo"], 
																			self.datos["operacion"], 
																			self.datos["URL_servidor"], 
																			self.datos["tiempo_map"], 
																			self.lista_apps["Camara"])
								elif i == "Facedetect":
									self.lista_apps["Reconocimiento"] = faceident(  self,
																			self.datos["Tienda_token"], 
																			self.datos["Nombreequipo"], 
																			self.datos["operacion"], 
																			self.datos["URL_servidor"], 
																			self.datos["URL_face"],  
																			self.datos["Tiempo_Espera"], 
																			self.datos["Tiempo_Actualiza"], 
																			self.lista_apps["Camara"],
																			self.datos["deteccion_minima"],
																			self.datos["deteccion_media"],
																			self.datos["deteccion_maxima"])
					for i in self.lista_apps:
						self.lista_apps[i].start()
				else:
					camara_datos["Error"] = "Error al leer la camara %s"%self.datos["IPcamara"]
				r = random.random()
				r = r/100.0
				time.sleep(r)
				self.padre.set_camaras_info(self.name,camara_datos)
				#while self.ready:
				#	pass
			except Exception as e:
				print "aqui"
				self.alert_error(e)


	def stop(self):
		for i in self.lista_apps:
			self.lista_apps[i].stop()
		self.ready = False

	def get_info(self,commando):
		try:
			if self.lista_apps["Camara"].funciona:
				commando = commando.split("_")
				if commando[0] == "Ver":
					if commando[1] == "Camara" or commando[1] == "Contador" or commando[1] == "Mapacalor":
						Ventana = Secundaria(self.lista_apps[commando[1]]).exec_()
						respuesta = "Se Activo la visualizacion de %s"%commando[1]
					else:
						respuesta = "%s No cuenta con visualizacion"%commando[1]

				elif commando[0] == "Estado":
					if commando[1] == "Global":
						respuesta = ""
						for i in self.lista_apps:
							respuesta += "%s\n"%self.lista_apps[i].get_estado()
					else:
						respuesta = self.lista_apps[commando[1]].get_estado()

				else:
					respuesta = "Comando Incorrecto"
			else:
				respuesta = "Error al leer la camara %s"%self.datos["IPcamara"]
			return "%s Dice: \n%s"%(self.name,respuesta)
		except Exception as e:
			return "%s Dice: \nError, No existe %s"%(self.name,str(e))

	def check_camera(self):
		ready = True
		for i in self.datos["protocolo"]:
			if self.datos["MarcaCamara"] == i:
				self.camara = self.datos["protocolo"][i] % (self.datos["Usuario"], self.datos["Contra"], self.datos["IPcamara"], self.datos["NumeroCamara"])
		return ready

	def alert_error(self,error):
		fecha = time.strftime("%Y/%m/%d")
		hora = time.strftime("%H:%M:%S")
		error = "%s\t%s\t%s\t%s"%(fecha,hora,self.name,error)
		self.padre.save_error(error)

class Secundaria(QDialog):
	def __init__(self, controla):
		QDialog.__init__(self)
		self.controla = controla
		contenedor = QGridLayout()
		self.setLayout(contenedor)
		self.ret = False
		while not self.ret:
			self.ret, self.imagen = self.controla.get_image()
		self.imagen = cv2.resize(self.imagen, (400, 200))
		self.imagen = cv2.cvtColor(self.imagen, cv2.COLOR_BGR2RGB)
		convertToQtFormat = QImage(self.imagen.data, self.imagen.shape[1], self.imagen.shape[0],QImage.Format_RGB888)
		convertToQtFormat = QPixmap.fromImage(convertToQtFormat)
		pixmap = QPixmap(convertToQtFormat)
		self.label = QLabel(self)
		self.label.setPixmap(pixmap)
		contenedor.addWidget(self.label, 1, 1)
		actualizar = QPushButton("Actualizar",None)
		contenedor.addWidget(actualizar, 2, 1)
		self.connect(actualizar, SIGNAL("clicked()"), self.actualiza)

	def actualiza(self):
		self.ret = False
		while not self.ret:
			self.ret, self.imagen = self.controla.get_image()
		self.imagen = cv2.resize(self.imagen, (400, 200))
		self.imagen = cv2.cvtColor(self.imagen, cv2.COLOR_BGR2RGB)
		convertToQtFormat = QImage(self.imagen.data, self.imagen.shape[1], self.imagen.shape[0],QImage.Format_RGB888)
		convertToQtFormat = QPixmap.fromImage(convertToQtFormat)
		pixmap = QPixmap(convertToQtFormat)
		self.label.setPixmap(pixmap)