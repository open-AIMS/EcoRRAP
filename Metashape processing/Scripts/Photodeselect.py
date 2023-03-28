import Metashape

doc = Metashape.app.document
chunk = doc.chunk

step = Metashape.app.getInt("Specify the selection step:",2)
index = 1
for camera in chunk.cameras:
      if not (index % step):
            camera.selected = True
      else:
            camera.selected = False
      index += 1