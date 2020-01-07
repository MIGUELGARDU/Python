from videostream import videostream
vs = videostream("self","http://admin:admin@190.117.52.207:8081/img/video.mjpeg","-2:600","iot-claro","cam-1","globalvideo","rtmp://172.19.0.179")
vs.start()
#vs.stop()