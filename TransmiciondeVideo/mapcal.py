#!/usr/bin/env python
# -*- coding: utf-8 -*-1

from threading import Thread
import cv2, numpy as np

class mapcalor(Thread):
	def __init__(self, self_padre, token, nombre_equipo, acceso, url, tiempo_envio, frame):
		Thread.__init__(self)
		self.setName("Mapacalor")
		self.padre = self_padre
		self.token = token
		self.nombre_equipo = nombre_equipo
		self.acceso = acceso
		self.url = url
		self.tiempo_envio = tiempo_envio
		self.funciona = True
		self.genRes = (640, 480)
		self.fgbg = cv2.createBackgroundSubtractorMOG2(history = 1500, varThreshold = 100, detectShadows = False)
		self.accum = np.zeros((self.genRes[1], self.genRes[0]), np.float32)
		self.cleanBool = True
		self.heat = None
		self.frame = frame
		self.ejecutandose = False
		self.ret = False
	def run(self):
		while self.funciona:
			try:
				self.ret, imagen = self.frame.get_image()
				if self.ret:
					frame = cv2.resize(imagen, self.genRes)
					gray = cv2.medianBlur( frame, 5)
					fgmask = self.fgbg.apply(gray)
					acmx = self.accum.max()
					if acmx >= np.finfo(np.float32).max or self.cleanBool == True:
						self.accum = np.zeros((self.genRes[1], self.genRes[0]), np.float32)
						self.cleanBool = False
					self.accum += fgmask
					acmx += 1
					normNew = np.uint8((self.accum/acmx)*255.0)
					acc_jet = cv2.applyColorMap(normNew, cv2.COLORMAP_JET)
					acc_hot = cv2.applyColorMap(normNew, cv2.COLORMAP_HOT)
					hot_gray = cv2.cvtColor(acc_hot, cv2.COLOR_BGR2GRAY)
					ret, mask_hot = cv2.threshold(acc_hot, 13, 255, cv2.THRESH_TOZERO)
					ret, mask_bin = cv2.threshold(hot_gray, 13, 255, cv2.THRESH_BINARY)
					mask_1C = cv2.cvtColor(mask_hot, cv2.COLOR_BGR2GRAY)
					sub = cv2.subtract(frame, np.stack((mask_1C,)*3, -1))
					compo_2 = cv2.bitwise_and(acc_jet, acc_jet, mask = mask_bin)
					compo = cv2.add(sub, compo_2)
					self.heat = compo.copy()
					sd = np.std(self.accum)
					mn = np.mean(self.accum)
					amp = 10
					self.accum[np.where(self.accum > mn + amp*sd)] = mn + amp*sd
					self.ejecutandose = True
			except Exception as e:
				error = "%s\t%s"%(self.name, e)
				self.ejecutandose = False
				self.padre.alert_error(error)

	def get_estado(self):
		return "%s \t %s"%(self.name,self.ejecutandose)

	def get_image(self):
		return (self.ret,self.heat)

	def stop(self):
		self.funciona = False

	def limpia_image(self):
		self.cleanBool = True