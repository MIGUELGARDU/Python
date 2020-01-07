#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Thread
from collections import defaultdict
import cv2, numpy as np, json

class contador(Thread):
	def __init__(self, self_padre, token, nombre_equipo, acceso, url, puntos, frame):
		Thread.__init__(self)
		self.setName("Contador")
		self.padre = self_padre
		self.token = token
		self.nombre_equipo = nombre_equipo
		self.acceso = acceso
		self.url = url
		self.frame = frame
		self.pxyList = []
		coorList = []
		puntos = puntos
		for i in range(len(puntos)):
			coorList.append((puntos[i][0], puntos[i][1]))
		self.pxyList = coorList
		coorList.append((640, 480))
		coorList.append((0, 480))
		self.inOutContour = np.array(coorList)
		self.running = True
		self.fgbg = cv2.createBackgroundSubtractorMOG2(history=1500, varThreshold=100, detectShadows=False) #750?
		self.blobList = []
		self.deadBlobs = []
		self.countOut = 0
		self.countIn = 0
		self.halfHourCounted = False
		self.show = True
		# PROPORCIONES
		self.wMin = 20
		self.wMax = 200
		self.hMin = 30
		self.hMax = 300
		# CAMBIO MÁXIMO
		self.blobAbsentFramesMax = 22
		self.blobXMax = 50  #50
		self.blobYMax = 50  #50
		self.blobWMax = 100 #100
		self.blobHMax = 100 #100
		self.tempIm = None
		self.ejecutandose = False
		self.ret = False
	def run(self):
		while self.running:
			try: 
				self.ret, imagen = self.frame.get_image()
				if self.ret:
					frame = cv2.resize(imagen, (640, 480))
					sendFrame = frame.copy()
					self.framePrep(frame)
					self.tempIm = self.blobCount(frame)
					self.ejecutandose = True
			except Exception as e:
				error = "%s\t%s"%(self.name, e)
				self.ejecutandose = False
				self.padre.alert_error(error)

	def get_estado(self):
		return "%s \t %s"%(self.name,self.ejecutandose)

	def stop(self):
		self.running = False
	def framePrep(self, im):
		gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
		gray = cv2.medianBlur(gray, 5)
		gray = cv2.bilateralFilter(gray, 5, 100, 100)
		fgmask = self.fgbg.apply(gray)
		contornosimg = fgmask.copy()
		self.prepIm = contornosimg
	def calcInOut(self, fS, lS, id):
		fSOut = self.isOutPoly(self.inOutContour, fS[0], fS[1])
		lSOut = self.isOutPoly(self.inOutContour, lS[0], lS[1])
		#print "\nID: %6d\tfSOut: %r\tlSOut: %r" %(id, fSOut, lSOut)
		if not fSOut == lSOut:
			#counted
			if lSOut:
				out = True
				#print "Counted out"
			else:
				out = False
				#print "Counted in"
			cnt = True
		else:
			#not counted
			out = None
			#print "Not counted"
			cnt = False
		return (cnt, out)
	def isOutPoly(self, cnt, px, py):
		loc = cv2.pointPolygonTest(cnt, (px, py), False)
		if loc < 0:
			return True
		else:
			return False
	def get_date(self):
		entradas = self.countIn
		salidas = self.countOut
		total = entradas+salidas
		self.countIn = 0
		self.countOut = 0
		return (entradas, salidas, total)
	def get_image(self):
		return(self.ret,self.tempIm)
	def blobCount(self, vframe):
		# ACTUALIZACION DE ARCHIVO
		im = self.prepIm
		#BLOB ABSENT FRAMES & ID
		for blob in self.blobList[:]:
			if blob['absentFrames'] >= self.blobAbsentFramesMax:
				lastSeen = (blob['X']+blob['W']/2, blob['Y']+blob['H']/2)
				blob['lastSeen'] = lastSeen
				self.deadBlobs.append(blob)
				self.blobList.remove(blob)
			else:
				blob['absentFrames'] += 1
				blob['disp'] = False
		# IN/OUT COMPUTATION
		for blob in self.deadBlobs[:]:
			if blob['counted'] == False:
				if blob['age'] > self.blobAbsentFramesMax:
					countBlob, blobOut = self.calcInOut(blob['firstSeen'], blob['lastSeen'], blob['blobID'])
					if countBlob:
						if blobOut:
							self.countOut += 1
						else:
							self.countIn += 1

						blob['counted'] = True
					else:
						self.deadBlobs.remove(blob)
				else:
					self.deadBlobs.remove(blob)
			else:
				self.deadBlobs.remove(blob)
		img, contornos, hierarchy = cv2.findContours(im, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		try: hierarchy = hierarchy[0]
		except: hierarchy = []
		# FIND CONTOURS
		for contour, hier in zip(contornos, hierarchy):
			rectangul = cv2.boundingRect(contour)
			(x,y,w,h) = rectangul

			newBlob = False
			if self.wMin < w < self.wMax and self.hMin < h < self.hMax:
				newBlob = True
				for blob in self.blobList:
					if abs(blob['X'] - x) < self.blobXMax and abs(blob['Y'] - y) < self.blobYMax :
						if abs(blob['W'] - w) < self.blobWMax and abs(blob['H'] - h) < self.blobHMax :
							newBlob = False
							blob['X'] = x
							blob['Y'] = y
							blob['W'] = w
							blob['H'] = h
							blob['disp'] = True
							blob['absentFrames'] -= 1
							blob['age'] += 1
							blob['xywh'] = x+y+w+h

			if newBlob:
				firstSeen = (x + w/2, y + h/2)
				lastSeen = firstSeen
				idList = []
				for b in self.blobList:
					idList.append(b['blobID'])
				newBlobID = 0         # SAFETY
				for id in range(len(idList) + 1):
					if id not in idList:
						newBlobID = id
						break
				newBlobComplete = {'X': x, 'Y': y, 'W': w, 'H': h, \
				'absentFrames': 0, 'blobID': newBlobID, 'disp': True, \
				'firstSeen': firstSeen, 'lastSeen': lastSeen, 'counted': False, \
				'age': 0, 'xywh': x+y+w+h}
				self.blobList.append(newBlobComplete)
		# AVOID REPETITIONS PATCH
		ddic = defaultdict(list)
		for blob in self.blobList:
			ddic[blob['xywh']].append(blob)
		blobby = []
		for rep, repBlobs in ddic.items():
			blobby.append(max(repBlobs, key=lambda x:x['age']))
		self.blobList = blobby
		# VISUALIZE
		for blob in self.blobList:
			if blob['disp']:
				cv2.putText(vframe, "%r" %blob['blobID'], (blob['X'] + blob['W']/2, blob['Y'] + blob['H']/2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
				cv2.rectangle(vframe, (blob['X'],blob['Y']), (blob['X']+blob['W'],blob['Y']+blob['H']), (255, 0, 0), 2)
		for i, xy in enumerate(self.pxyList):
			if i > 0:
				cv2.line(vframe, xy0, xy, (255, 255, 0), 2)
			xy0 = xy
		return vframe