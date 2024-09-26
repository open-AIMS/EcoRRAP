import Metashape


doc = Metashape.app.document
chunk = doc.chunk
x = 0

for camera in chunk.cameras:
	if  camera.enabled and camera.transform:
		x = x + 1
		camera.selected = True
	else:
		camera.selected = False
		
print ('Enabled and aligned images: %d ' % x)


