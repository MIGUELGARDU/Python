import cognitive_face as CF, json, os, time

file = open("Subs_date.json", "rb")
datos = json.loads(file.read())
file.close()


ejecutar = True
Id_group = datos["Id_grupo_faces"]
key = datos["Key_Subscription"][0]
point = datos["Endpoint"]
carpeta_enrolamiento = datos["Carpeta_enrola"]


def enrolar():
	for person in os.listdir(carpeta_enrolamiento):
		res = None
		path = os.path.join(carpeta_enrolamiento, person)
		person = person.split(".")[0]
		if person in datos["Enrolados"]:
			try:
				datos["Enrolados"][person] = CF.large_person_group_person.get(Id_group, datos["Enrolados"][person]['personId'])
				res = CF.large_person_group_person_face.add(path,Id_group,datos["Enrolados"][person]['personId'])
				print ("persona ya creada %s"%datos["Enrolados"][person]['personId'])
			except CF.CognitiveFaceException as exp:
				if exp.code == 'PersonNotFound':
					print("creando %s"%exp.code)
					datos["Enrolados"][person] = CF.large_person_group_person.create(Id_group, person)
					res = CF.large_person_group_person_face.add(path,Id_group,datos["Enrolados"][person]['personId'])
				else:
					print ("Error ", exp.code)
		else:
			datos["Enrolados"][person] = CF.large_person_group_person.create(Id_group, person)
			print("creando Persona no hay %s"%person)
			res = CF.large_person_group_person_face.add(path,Id_group,datos["Enrolados"][person]['personId'])
		res = datos["Enrolados"][person]
		file = open("Subs_date.json", "wb")
		file.write(json.dumps(datos, sort_keys=True, indent=4))
		file.close()
		print res['personId']
		time.sleep(5)



try:
	CF.Key.set(key)
	CF.BaseUrl.set(point)
	CF.large_person_group.get(Id_group)
except CF.CognitiveFaceException as exp:
	if exp.code == 'LargePersonGroupNotFound':
		print "creando grupo"
		CF.large_person_group.create(Id_group)
	else:
		print "Error ",exp.code
		ejecutar = False
while ejecutar:
	opcion = int(input("Ingrese Comando para continuar:"))
	if opcion is 1:
		enrolar()
	elif opcion is 2:
		CF.large_person_group.get(Id_group)
	elif opcion is 3:
		res = CF.large_person_group.train(Id_group)
	elif opcion is 4:
		ejecutar = False

	else:
		print ("Comando incorrecto")
#print CF.large_person_group.list()