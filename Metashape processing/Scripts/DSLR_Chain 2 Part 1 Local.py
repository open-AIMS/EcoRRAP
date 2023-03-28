'''


Processing chain 2 Part 1:

This is a very simple script. No user input is required.

1: Script resets camera alignment then aligns on high quality. Tie point limit is Zero (infinite)

2: Calculates error for all scalebars and stores them in a list that is printed out at the end

3: Resizes bounding box to 12 x 6 x 10m size.

4: Duplicates the chunk to preserve unedited point cloud (failsafe)

5: Saves the document



'''

# Set duplicate to False if you don't want to back up the sparse cloud

############
duplicate = True
############


import Metashape as ms
import math
import sys


doc = ms.app.document
chunks = ms.app.document.chunks
chunk = doc.chunk

# First align photos on high quality:

if not chunk.scalebar:
    ms.app.messageBox("No scalebars. Ensure chain 1 finished properly then try again.")
    sys.exit()

for camera in chunk.cameras:
    camera.transform = None

chunk.matchPhotos(downscale=1, # 1 = high
                  generic_preselection=True, # set tie point limit to 0
                  reference_preselection=True,
                  reset_matches=True,
                  tiepoint_limit=0)

chunk.alignCameras()

chunk.updateTransform()

sb_err = []

for scalebar in chunk.scalebars:
    dist_source = scalebar.reference.distance
    if not dist_source:
        continue  # skipping scalebars without source values
    if type(scalebar.point0) == ms.Camera:
        if not (scalebar.point0.center and scalebar.point1.center):
            continue  # skipping scalebars with undefined ends
        dist_estimated = (scalebar.point0.center - scalebar.point1.center).norm() * chunk.transform.scale
    else:
        if not (scalebar.point0.position and scalebar.point1.position):
            continue  # skipping scalebars with undefined ends
        dist_estimated = (scalebar.point0.position - scalebar.point1.position).norm() * chunk.transform.scale
    dist_error = dist_estimated - dist_source
    sb_err.append(scalebar.label + " error: " + str(dist_error) + "m")

# Then resize the bounding box
new_size = ms.Vector([12, 6, 10]) #size in the coordinate system units
S = chunk.transform.scale
crs = chunk.crs

region = chunk.region
region.size = new_size / S
chunk.region = region

# duplicate chunk to preserve source
if duplicate is True:
    chunk_label = chunk.label  # create reference to source chunk
    chunk.copy()  # now duplicate the source chunk
    chunks = ms.app.document.chunks  # update reference to chunks
    # set reference to the duplicated chunks since we will be working with this chunk:
    dupeChunk = ms.app.document.chunks[len(ms.app.document.chunks)-1]
    if dupeChunk in chunks:
        dupeChunk.label = str(chunk_label) + " -PreCleanUnFiltered"  # rename dupe chunk

### NEED A CHECK HERE FOR BOUNDING BOX PLACEMENT, END SCRIPT< MAKE EVERYTHING ELSE NEW SCRIPT ### 
print(sb_err)

doc.save()






