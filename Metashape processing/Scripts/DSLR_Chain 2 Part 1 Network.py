"""

This script performs high quality alignment over the network, then
resizes the bounding box and duplicates the chunk.

Manual checking of the orientation of the bounding box is needed after this.

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

chunk = doc.chunk

task = Metashape.Tasks.MatchPhotos()
task.downscale = 0 # High quality align
task.generic_preselection = True
task.reference_preselection = True,
task.reset_matches = True
tasks.append(task)
task.keypoint_limit = 0

task = Metashape.Tasks.AlignCameras()
tasks.append(task)


task = Metashape.Tasks.RunScript()
task.path = "//pearl/3d-ltmp/scripts/EcoRRAP/PythonScripts/Resize_Dupe.py"
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

Metashape.app.messageBox("Tasks have been sent to the network. Please reopen this project without saving and it will display the progress of the jobs you have just sent.")

