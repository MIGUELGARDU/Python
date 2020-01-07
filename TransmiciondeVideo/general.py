#!/usr/bin/env python 
# -*- coding: utf-8 -*-

import json, sys, time, os, requests as rq, cv2, base64
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from control_camara import controlcamara

class control(QThread):
	def __init__(self, self_padre):
		super(control,self).__init__()
		self.padre = self_padre
		self.hour = time.strftime("%H")
		self.minute = time.strftime("%M")
		self.camaras_online = {}
		self.accesos = None
		self.running = True
		self.enviado = False

	def run(self):
		self.padre.set_hour(self.hour, self.minute)
		ready = self.load_info()
		time.sleep(0.5)
		if ready:
			self.start_services()
			token = self.lista_accesos[0].datos["Tienda_token"]
			direccion = self.lista_accesos[0].datos["URL_servidor"]
			while self.running:
				time.sleep(0.1)
				if self.minute != time.strftime("%M"):
					self.hour = time.strftime("%H")
					self.minute = time.strftime("%M")
					self.emit(SIGNAL('hour'),self.hour,self.minute)
					datos_actuales = {}
					try:
						if int(self.minute) + 1 == 29:
							self.emit(SIGNAL('info'), "Enviando Informacion de grafica")
							estadisticos = {}
							for i in self.lista_accesos:
								if i.datos["Contador"]:
									if i.datos["Facedetect"]:
										estadisticos = i.lista_apps["Reconocimiento"].get_datos()
									entradas, salidas, total = i.lista_apps["Contador"].get_date()
									self.fixRefreshFile(entradas,salidas,self.hour,"00",i,estadisticos)
							self.envia_general(self.hour, "00", token, direccion)
						elif int(self.minute) + 1 == 59:
							self.emit(SIGNAL('info'), "Enviando Informacion de grafica")
							for i in self.lista_accesos:
								if i.datos["Contador"]:
									if i.datos["Facedetect"]:
										estadisticos = i.lista_apps["Reconocimiento"].get_datos()
									entradas, salidas, total = i.lista_apps["Contador"].get_date()
									self.fixRefreshFile(entradas,salidas,self.hour,"30",i,estadisticos)
							self.envia_general(self.hour, "30", token, direccion)
					except Exception as e:
						fecha = time.strftime("%Y/%m/%d")
						hora = time.strftime("%H:%M:%S")
						error = "%s\t%s\t%s\t%s"%(fecha,hora,self.objectName(),str(e))
						self.save_error(error)
					for i in self.lista_accesos:
						if "Mapacalor" in i.lista_apps:
							if int(self.minute) == int(i.lista_apps["Mapacalor"].tiempo_envio):
								try:
									ret, heatimage = i.lista_apps["Mapacalor"].get_image()
									imagen = cv2.imencode('.jpg',heatimage)[1]
									b64 = base64.standard_b64encode(imagen)
									datos = {
									'img_mapa_acceso':b64,
									"tienda_token": i.lista_apps["Mapacalor"].token,
									"nombre_equipo": i.lista_apps["Mapacalor"].nombre_equipo,
									"operacion": i.lista_apps["Mapacalor"].acceso,
									"fecha": time.strftime("%Y-%m-%d"),
									"hora": time.strftime("%H:%M")
									}
									resp = rq.post("%s/subir-mapa-acceso"%i.lista_apps["Mapacalor"].url, datos)
	 								print ("Datos de Mapacalor:\n"+resp.text)
								except Exception as e:
									fecha = time.strftime("%Y/%m/%d")
									hora = time.strftime("%H:%M:%S")
									error = "%s\t%s\t%s\t%s"%(fecha,hora,self.objectName(),str(e))
									self.save_error(error)




	def fixRefreshFile(self, cntUp, cntDo, hr, mn, accssFile,estadisticos):
		todayDir = time.strftime('%Y_%m_%d') + "/"
		oper = accssFile
		accssFile = accssFile.name + ".json"
		try:
	 		if not os.path.exists(todayDir):
	 			os.mkdir(todayDir)
	 		if not os.path.isfile(todayDir + accssFile):
	 			self.genera_blank(todayDir, accssFile)

	 		file = open(todayDir + accssFile, "r")
	 		info = file.read()
	 		file.close()
	 		infoDict = json.loads(info)
	 		hrS = "h%02d" %int(hr)
	 		mnS = "%02d" %int(mn)
	 		direccion = oper.lista_apps["Contador"].url

	 		infoDict[hrS][mnS]['entradas'] = cntUp
	 		infoDict[hrS][mnS]['salidas'] = cntDo
	 		infoDict[hrS][mnS]['total'] = cntUp + cntDo
	 		infoDict[hrS]['totalhora'] = infoDict[hrS]['00']['total'] + infoDict[hrS]['30']['total']
	 		#infoDict[hrS][estadisticos]

	 		dayTotal = 0
		
	 		for hour in range(0, 24):
	 			dayTotal += infoDict["h%02d" %hour]['totalhora']
	 		infoDict['totaldia'] = dayTotal

	 		datos_acceso = {
	 		"tienda_token": oper.lista_apps["Contador"].token,##"kkRNosZPW8YETQNdcCOS",
	 		"nombre_equipo": oper.lista_apps["Contador"].nombre_equipo,##nombre_maquina,
	 		"operacion": oper.lista_apps["Contador"].acceso,
	 		"hora": "%s:%s" % (hr, mn),
	 		"entradas": cntUp,
	 		"salidas": cntDo,
	 		"total": cntUp + cntDo,
	 		"info_camara": ""
	 		}


	 		resp = rq.post(direccion, datos_acceso, timeout=10)
	 		if resp.json()["estado"]:
	 			guardo = rq.post(direccion+"/guardar", datos_acceso)
	 		print ("Datos de grafica:\n"+str(datos_acceso))
	 		file = open(todayDir + accssFile, "wb")
	 		file.write(json.dumps(infoDict, sort_keys=True, indent=4))
	 		file.close()
	 	except Exception as e:
			fecha = time.strftime("%Y/%m/%d")
			hora = time.strftime("%H:%M:%S")
			error = "%s\t%s\t%s\t%s"%(fecha,hora,self.objectName(),str(e))
			self.save_error(error)


	def genera_blank1(self,todayDir, accssFile):
			blank = {}
			for i in range(24):
				blank["h%02d"%i]={}
				blank["h%02d"%i]["00"] = {"entradas":0,"salidas":0,"total":0}
				blank["h%02d"%i]["30"] = {"entradas":0,"salidas":0,"total":0}
				blank["h%02d"%i]["totalhora"] = 0
			blank["id"] = "Direccion mac envido con cron desde nuck"
			blank["info_camara"] = "numer,ip,descripcion..."
			blank["totaldia"] = 0
			blank["ubicacion"] = " "
			file = open(todayDir+accssFile, "wb")
			file.write(json.dumps(blank, sort_keys=True, indent=4))
			file.close()



	def envia_general(self ,hr , mn, Tienda_token, direccion):
		todayDir = time.strftime('%Y_%m_%d') + "/"
		accssFile = "General.json"
		
		if os.path.exists(todayDir):
			if not os.path.isfile(todayDir+accssFile):
				self.genera_blank(todayDir, accssFile)
			documentos = os.listdir(todayDir)
			file = open(todayDir + accssFile, "r")
			info = file.read()
			file.close()
			infogeneral = json.loads(info)
			hrS = "h%02d" %int(hr)
			mnS = "%02d" %int(mn)
			for d in documentos:
				if d != "General.json":
					file = open(todayDir + d, "r")
					info = file.read()
					file.close()
					infoDict = json.loads(info)
					infogeneral[hrS][mnS]['entradas'] += infoDict[hrS][mnS]['entradas']
					infogeneral[hrS][mnS]['salidas'] += infoDict[hrS][mnS]['salidas']
					infogeneral[hrS][mnS]['total'] += infoDict[hrS][mnS]['total']
					infogeneral[hrS]['totalhora'] += infoDict[hrS]['00']['total'] + infoDict[hrS]['30']['total']
					for hour in range(0, 24):
						infogeneral['totaldia'] += infoDict["h%02d" %hour]['totalhora']

			datos_acceso = {
			"tienda_token": Tienda_token,##"kkRNosZPW8YETQNdcCOS",
			"hora": "%s:%s" % (hr, mn),
			"entradas": infogeneral[hrS][mnS]['entradas'],
			"salidas": infogeneral[hrS][mnS]['salidas'],
			"total": infogeneral[hrS][mnS]['total']
			}
			resp = rq.post(direccion, datos_acceso, timeout=10)
			if resp.json()["estado"]:
				guardo = rq.post(direccion+"/guardarglobal", datos_acceso)
			file = open(todayDir + accssFile, "wb")
			file.write(json.dumps(infogeneral, sort_keys=True, indent=4))
			file.close()

	def stop(self):
		for i in self.lista_accesos:
			i.stop()
		self.running = False

	def start_services(self):
		self.lista_accesos = list()
		for i in self.accesos:
			self.lista_accesos.append(controlcamara(self, i))
			self.camaras_online[i["operacion"]] = {}
		for i in self.lista_accesos:
			i.start()

	def set_camaras_info(self, acceso, info):
		self.camaras_online[acceso] = info
		self.emit(SIGNAL('acces'),self.camaras_online.keys())

	def get_camaras_info(self, acceso):
		return self.camaras_online[acceso]


	def load_info(self):
		#try:
		archivo = open("configuracion.json","r")
		datos = json.loads(archivo.read())
		archivo.close()
		datos_generales = ["URL_servidor","URL_video","App_nombre","Tienda_token","Nombreequipo","Ubicacion_tienda","Resolucion","URL_face",
							"Tiempo_Espera","Tiempo_Actualiza","protocolo", "deteccion_minima","deteccion_media","deteccion_maxima"]
		datos_camara = ["IPcamara","Usuario","Contra","NumeroCamara","MarcaCamara","transmicion","Contador","Mapacalor","Facedetect","operacion","info_camara","tiempo_map","puntos"]
		self.accesos = list()
		for i in datos["camaras"]:
			datos_acceso = {}
			for j in datos_generales:
				datos_acceso[j] = datos[j]
			for j in datos_camara:
				datos_acceso[j] = datos["camaras"][i][j]
			self.accesos.append(datos_acceso)
		self.emit(SIGNAL('info'),"Informacion cargada exitosamente")
		return True
		#except Exception as e:
		#	fecha = time.strftime("%Y/%m/%d")
		#	hora = time.strftime("%H:%M:%S")
		#	error = "%s\t%s\t%s\t%s"%(fecha,hora,self.objectName(),str(e))
		#	self.save_error(error)
		#	return False

	def save_error(self,error):
		error = error+"\n"
		file = open("log_error.txt", "a")
		file.write(error)
		file.close
		self.emit(SIGNAL('info'), error)

	def get_info(self, acceso, mensaje):
		for i in self.lista_accesos:
			if i.name == acceso:
				respuesta = i.get_info(mensaje)
				self.emit(SIGNAL('resp'),respuesta)
				break



	def genera_blank(self, todayDir, accssFile):
		blank = {}

		rango_edades = [0, 16, 31, 46, 61]
		emociones = ["neutral", "sad", "happy", "surprise", "angry", "disgust","fear"]
		estadisticos = {}
		estadisticos["male"] = {}
		estadisticos["male"]["edad"] = {}
		estadisticos["male"]["emocion"] = {}
		estadisticos["male"]["total"] = 0
		for i in range(len(rango_edades)):
			estadisticos["male"]["edad"][str(i)] = 0
		for i in emociones:
			estadisticos["male"]["emocion"][i] = 0
		estadisticos["female"] = {}
		estadisticos["female"]["edad"] = {}
		estadisticos["female"]["emocion"] = {}
		estadisticos["female"]["total"] = 0
		for i in range(len(rango_edades)):
			estadisticos["female"]["edad"][str(i)] = 0
		for i in emociones:
			estadisticos["female"]["emocion"][i] = 0

		for i in range(24):
			blank["h%02d"%i] = {}
			blank["h%02d"%i]["00"] = {"entradas":0,"salidas":0,"total":0,"male": estadisticos["male"],"female": estadisticos["female"]}
			blank["h%02d"%i]["30"] = {"entradas":0,"salidas":0,"total":0,"male": estadisticos["male"],"female": estadisticos["female"]}
			blank["h%02d"%i]["totalhora"] = 0
		blank["id"] = ""
		blank["info_camara"] = ""
		blank["totaldia"] = 0
		blank["ubicacion"] = ""
		file = open(todayDir+accssFile, "wb")
		file.write(json.dumps(blank, sort_keys=True, indent=4))
		file.close()


class Window(QWidget):
	def __init__(self):
		QWidget.__init__(self)
		self.contr = control(self)
		self.contr.setObjectName("Control_General")
		QObject.connect(self.contr, SIGNAL("acces"), self.set_box)
		QObject.connect(self.contr, SIGNAL("info"), self.set_info)
		QObject.connect(self.contr, SIGNAL("hour"), self.set_hour)
		QObject.connect(self.contr, SIGNAL("resp"), self.set_response)
		self.UI()
		self.setWindowTitle("General")
		self.show()
		self.contr.start()

	def UI(self):
		layout = QGridLayout()

		self.hour = QLabel("00:00")
		
		self.access = QComboBox()
		self.access.currentIndexChanged.connect(lambda: self.clickbutton(self.access))
		
		self.info = QPlainTextEdit()
		self.info.setEnabled(False)

		self.command = QLineEdit()
		self.command.setEnabled(False)

		self.btn_Enter = QPushButton("Enter")
		self.btn_Enter.clicked.connect(lambda: self.clickbutton(self.btn_Enter))
		self.btn_Enter.setStyleSheet("color: white;""background-color: red;""selection-color: black;""selection-background-color: white;");
		self.btn_Enter.setEnabled(False)

		self.response = QPlainTextEdit()
		self.response.setEnabled(False)

		self.btn_close = QPushButton("Cerrar")
		self.btn_close.clicked.connect(lambda: self.clickbutton(self.btn_close))  
		self.btn_close.setStyleSheet("color: white;""background-color: red;""selection-color: black;""selection-background-color: white;");

		layout.addWidget(self.hour, 0, 3)
		layout.addWidget(self.access, 1, 1, 1, 3)
		layout.addWidget(QLabel("Informacion"), 2, 1)
		layout.addWidget(self.info, 3, 1, 1, 3)
		layout.addWidget(QLabel("Comando"), 4, 1)
		layout.addWidget(self.command, 4, 2)
		layout.addWidget(self.btn_Enter, 4, 3)
		layout.addWidget(self.response, 5, 1, 1, 3)
		layout.addWidget(self.btn_close, 6, 3)
		self.setLayout(layout)

	def set_box(self,accessos):
		self.access.clear()
		self.access.addItems(sorted(accessos))
		self.command.setEnabled(True)
		self.btn_Enter.setEnabled(True)

	def closeEvent(self, event):
		self.close()
		self.contr.stop()
		sys.exit()

	def set_hour(self, hour, minute):
		self.hour.setText("%s:%s"%(hour, minute))

	def set_info(self, texto):
		self.info.setPlainText("")
		self.info.setPlainText(texto)

	def set_response(self, texto):
		self.command.setText("")
		self.response.setPlainText("")
		self.response.setPlainText(texto)

	def clickbutton(self, bot):
		if bot == self.btn_Enter:
			self.contr.get_info(str(self.access.currentText()),str(self.command.text()))

		if bot == self.btn_close:
			self.close()
			self.contr.stop()
			sys.exit()

		if bot == self.access: 
			if str(self.access.currentText()) != "":
				self.set_response("")
				info = self.contr.get_camaras_info(str(self.access.currentText()))
				texto = ""
				for i in info:
					texto += "%s\t%s\n"%(i, info[i])
				self.set_info(texto)




def main():
	app = QApplication(sys.argv)
	window = Window()
	sys.exit(app.exec_())


if __name__ == '__main__':
	main()