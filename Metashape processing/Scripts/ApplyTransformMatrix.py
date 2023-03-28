import Metashape as ms

doc = ms.app.document
chunk = doc.chunk

path = ms.app.getOpenFileName("Specify path to the transformation matrix")


f = open(path , 'r')


content = f.read()



content = content.replace("\n", " ")

a = content.split(" ")




T = [[float(a[0]), float(a[1]), float(a[2]), float(a[3])],
    [float(a[4]), float(a[5]), float(a[6]), float(a[7])],
    [float(a[8]), float(a[9]), float(a[10]), float(a[11])],
    [float(a[12]), float(a[13]), float(a[14]), float(a[15])]]

m = ms.Matrix(T)



chunk.transform.matrix = m * chunk.transform.matrix
