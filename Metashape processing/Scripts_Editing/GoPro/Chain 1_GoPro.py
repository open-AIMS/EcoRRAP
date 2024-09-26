'''
GoPro Chain 1_edit -

@Eoghan @Januar

LOCAL PROCESSING SCRIPT - Works on the ACTIVE CHUNK ONLY


User input is required by this script!

scalebarpath= requires you to point to the right direction of the scale bar text file. The default is where the
file is stored in AIMS folder structure

There will also be a popup box asking you to point the script to the target depth csv file

####################################################

####################################################

####################################################

EVERYTHING that happens will be in a process log file that is deposited in the same folder the project is in.
Certain values are printed throughout and at the end and can be checked if the need arises

Field chain 1 processing. For use in the field. Before running the script, the full photo set just needs to be
imported. Functionality is:

1: Quality checks all of the images and removes the poor quality ones from the project. Threshold is 0.5. If this leads
to under 1000 photos, it will re-enable all of them, then disable ones with a threshold of 0.45, then 0.4, then 0.35.
If <1000, script continues on anyway. The number of photos are logged before and after this, as they get deleted

2: Aligns the photos (lowest quality) to give the markers points in 3D space. Throws error if <80% alignment

3: Detects markers. Removes projections from photos if their error is more than 50 pixels. Also removes markers
altogether if there are less than 5 projections of that marker.

4: Adds scale bars automatically

5: Checks to see how many scale bars there are. If not enough (1 or less), deletes all the markers, detects again
with higher tolerance, adds the scale bars again, then performs the same check.

6: Updates the model transform if there are more than 2 scale bars.

7: Automatically imports X Y Z co-ordinates and error for the triads.

8: Checks the error of the scale bars and breaks the script if it's too high (>1cm).

9: Saves the document




'''



###### KEY VARIABLES #######

# Can we add a 'quality threshold' variable in the key variables section here too?
tolerance_firstattempt = 85 # Marker tolerance
tolerance_secondattempt = 95 # Marker tolerance if too few scalebars on first attempt
min_marker_projections = 10 # Disable markers with less than this number
marker_projection_error_threshold = 150 # Remove marker projections from photos where error is greater than this value

import Metashape
import sys
import os
from os import path
import math


doc = Metashape.app.document
chunk = doc.chunk

current_dir = path.dirname(Metashape.app.document.path)
Metashape.app.settings.log_path = os.path.join(current_dir + "/log.txt")
Metashape.app.settings.log_enable = True

scalebarpath = 'R:/PRJ-ecoRRAP/scripts/PythonScripts/GoPro_Chains/scalebars.txt' # Path to scale bars txt file 

targetpath = Metashape.app.getOpenFileName("Specify path to the depth csv:")


camera = chunk.cameras[0]
if not camera.frames[0].meta["Image/Quality"]: # only runs if the first camera doesn't have an image quality associated
    chunk.analyzePhotos() # estimate the image sharpenss of all the photos in the chunk

    for camera in chunk.cameras:
        if float(camera.meta["Image/Quality"]) < 0.5:
            camera.enabled = False # Disable the photographs with a quality value of less than 0.5

x = 0 # Placeholder counter starting at 0 for the purposes of counting how many photos are disabled
for camera in chunk.cameras:
    if camera.enabled:
        x = x + 1 # Increases the counter by 1 for every enabled photo
if x < 2000:
    x = 0 # resets the counter to 0
    for camera in chunk.cameras:
        camera.enabled = True # This first bit re-enables all cameras if there are less than 2,000 photos selected
        if float(camera.meta["Image/Quality"]) <0.45: # Then goes through the same process again with a lower threshold
            camera.enabled = False
        if camera.enabled:
            x = x + 1


# Now same again just with the lowest threshold. Not doing a counter anymore.

if x < 2000:
    x = 0 # resets the counter to 0
    for camera in chunk.cameras:
        camera.enabled = True # This first bit re-enables all cameras if there are less than 2,000 photos selected
        if float(camera.meta["Image/Quality"]) <0.4: # Then goes through the same process again with a lower threshold
            camera.enabled = False
        if camera.enabled:
            x = x + 1


for camera in chunk.cameras:
    if not camera.enabled:
        chunk.remove(camera) # deletes the disabled photos
    if camera.enabled:
        x = x + 1

if x < 2000:
    for camera in chunk.cameras:
        camera.enabled = True
        if float(camera.meta["Image/Quality"]) <0.35:
            camera.enabled = False

x = 0

for camera in chunk.cameras:
    if not camera.enabled:
        chunk.remove(camera) # deletes the disabled photos
    if camera.enabled:
        x = x + 1



# This next 2 lines will pause the script until you click OKAY

if x <1500:
    Metashape.app.messageBox("WARNING: Number of photos is less than 1500 even with the lowest threshold. Manual "
                         "intervention needed. Script will continue from here anyway.")

if not chunk.point_cloud:
    chunk.matchPhotos(downscale=2, generic_preselection=True, reference_preselection=True,  reset_matches=True)
    chunk.alignCameras()


x = 0
y = 0

for camera in chunk.cameras: # Next few lines before detect markers checks for 80% alignment of photographs. Stops
    # the code if it is less
    x = x + 1
    if camera.transform:
        y = y + 1

if y < (x * 0.8):
    Metashape.app.messageBox("WARNING: Poor alignment of photos. Recommend processing this plot manually")
    

print(str(y/x*100) + "% of photos aligned")

# detect inverted circular 12bit coded markers
if not chunk.markers:
    chunk.detectMarkers(
        target_type=Metashape.TargetType.CircularTarget12bit,
        tolerance=tolerance_firstattempt,
        filter_mask=False,
        inverted=True,
        noparity=False,
        maximum_residual=5,
        minimum_size=0,
        minimum_dist=5
    )

# Remove markers with less than specified projections
for marker in chunk.markers:
    if len(marker.projections) < min_marker_projections:
        chunk.remove(marker)

# Remove marker projections with error greater than thresholdor m in chunk.markers:
    print(marker.label + " has " +
          str(len(marker.projections)) + " projections")

# For each marker in list of markers for active chunk, remove markers from each
# camera with error greater than input value
for marker in chunk.markers:
    # skip marker if it has no position
    if not marker.position:
        print(marker.label + " is not defined in 3D, skipping...")
        continue

    # reference the position of the marker
    position = marker.position

    for camera in marker.projections.keys():
        if not camera.transform:
            continue
        proj = marker.projections[camera].coord
        reproj = camera.project(position)
        error = (proj - reproj).norm()
        if error > marker_projection_error_threshold:
            marker.projections[camera] = None

# Add scale bars from the scalebarpath file
file = open(scalebarpath, "rt")
if not chunk.scalebars:
    markers = {}
    for marker in chunk.markers:
        markers[marker.label] = marker
    eof = False
    line = file.readline()
    while not eof:
        t1, t2, dist = line.split(',')[0], line.split(',')[1], line.split(',')[2]
        if t1 in markers.keys() and t2 in markers.keys():
            s = chunk.addScalebar(markers[t1], markers[t2])
            s.reference.distance = float(dist)
        line = file.readline()
        if not len(line):
            eof = True
            break
file.close()

# Update the model reference if there are enough scale bars
if len(chunk.scalebars) > 2:
    chunk.updateTransform()
else:
    Metashape.app.messageBox("WARNING: There are not enough scale bars. Inadequate detection of markers. The chunk transformation has not been applied. Restarting marker detection with higher tolerance.")
    chunk.remove(chunk.markers)

# Detect markers again with higher tolerance if necessary
if not chunk.markers:
    chunk.detectMarkers(
        target_type=Metashape.TargetType.CircularTarget12bit,
        tolerance=tolerance_secondattempt,
        filter_mask=False,
        inverted=True,
        noparity=False,
        maximum_residual=5,
        minimum_size=0,
        minimum_dist=5
    )
    for marker in chunk.markers:
        if len(marker.projections) < min_marker_projections:
            chunk.remove(marker)

# Add scale bars from the scalebarpath file

    file = open(scalebarpath, "rt")
    if not chunk.scalebars:
        markers = {}
        for marker in chunk.markers:
            markers[marker.label] = marker
        eof = False
        line = file.readline()
        while not eof:
            t1, t2, dist = line.split(',')[0], line.split(',')[1], line.split(',')[2]
            if t1 in markers.keys() and t2 in markers.keys():
                s = chunk.addScalebar(markers[t1], markers[t2])
                s.reference.distance = float(dist)
            line = file.readline()
            if not len(line):
                eof = True
                break
    file.close()

# Update the model reference if there are enough scale bars
if len(chunk.scalebars) > 4:
    chunk.updateTransform()
else:
    Metashape.app.messageBox("WARNING: Couldn't detect enough markers to make scale bars. Needs doing manually.")
    file = open(scalebarpath, "rt")
    if not chunk.scalebars:
        markers = {}
        for marker in chunk.markers:
            markers[marker.label] = marker
        eof = False
        line = file.readline()
        while not eof:
            t1, t2, dist = line.split(',')[0], line.split(',')[1], line.split(',')[2]
            if t1 in markers.keys() and t2 in markers.keys():
                s = chunk.addScalebar(markers[t1], markers[t2])
                s.reference.distance = float(dist)
            line = file.readline()
            if not len(line):
                eof = True
                break
    file.close()

# Update the model reference if there are enough scale bars
if len(chunk.scalebars) > 4:
    chunk.updateTransform()
else:
    Metashape.app.messageBox("WARNING: Couldn't detect enough markers to make scale bars. Needs doing manually.")

# Import depth data on the triads automatically
chunk.importReference(targetpath, delimiter=",", columns="nxyzXYZ", items=Metashape.ReferenceItemsMarkers)

# Remove markers with less than 1 projection
      # if marker has less than 1 projections, remove from chunk
for marker in chunk.markers:
        if len(marker.projections) < 1:
            Metashape.app.messageBox("Check the markers that are in the reference pane now - you've added data for markers that don't exist in the project.")

# This section calculates the error of each scale bar, by comparing the estimated measurement of the scale bar
# with the input distance we have applied. If the error is too big the script will stop



print("Number of markers:" + str(len(chunk.markers)))

for marker in chunk.markers: # Print reprojection error for markers
	if not marker.position:
		print(marker.label + " is not defined in 3D, skipping...")
		continue
	position = marker.position
	proj_error = list()
	proj_sqsum = 0
	for camera in marker.projections.keys():
		if not camera.transform:
			continue #skipping not aligned cameras
		image_name = camera.label
		proj = marker.projections[camera].coord
		reproj = camera.project(marker.position)
		error = reproj - proj
		proj_error.append(error.norm())
		proj_sqsum += error.norm()**2
	if len(proj_error):
		error = math.sqrt(proj_sqsum / len(proj_error))
		print(marker.label + " had " + str(len(marker.projections)) + " projections. The error was " + str(error))
sb_err = []

for scalebar in chunk.scalebars:
    dist_source = scalebar.reference.distance
    if not dist_source:
        continue
    if type(scalebar.point0) == Metashape.Camera:
        if not (scalebar.point0.center and scalebar.point1.center):
            continue
        dist_estimated = (scalebar.point0.center - scalebar.point1.center).norm() * chunk.transform.scale
    else:
        if not (scalebar.point0.position and scalebar.point1.position):
            continue
        dist_estimated = (scalebar.point0.position - scalebar.point1.position).norm() * chunk.transform.scale
    dist_error = dist_estimated - dist_source
    print(str(dist_error))
    sb_err.append(dist_error)

# Check if any scale bar has an error greater than 2cm
if any(item > 0.02 for item in sb_err):
    Metashape.app.messageBox("At least one scalebar has an error greater than 2cm - Manual intervention is needed")
else:
    print('All scalebars meet the error threshold')

marker_list = []

for marker in chunk.markers:
    marker_list.append(int(marker.label[7:]))


count = sum(map(lambda x : x>100, marker_list))

print('Count of Triad targets: ', count)

triad_1 = [102, 103, 104]
triad_2 = [105, 106, 107]
triad_3 = [108, 109, 110]
triad_4 = [111, 112, 113]
triad_5 = [114, 115, 116]
triad_6 = [117, 118, 119]
triad_7 = [120, 121, 112]

if all(value in marker_list for value in triad_1) or all(value in marker_list for value in triad_2) or all(value in marker_list for value in triad_3) or all(value in marker_list for value in triad_4) or all(value in marker_list for value in triad_5) or all(value in marker_list for value in triad_6) or all(value in marker_list for value in triad_7):
    print('At least one triad has been detected')
else:
    Metashape.app.messageBox("Warning - no complete triads have been detected. Please intervene.")


# Save the document
doc.save()
