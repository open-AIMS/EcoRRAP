'''


This script gets loaded as part of processing chain 2, part 2. It performs
the editing of the sparse cloud. It does so in the following way:

Deletes all the points outside of the bounding box.

Performs an initial optimisation of the cameras. 

Sets the following criteria for simultaneous point selection:

Reprojection error : 0.5
Projection accuracy: 3
Reconstruction uncertainty: 10

It first simultaneously selects all the points not meeting these criteria.
It then checks to see whether over half of the sparse cloud is selected,
and if it is, it reduces the selection to half (so we don't lose too many points)

Then optimizes cameras.

Then goes through a cycle of selecting points based on reprojection error,
5 times in a row. It removes the worst 10% of points and then optimises each
time. The loop will stop if EITHER reprojection error reaches less than
0.5 OR the size of the point cloud reaches <30% of the ORIGINAL size.

It is unlikely with our data that we get to 0.5, but in this way the
routine is looking for a target and can be stopped in 2 different ways,
which will improve the estimation of positions of the camera network.

It then performs a final, full optimisation. 



'''


reconst_uncertainty = 10 # ideal is 10
projection_accuracy = 3  # ideal is 3
reprojection_error = 0.5  # ideal is 0.5


min_percentage = 0.3 # Lower threshold of points we want the points to get to during reprojection error improvement

import Metashape as ms
import math
import sys


app = ms.app
docpath = app.document.path
doc = ms.Document()
chunk = ms.app.document.chunk

doc.open(docpath, read_only=False, ignore_lock=True)

chunk = ms.app.document.chunk

# First align photos on high quality:


chunk = doc.chunks[0]



# First remove the points outside the bounding box


R = chunk.region.rot  # Bounding box rotation matrix
C = chunk.region.center  # Bounding box center vector
size = chunk.region.size

chunk.point_cloud.points

for point in chunk.point_cloud.points:

    if point.valid:
        v = point.coord
        v.size = 3
        v_c = v - C
        v_r = R.t() * v_c

        if abs(v_r.x) > abs(size.x / 2.):
            point.valid = False
        elif abs(v_r.y) > abs(size.y / 2.):
            point.valid = False
        elif abs(v_r.z) > abs(size.z / 2.):
            point.valid = False
        else:
            continue


def calc_reprojection(chunk):
    point_cloud = chunk.point_cloud
    points = point_cloud.points
    npoints = len(points)
    projections = chunk.point_cloud.projections
    err_sum = 0
    num = 0
    point_ids = [-1] * len(point_cloud.tracks)
    for point_id in range(0, npoints):
        point_ids[points[point_id].track_id] = point_id

    for camera in chunk.cameras:
        if not camera.transform:
            continue
        for proj in projections[camera]:
            track_id = proj.track_id
            point_id = point_ids[track_id]
            if point_id < 0:
                continue
            point = points[point_id]
            if not point.valid:
                continue
            error = camera.error(point.coord, proj.coord).norm() ** 2
            err_sum += error
            num += 1
    sigma = math.sqrt(err_sum / num)
    return (sigma)

reproj_initial = calc_reprojection(chunk)

points_initial = len(chunk.point_cloud.points)

# filter options
# create reference to filter technique
selection = ms.PointCloud.Filter()
# generate filter options
# options = ms.PointCloud.Filter(.ReprojectionError,
#                                       .ReconstructionUncertainty,
#                                       .ImageCount, # do not use
#                                       .ProjectionAccuracy)


# initialise


# gradual selection settings  - Make this a dynamic value up at the top and update in the SOP


actions = \
    [
        [ms.PointCloud.Filter.ReconstructionUncertainty, reconst_uncertainty],
        [ms.PointCloud.Filter.ProjectionAccuracy, projection_accuracy],
        [ms.PointCloud.Filter.ReprojectionError, reprojection_error]
    ]


# Begin gradual selection

# Optimise cameras once, before we begin
chunk.optimizeCameras(
    fit_f=True,
    fit_cx=True,
    fit_cy=True,
    fit_b1=False,
    fit_b2=False,
    fit_k1=True,
    fit_k2=True,
    fit_k3=True,
    fit_k4=False,
    fit_p1=True,
    fit_p2=True,
    fit_corrections=False,
    adaptive_fitting=False,
    tiepoint_covariance=False
)

for index, filterOption in enumerate(actions):
    print("=========================================================================")
    print("performing filter action " +
          str(index) + ", " + str(filterOption[0]))
    print("=========================================================================")

    # If current action is not reprojection error, run below
    if filterOption[0] is not ms.PointCloud.Filter.ReprojectionError:
        # perform filter selection
        selection.init(
            chunk,
            criterion=filterOption[0]
        )
        # select all points above the passed threshold value
        selection.selectPoints(filterOption[1])
        nselected = len(
            [p for p in chunk.point_cloud.points if p.selected])
        half_points = (len(chunk.point_cloud.points) * 0.5)

        # check if less than half of all points are selected;
        # if more, then re-select half the points only
        if nselected < half_points:
            selection.removePoints(filterOption[1])
        else:
            copy_points = selection.values.copy()
            copy_points.sort()
            t50 = copy_points[int(len(copy_points) * 0.5)]
            selection.selectPoints(t50)
            selection.removePoints(t50)
        # optimise cameras
        chunk.optimizeCameras(
            fit_f=True,
            fit_cx=True,
            fit_cy=True,
            fit_b1=False,
            fit_b2=False,
            fit_k1=True,
            fit_k2=True,
            fit_k3=True,
            fit_k4=False,
            fit_p1=True,
            fit_p2=True,
            fit_corrections=False,
            adaptive_fitting=False,
            tiepoint_covariance=False
        )
    # time for reprojection errors
    # filter by reprojection error (removes 10% of data each time up to 5 times)
    # if threshold is reached then stop the loop and optimise cameras
    else:
        repError = calc_reprojection(chunk)
        # repeat 5 times so that what remains are 100% * 0.9^5 = 59% of the data
        for i in range(5): # Edit this so it runs at least once
            if repError > filterOption[1] and len(chunk.point_cloud.points) > points_initial*min_percentage:
                selection.init(
                    chunk,
                    criterion=ms.PointCloud.Filter.ReprojectionError
                )
                values = selection.values.copy()
                values.sort()  # sort the filter values by reprojection error
                # identify 10% points with highest reprojection error:
                thresh = values[int(len(values) * 0.9)]
                selection.selectPoints(thresh)  # select those points
                # no. of points selected
                nselected = len(
                    [p for p in chunk.point_cloud.points if p.selected])
                chunk.point_cloud.removeSelectedPoints()
                print(nselected,"points removed during reprojection error filtering")
                # Camera optimisation
                chunk.optimizeCameras(
                    fit_f=True,
                    fit_cx=True,
                    fit_cy=True,
                    fit_b1=True,
                    fit_b2=True,
                    fit_k1=True,
                    fit_k2=True,
                    fit_k3=True,
                    fit_k4=False,
                    fit_p1=True,
                    fit_p2=True,
                    fit_corrections=False,
                    adaptive_fitting=False,
                    tiepoint_covariance=False)



# Perform final full optimisation
chunk.optimizeCameras(
    fit_f=True,
    fit_cx=True,
    fit_cy=True,
    fit_b1=True,
    fit_b2=True,
    fit_k1=True,
    fit_k2=True,
    fit_k3=True,
    fit_k4=True,
    fit_p1=True,
    fit_p2=True,
    fit_corrections=True,
    adaptive_fitting=False,
    tiepoint_covariance=True)

points_final = len(chunk.point_cloud.points)



'''
reproj_final = calc_reprojection(chunk)


x = 0
for camera in chunk.cameras:
    x = x + 1

no_cameras = x

match = float(chunk.meta["AlignCameras/duration"])
align = float(chunk.point_cloud.meta["MatchPhotos/duration"])
a = match + align
amins = a/60

alignhrs = amins/60


depthmapstime = float(chunk.model.meta["BuildDepthMaps/duration"])
dmmins = depthmapstime/60
depthmapshours = dmmins/60

area_3d = chunk.model.area()
area_2d = 72

meshtime = float(chunk.model.meta["BuildModel/duration"])
meshmins = (meshtime/60)
meshhrs = meshmins/60

faces = len(chunk.model.faces)

picdensity = no_cameras/area_2d

rugosity = area_3d/area_2d

resolution = 1 / ((faces / area_3d) / 1000000 )

model_stats = ["Number of aligned cameras: " + no_cameras,
               "" + picdensity,
               "Reprojection error initial: " + reproj_initial,
               "Initial size of sparse cloud: " + points_initial,
               "Reprojection error final: " + reproj_final,
               "Final size of sparse cloud: " + points_final,
               "No. faces: " + faces,
               "Model effective resolution: " + resolution,
               "3D sa: " + area_3d,
               "2D sa: " + area_2d,
               "Depth maps time (hrs): " + depthmapshours,
               "Alignment time (hrs): " + alignhrs,
               "Mesh time (hrs): " + meshhrs]

print(str(model_stats))
'''
doc.save()




