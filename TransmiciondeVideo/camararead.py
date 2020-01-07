import cv2
from threading import Thread

class reading_cam(Thread):
	def __init__(self,self_padre, rtsp_camara):
		Thread.__init__(self)
		cam = rtsp_camara
		self.setName("Camara")
		self.funciona = False
		self.padre = self_padre
		self.cap = cv2.VideoCapture(rtsp_camara)
		self.ejecutandose = False
		if self.cap.isOpened():
			self.funciona = True
		self.frame = None
		self.first = True
		self.ret = False

	def run(self):
		while self.funciona:
			try:
				self.ret, self.frame = self.cap.read()
				height, width, channels = self.frame.shape
				self.ejecutandose = True
				self.first = False
			except Exception as e:
				if self.first or self.ejecutandose:
					self.ret, self.frame = (False, None)
					error = "%s\t%s"%(self.name, e)
					self.ejecutandose = False
					self.padre.alert_error(error)
		self.cap.release()

	def get_image(self):
		return (self.ret, self.frame)

	def get_estado(self):
		return "%s \t %s"%(self.name,self.ejecutandose)

	def stop(self):
		self.funciona = False