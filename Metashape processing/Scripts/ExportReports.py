import Metashape

doc = Metashape.app.document
chunk = doc.chunk

for chunk in doc.chunks:
    chunk.exportReport(path="C:/Users/easton/Documents/DAFR1S/" + str(chunk.label) + ".pdf",
                       title=str(chunk), page_numbers=True, include_system_info=True)
