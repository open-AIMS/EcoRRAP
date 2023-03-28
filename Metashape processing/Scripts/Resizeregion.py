import Metashape


doc = Metashape.app.document
for chunk in doc.chunks:
    print("Resizing bounding box...")
    new_size = Metashape.Vector([12, 6, 10]) #size in the coordinate system units
    S = chunk.transform.scale
    crs = chunk.crs

    region = chunk.region
    region.size = new_size / S
    chunk.region = region
