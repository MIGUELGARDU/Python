#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time, subprocess
from threading import Thread


class videostream(Thread):
	def __init__(self, self_padre, camara, resolucion, nombreequipo, operacion, app_nombre, url_video):
		Thread.__init__(self)
		self.setName("Transmicion")
		self.padre = self_padre
		self.camara = camara
		self.resolucion = resolucion
		self.nombreequipo = nombreequipo
		self.operacion = operacion
		self.app_nombre = app_nombre
		self.url_video = url_video
		self.continuar = True
		self.ejecutandose = False
		self.error = "declarado pero no iniciado"
		self.p = None

	def run(self):
		while self.continuar:
			try:
				"""self.p = subprocess.Popen(['ffmpeg',
				"-loglevel", "quiet",
				 "-f", "rtsp", 
				 "-i", self.camara, 
				 "-an", 
				 "-f", "flv", 
				 "-vf", "scale=%s" %(self.resolucion), 
				 "-c:v", "libx264", 
				 "-rtmp_playpath", "%s-%s"%(self.nombreequipo, self.operacion), 
				 "-rtmp_app", self.app_nombre, 
				 self.url_video], shell = False)"""
				self.p = subprocess.Popen(['ffmpeg',
					#"-loglevel", "quiet",
					#'-rtsp_transport', 'tcp',
					#'-stimeout', '500000',
					#'-stream_loop', '-1',
					"-i", self.camara,
					'-preset', 'veryfast',
					'-g', '10',
					'-sc_threshold', '0',
					'-vf', "scale=%s"%self.resolucion, 
					'-c:v', 'libx264',
					"-an", 
					"-f", "flv", 
					#"-vf", "scale=%s" %(self.resolucion), 
					"-c:v", "libx264", 
					"-preset", "ultrafast",
					"-tune", "zerolatency",
					"-threads", "0", 
					"-rtmp_playpath", "%s-%s"%(self.nombreequipo, self.operacion), 
					"-rtmp_app", self.app_nombre,
					self.url_video
					], shell = False)

				self.ejecutandose = True
				self.p.wait()
			except Exception as e:
				error = "%s\t%s"%(self.name, e)
				self.ejecutandose = False
				#self.padre.alert_error(error)


	def get_estado(self):
		return "%s \t %s"%(self.name,self.ejecutandose)

	def stop(self):
		self.continuar = False
		if self.p:
			self.p.kill()
