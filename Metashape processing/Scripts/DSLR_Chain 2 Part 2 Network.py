"""


This is the network-adapted version of Chain 2. It mixes network and non-network processes together in the same
script and has links to other scripts in it because of that. The assume start point is the end of chain 1.


"""

"""

Demo workflow script
> @Eoghan @Januar

This is a demo script to demonstrate how to process models through the network using a combination of known network
processes and scripts.
"""

import Metashape

app = Metashape.app
docpath = app.document.path
doc = Metashape.Document()
chunk = Metashape.app.document.chunk


network_server = 'metashape-qmgr.aims.gov.au'

Metashape.app.settings.network_path = '//pearl/3d-ltmp/'

client = Metashape.NetworkClient()

doc.open(docpath, read_only=False, ignore_lock=True)
# save latest changes
doc.save()

tasks = []  # create task list

chunk = doc.chunks[0]


task = Metashape.Tasks.RunScript()
task.path = "//pearl/3d-ltmp/scripts/EcoRRAP/PythonScripts/SparseCloudEdit.py"
tasks.append(task)

chunk = doc.chunks[0]

task = Metashape.Tasks.BuildDepthMaps()
task.downscale = 4
task.reuse_depth = False
task.max_neighbors = 40
task.max_workgroup_size = 100
tasks.append(task)

task = Metashape.Tasks.BuildModel()
task.surface_type = Metashape.Arbitrary
task.interpolation = Metashape.EnabledInterpolation
task.face_count = Metashape.FaceCount.HighFaceCount
task.source_data = Metashape.DepthMapsData
task.vertex_colors = True
task.vertex_confidence = True,
task.volumetric_masks = False,
task.keep_depth = True,
task.trimming_radius = 10
task.subdivide_task = True
task.workitem_size_cameras = 20
task.max_workgroup_size = 100
tasks.append(task)



# convert task list to network tasks
network_tasks = []
for task in tasks:
    if task.target == Metashape.Tasks.DocumentTarget:
        network_tasks.append(task.toNetworkTask(doc))
    else:
        network_tasks.append(task.toNetworkTask(chunk))

client = Metashape.NetworkClient()
client.connect(app.settings.network_host)  # server ip
batch_id = client.createBatch(docpath, network_tasks)
client.setBatchPaused(batch_id, False)


Metashape.app.messageBox("Tasks have been sent do the network. Please reopen this project without saving and it will display the progress of the jobs you have just sent.")
