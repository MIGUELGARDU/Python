import cv2
import json
import requests

def decode_face_id(res):
    if res['id'] is None and res['sim'] is None:
        return None, None, int(res['age']), res['gender'], res['emotion']
    else:
        return res['id'], round(float(res['sim']), 2), int(res['age']), res['gender'], res['emotion']

def get_face_id(img):
    addr = 'http://172.19.0.7:1234'
    url = addr + '/api/id'
    content_type = 'image/jpeg'
    headers = {'content-type': content_type}
    try:
        _, img_encoded = cv2.imencode('.jpg', img)
    except:
        return None
    response = requests.post(url, data=img_encoded.tostring(), headers=headers)
    return decode_face_id(json.loads(response.text))

def get_face_id_euclidean(img):
    addr = 'http://172.19.0.7:1234'
    url = addr + '/api/id_euclidean'
    content_type = 'image/jpeg'
    headers = {'content-type': content_type}
    try:
        _, img_encoded = cv2.imencode('.jpg', img)
    except:
        return None
    response = requests.post(url, data=img_encoded.tostring(), headers=headers)
    return decode_face_id(json.loads(response.text))
