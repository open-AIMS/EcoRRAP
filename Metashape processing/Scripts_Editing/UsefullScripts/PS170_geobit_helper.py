import Metashape as PhotoScan
import sys
import math

from PySide2 import QtGui, QtCore, QtWidgets

from threading import Timer

#
# VERSION: 1.0.1
# DATE: 01-November
# AUTHOR: Rubén Martínez / Jose Martínez (GEOBIT S.L.)
# You are free to use this script on an as-is-no-warranty basis
# You are free to modify and adapt it but if you find it useful please let the original authors have a copy
# Finally, if you find this code useful please support us - the https://accupixel.co.uk/shop/ will always appreciate the business. 
# If you are not ready to purchase then please just spread the good word about AccuPixel and Geobit Consulting.
# 18-Aug 2021, Fixed compatibility with Metashape 1.7

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


class GeoBitTransformDialog(QtWidgets.QDialog):

	def __init__(self, parent):

		QtWidgets.QDialog.__init__(self, parent)
		self.setWindowTitle("Transform Helper")

		self.__tabWidget = QtWidgets.QTabWidget()
		self.__mainLayout = QtWidgets.QVBoxLayout()
		self.__mainLayout.addWidget(self.__tabWidget)
		
		# Create tabs
		self.__tab1 = QtWidgets.QWidget()	
		self.__tab2 = QtWidgets.QWidget()
		self.__tab3 = QtWidgets.QWidget()
		self.__tabWidget.resize(300,200)

		# Add tabs
		self.__tabWidget.addTab(self.__tab1,"View")
		self.__tabWidget.addTab(self.__tab2,"Region")
		self.__tabWidget.addTab(self.__tab3,"Object")

		# Config mode
		self.mode = 'xyz' #xyz / bbox / object
		self.modeobject = False

		if (PhotoScan.app.document.chunk is None):
			msgBox = QtWidgets.QMessageBox()
			msgBox.setText("Critical Error!.")
			msgBox.setInformativeText("Failed load chunk. Exists anyone?")
			print("Failed load chunk. Exists anyone?.")
			msgBox.exec_()
			return

		# Populate Tabs
		try:
			self.tab1UI()
			self.tab2UI()
			self.tab3UI()
		except:
			msgBox = QtWidgets.QMessageBox()
			msgBox.setText("Critical Error!.")
			msgBox.setInformativeText("Failed configure Widget. Try again.")
			print("Failed configure Widget. Try again.")
			msgBox.exec_()
			return

		# Create Main Layout
		self.setLayout(self.__mainLayout)

		self.__tabWidget.currentChanged.connect(self.onChange)

		try:
			self.config()
		except:
			msgBox = QtWidgets.QMessageBox()
			msgBox.setText("Critical Error!.")
			msgBox.setInformativeText("Failed reading Chunk parameters. Something goes wrong. Try again.")
			print("Failed reading Chunk parameters. Something goes wrong. Try again.")
			msgBox.exec_()
			return

		self.exec()

	def onChange(self,i): #changed!
		if (i == 0):
			#print("View")
			self.mode = "xyz"
		elif (i == 1):
			#print("Region")
			self.mode = "bbox"
		elif (i == 2):
			#print("Object")
			self.objectClicked()
		
		self.getTransformMatrix()

	def tab1UI(self):
		orthoButton = QtWidgets.QPushButton("Orthographic")
		perspButton = QtWidgets.QPushButton("Perspective")
		buttonLayout1 = QtWidgets.QHBoxLayout()
		buttonLayout1.addWidget( orthoButton )
		buttonLayout1.addWidget( perspButton )
		
		orthoButton.clicked.connect(self.orthoButtonClicked)
		perspButton.clicked.connect(self.perspButtonClicked)

		self.backButton = QtWidgets.QPushButton("Back")
		self.leftButton = QtWidgets.QPushButton("Left")
		self.topButton = QtWidgets.QPushButton("Top")
		self.rightButton = QtWidgets.QPushButton("Right")
		self.bottomButton = QtWidgets.QPushButton("Bottom")
		self.frontButton = QtWidgets.QPushButton("Front")
		buttonLayoutGrid = QtWidgets.QGridLayout()
		buttonLayoutGrid.addWidget(self.backButton, 0 , 3, 1, 1)
		buttonLayoutGrid.addWidget(self.leftButton, 1 , 0, 1, 1)
		buttonLayoutGrid.addWidget(self.topButton, 1 , 3, 1, 1)
		buttonLayoutGrid.addWidget(self.rightButton, 1 , 6, 1, 1)
		buttonLayoutGrid.addWidget(self.bottomButton, 1 , 9, 1, 1)
		buttonLayoutGrid.addWidget(self.frontButton, 2 , 3, 1, 1)

		layout1 = QtWidgets.QVBoxLayout()
		layout1.addLayout( buttonLayout1 ) 
		layout1.addLayout( buttonLayoutGrid ) 

		labelStep = QtWidgets.QLabel("Step value:")
		self.textStep = QtWidgets.QPlainTextEdit()
		self.textStep.setFixedSize(75, 25)
		self.textStep.setPlainText("1.0")
		stepLayout = QtWidgets.QGridLayout()
		stepLayout.addWidget(labelStep, 4 , 6, 1, 1)
		stepLayout.addWidget(self.textStep, 4 , 9, 1, 1)

		##
		labelX = QtWidgets.QLabel("X:")
		self.xbutton1 = QtWidgets.QPushButton("<")
		self.xbutton1.setFixedSize(25, 25)
		self.slx = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.slx.setMinimum(10)
		self.slx.setMaximum(30)
		self.slx.setValue(20)
		self.slx.setTickInterval(5)
		self.xbutton2 = QtWidgets.QPushButton(">")
		self.xbutton2.setFixedSize(25, 25)

		__groupBoxXLayout = QtWidgets.QHBoxLayout()
		__groupBoxXLayout.addWidget(labelX)
		__groupBoxXLayout.addWidget(self.xbutton1)
		__groupBoxXLayout.addWidget(self.slx)
		__groupBoxXLayout.addWidget(self.xbutton2)
		##

		##
		labelY = QtWidgets.QLabel("Y:")
		self.ybutton1 = QtWidgets.QPushButton("<")
		self.ybutton1.setFixedSize(25, 25)
		self.sly = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.sly.setMinimum(10)
		self.sly.setMaximum(30)
		self.sly.setValue(20)
		self.sly.setTickInterval(5)
		self.ybutton2 = QtWidgets.QPushButton(">")
		self.ybutton2.setFixedSize(25, 25)

		__groupBoxYLayout = QtWidgets.QHBoxLayout()
		__groupBoxYLayout.addWidget(labelY)
		__groupBoxYLayout.addWidget(self.ybutton1)
		__groupBoxYLayout.addWidget(self.sly)
		__groupBoxYLayout.addWidget(self.ybutton2)
		##

		##
		labelZ = QtWidgets.QLabel("Z:")
		self.zbutton1 = QtWidgets.QPushButton("<")
		self.zbutton1.setFixedSize(25, 25)
		self.slz = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.slz.setMinimum(10)
		self.slz.setMaximum(30)
		self.slz.setValue(20)
		self.slz.setTickInterval(5)
		self.zbutton2 = QtWidgets.QPushButton(">")
		self.zbutton2.setFixedSize(25, 25)

		__groupBoxZLayout = QtWidgets.QHBoxLayout()
		__groupBoxZLayout.addWidget(labelZ)
		__groupBoxZLayout.addWidget(self.zbutton1)
		__groupBoxZLayout.addWidget(self.slz)
		__groupBoxZLayout.addWidget(self.zbutton2)
		##
		rotateLayout = QtWidgets.QVBoxLayout()
		rotateLayout.addLayout( __groupBoxXLayout )
		rotateLayout.addLayout( __groupBoxYLayout )
		rotateLayout.addLayout( __groupBoxZLayout ) 

		self.alignButtonView = QtWidgets.QPushButton("Align to Region")
		self.resetButton = QtWidgets.QPushButton("Reset View")
		buttonLayout2 = QtWidgets.QHBoxLayout()
		buttonLayout2.addWidget( self.alignButtonView )
		buttonLayout2.addWidget( self.resetButton )

		self.alignButtonView.clicked.connect(self.alignViewToBBox)

		layout2 = QtWidgets.QVBoxLayout()
		layout2.addLayout( stepLayout )
		layout2.addLayout( rotateLayout )

		groupBoxRotateView = QtWidgets.QGroupBox(self.tr("Rotate View"))
		groupBoxRotateView.setLayout( layout2 )


		cameras = QtWidgets.QCheckBox("Cameras")
		markers = QtWidgets.QCheckBox("Markers")
		other = QtWidgets.QCheckBox("Other Referenced Chunks")
		layout3 = QtWidgets.QVBoxLayout()
		layout3.addWidget( cameras )
		layout3.addWidget( markers )
		layout3.addWidget( other )
		cameras.setDisabled(True)
		markers.setDisabled(True)
		other.setDisabled(True)

		groupBoxShowItems = QtWidgets.QGroupBox(self.tr("Show/Hide Items"))
		groupBoxShowItems.setLayout( layout3 )

		internalLayout = QtWidgets.QVBoxLayout()
		internalLayout.addLayout( layout1 )
		internalLayout.addStretch(1)
		internalLayout.addWidget( groupBoxRotateView )
		internalLayout.addStretch(1)
		internalLayout.addWidget( groupBoxShowItems )
		internalLayout.addStretch(1)
		internalLayout.addLayout( buttonLayout2 )

		self.__tab1.setLayout( internalLayout )


		# Events
		self.slx.valueChanged.connect(self.sliderchangedX)
		self.sly.valueChanged.connect(self.sliderchangedY)
		self.slz.valueChanged.connect(self.sliderchangedZ)

		self.backButton.clicked.connect(self.backButtonClicked)
		self.leftButton.clicked.connect(self.leftButtonClicked)
		self.topButton.clicked.connect(self.topButtonClicked)
		self.rightButton.clicked.connect(self.rightButtonClicked)
		self.bottomButton.clicked.connect(self.bottomButtonClicked)
		self.frontButton.clicked.connect(self.frontClicked)
		self.resetButton.clicked.connect(self.resetButtonClicked)

		self.xbutton1.clicked.connect(self.xbutton1Clicked)
		self.xbutton2.clicked.connect(self.xbutton2Clicked)
		self.ybutton1.clicked.connect(self.ybutton1Clicked)
		self.ybutton2.clicked.connect(self.ybutton2Clicked)
		self.zbutton1.clicked.connect(self.zbutton1Clicked)
		self.zbutton2.clicked.connect(self.zbutton2Clicked)

		self.timedTask = False
		self.xbutton1.pressed.connect(self.xbutton1Pressed)
		self.xbutton1.released.connect(self.xbutton1Released)
		self.xbutton2.pressed.connect(self.xbutton2Pressed)
		self.xbutton2.released.connect(self.xbutton2Released)
		self.ybutton1.pressed.connect(self.ybutton1Pressed)
		self.ybutton1.released.connect(self.ybutton1Released)
		self.ybutton2.pressed.connect(self.ybutton2Pressed)
		self.ybutton2.released.connect(self.ybutton2Released)
		self.zbutton1.pressed.connect(self.zbutton1Pressed)
		self.zbutton1.released.connect(self.zbutton1Released)
		self.zbutton2.pressed.connect(self.zbutton2Pressed)
		self.zbutton2.released.connect(self.zbutton2Released)

	def config(self):
		self.slx.setMinimum(-180)
		self.slx.setMaximum(180)
		self.slx.setTickInterval(45)
		self.slx.setSingleStep(45)
		self.slx.setPageStep(45)
		self.slx.setTracking(True)
		self.slx.setTickPosition(QtWidgets.QSlider.TicksRight)

		self.sly.setMinimum(-180)
		self.sly.setMaximum(180)
		self.sly.setTickInterval(45)
		self.sly.setSingleStep(45)
		self.sly.setPageStep(45)
		self.sly.setTracking(True)
		self.sly.setTickPosition(QtWidgets.QSlider.TicksRight)

		self.slz.setMinimum(-180)
		self.slz.setMaximum(180)
		self.slz.setTickInterval(45)
		self.slz.setSingleStep(45)
		self.slz.setPageStep(45)
		self.slz.setTracking(True)
		self.slz.setTickPosition(QtWidgets.QSlider.TicksRight)

		self.slx_b.setMinimum(-180)
		self.slx_b.setMaximum(180)
		self.slx_b.setTickInterval(45)
		self.slx_b.setSingleStep(45)
		self.slx_b.setPageStep(45)
		self.slx_b.setTracking(True)
		self.slx_b.setTickPosition(QtWidgets.QSlider.TicksRight)

		self.sly_b.setMinimum(-180)
		self.sly_b.setMaximum(180)
		self.sly_b.setTickInterval(45)
		self.sly_b.setSingleStep(45)
		self.sly_b.setPageStep(45)
		self.sly_b.setTracking(True)
		self.sly_b.setTickPosition(QtWidgets.QSlider.TicksRight)

		self.slz_b.setMinimum(-180)
		self.slz_b.setMaximum(180)
		self.slz_b.setTickInterval(45)
		self.slz_b.setSingleStep(45)
		self.slz_b.setPageStep(45)
		self.slz_b.setTracking(True)
		self.slz_b.setTickPosition(QtWidgets.QSlider.TicksRight)

		self.slx_o.setMinimum(-180)
		self.slx_o.setMaximum(180)
		self.slx_o.setTickInterval(45)
		self.slx_o.setSingleStep(45)
		self.slx_o.setPageStep(45)
		self.slx_o.setTracking(True)
		self.slx_o.setTickPosition(QtWidgets.QSlider.TicksRight)

		self.sly_o.setMinimum(-180)
		self.sly_o.setMaximum(180)
		self.sly_o.setTickInterval(45)
		self.sly_o.setSingleStep(45)
		self.sly_o.setPageStep(45)
		self.sly_o.setTracking(True)
		self.sly_o.setTickPosition(QtWidgets.QSlider.TicksRight)

		self.slz_o.setMinimum(-180)
		self.slz_o.setMaximum(180)
		self.slz_o.setTickInterval(45)
		self.slz_o.setSingleStep(45)
		self.slz_o.setPageStep(45)
		self.slz_o.setTracking(True)
		self.slz_o.setTickPosition(QtWidgets.QSlider.TicksRight)

		# Obtain Omega/Phi/Kappa from viewpoint
		self.getTransformMatrix()

	def getTransformMatrix(self):

		if (self.mode == "xyz"):
			# Obtain Omega/Phi/Kappa from viewpoint
			R = self.getViewportTransformMatrix() * PhotoScan.app.model_view.viewpoint.rot
			self.omega, self.phi, self.kappa = PhotoScan.Utils.mat2opk(R)

			#print("O",self.omega)
			#print("P",self.phi)
			#print("K",self.kappa)

			self.slx.setValue(self.omega)
			self.sly.setValue(self.phi)
			self.slz.setValue(self.kappa)
			
		if (self.mode == "bbox"):
			R = self.getBBOXTransformMatrix()
			self.omega, self.phi, self.kappa = PhotoScan.utils.mat2opk(R) #current OPK

			#print("O",self.omega)
			#print("P",self.phi)
			#print("K",self.kappa)

			self.slx_b.setValue(self.omega)
			self.sly_b.setValue(self.phi)
			self.slz_b.setValue(self.kappa)

			self.textX_b.setText( "{:.2f}".format(self.omega) )
			self.textY_b.setText( "{:.2f}".format(self.phi) )
			self.textZ_b.setText( "{:.2f}".format(self.kappa) )

			doc = PhotoScan.app.document
			chunk = doc.chunk
			reg = chunk.region

			c = chunk.region.center
			c_temp = v1_new = chunk.transform.matrix.mulp(c)
			c_geo = chunk.crs.project(c_temp)

			if (chunk.transform.scale != None):
				s_scale = reg.size * chunk.transform.scale
			else :
				s_scale = reg.size

			self.textX2.setText( "{:.2f}".format(c_geo[0]) )
			self.textY2.setText( "{:.2f}".format(c_geo[1]) )
			self.textZ2.setText( "{:.2f}".format(c_geo[2]) )
			
			self.textX3.setText( "{:.2f}".format(s_scale[0]) )
			self.textY3.setText( "{:.2f}".format(s_scale[1]) )
			self.textZ3.setText( "{:.2f}".format(s_scale[2]) )

		elif (self.mode == "object"):
			R = self.getObjectTransformMatrix()
			self.omega, self.phi, self.kappa = PhotoScan.utils.mat2opk(R) #current OPK

			#print("O",self.omega)
			#print("P",self.phi)
			#print("K",self.kappa)

			self.slx_o.setValue(self.omega)
			self.sly_o.setValue(self.phi)
			self.slz_o.setValue(self.kappa)

			self.textX_o.setText( "{:.2f}".format(self.omega) )
			self.textY_o.setText( "{:.2f}".format(self.phi) )
			self.textZ_o.setText( "{:.2f}".format(self.kappa) )
			

	def getViewportTransformMatrix(self):
		doc = PhotoScan.app.document
		chunk = doc.chunk
		# Transform matrix 4x4
		T = chunk.transform.matrix

		# Translation vector 3
		#v_t = T * PhotoScan.Vector( [0,0,0,1] )
		#v_t.size = 3
		v_t = T.translation() #replaces two lines above
		if chunk.crs:
			m = chunk.crs.localframe(v_t)
		else:
			m = PhotoScan.Matrix().Diag([1,1,1,1])

		#R = PhotoScan.Matrix( [[m[0,0],m[0,1],m[0,2]], [m[1,0],m[1,1],m[1,2]], [m[2,0],m[2,1],m[2,2]]])
		R = m.rotation() #replaces the line above
		
		return R

	def getBBOXTransformMatrix(self):
		chunk = doc.chunk
		T = chunk.transform.matrix
		region = chunk.region
		local = chunk.crs.localframe(T.mulp(region.center))

		return (local * T).rotation() * region.rot

	def getObjectTransformMatrix(self):
		chunk = doc.chunk
		T = chunk.transform.matrix
		rot = PhotoScan.Matrix.Diag([1, -1, -1])
		local = chunk.crs.localframe(T.mulp(PhotoScan.Vector([0,0,0])))

		return (local * T).rotation() * rot

	def sliderchangedX(self):
		if ( self.slx.isSliderDown() ):
			self.omega = float( self.slx.value() )
			self.transform()

		if ( self.slx_b.isSliderDown() ):
			self.omega = float( self.slx_b.value() )
			self.transform()
			self.textX_b.setText( "{:.2f}".format(self.omega) )
		
		if ( self.slx_o.isSliderDown() ):
			self.omega = float( self.slx_o.value() )
			self.transform()
			self.textX_o.setText( "{:.2f}".format(self.omega) )

		return True

	def sliderchangedY(self):
		if ( self.sly.isSliderDown() ):
			self.phi = float( self.sly.value() )
			self.transform()

		if ( self.sly_b.isSliderDown() ):
			self.phi = float( self.sly_b.value() )
			self.transform()
			self.textY_b.setText( "{:.2f}".format(self.phi) )
		
		if ( self.sly_o.isSliderDown() ):
			self.phi = float( self.sly_o.value() )
			self.transform()
			self.textY_o.setText( "{:.2f}".format(self.phi) )

		return True

	def sliderchangedZ(self):
		if ( self.slz.isSliderDown() ):
			self.kappa = float( self.slz.value() )
			self.transform()

		if ( self.slz_b.isSliderDown() ):
			self.kappa = float( self.slz_b.value() )
			self.transform()
			self.textZ_b.setText( "{:.2f}".format(self.kappa) )
		
		if ( self.slz_o.isSliderDown() ):
			self.kappa = float( self.slz_o.value() )
			self.transform()
			self.textZ_o.setText( "{:.2f}".format(self.kappa) )

		return True

	def resetButtonClicked(self):
		self.topButtonClicked()

	def backButtonClicked(self):
		self.omega = -90.0
		self.phi = 0.0
		self.kappa = -180.0
		self.transform()
		self.getTransformMatrix()

	def leftButtonClicked(self):
		self.omega = 0.0
		self.phi = -90.0
		self.kappa = -90.0
		self.transform()
		self.getTransformMatrix()

	def topButtonClicked(self):
		self.omega = 0.0 
		self.phi = 0.0 
		self.kappa = 0.0
		self.transform()
		self.getTransformMatrix()

	def rightButtonClicked(self):
		self.omega = 180.0
		self.phi = 90.0
		self.kappa = -90.0
		self.transform()
		self.getTransformMatrix()

	def bottomButtonClicked(self):
		self.omega = -180.0
		self.phi = 0.0
		self.kappa = 0.0
		self.transform()
		self.getTransformMatrix()

	def frontClicked(self):
		self.omega = 90 
		self.phi = 0.0
		self.kappa = 0.0
		self.transform()
		self.getTransformMatrix()

	def initSchedule(self, delegate):
		self.rt.stop()
		self.timedTask = True
		self.rtscheduled = RepeatedTimer(0.2, delegate)

	def dox1buttonClickedTask(self):
		if (self.mode == "xyz"):
			step = self.textStep.toPlainText()
		if (self.mode == "bbox"):
			step = self.textStep_b.toPlainText()
		if (self.mode == "object"):
			step = self.textStep_o.toPlainText()

		if ( self.omega - float(step) ) < -180:
			self.omega = ( self.omega - float(step) ) + 360
		else :
			self.omega = ( self.omega - float(step) )

		if (self.mode == "xyz"):
			self.slx.setValue ( int(self.omega) )
		if (self.mode == "bbox"):
			self.slx_b.setValue ( int(self.omega) )
		if (self.mode == "object"):
			self.slx_o.setValue ( int(self.omega) )

		self.transform()

	def xbutton1Pressed(self):
		self.rt = RepeatedTimer(1, self.initSchedule, self.dox1buttonClickedTask) # it auto-starts, no need of rt.start()

	def xbutton1Released(self):
		try:
			self.rt.stop()
			self.rtscheduled.stop()
		except:
			self.rt = None
			self.rtscheduled = None

		if (self.mode == "bbox"):
			self.textX_b.setText( "{:.2f}".format(self.omega) )
		if (self.mode == "object"):
			self.textX_o.setText( "{:.2f}".format(self.omega) )

	def xbutton1Clicked(self):
		#print("Button xbutton1Clicked")
		if self.timedTask :
			self.timedTask = False
		else:
			self.dox1buttonClickedTask()
			
			if (self.mode == "bbox"):
				self.textX_b.setText( "{:.2f}".format(self.omega) )
			if (self.mode == "object"):
				self.textX_o.setText( "{:.2f}".format(self.omega) )

		return True

	def dox2buttonClickedTask(self):
		if (self.mode == "xyz"):
			step = self.textStep.toPlainText()
		if (self.mode == "bbox"):
			step = self.textStep_b.toPlainText()
		if (self.mode == "object"):
			step = self.textStep_o.toPlainText()

		if ( self.omega + float(step) ) > 180:
			self.omega = ( self.omega + float(step) ) - 360
		else :
			self.omega = ( self.omega + float(step) )

		if (self.mode == "xyz"):
			self.slx.setValue ( int(self.omega) )
		if (self.mode == "bbox"):
			self.slx_b.setValue ( int(self.omega) )
		if (self.mode == "object"):
			self.slx_o.setValue ( int(self.omega) )
			
		self.transform()

	def xbutton2Pressed(self):
		self.rt = RepeatedTimer(1, self.initSchedule, self.dox2buttonClickedTask) # it auto-starts, no need of rt.start()

	def xbutton2Released(self):
		try:
			self.rt.stop()
			self.rtscheduled.stop()
		except:
			self.rt = None
			self.rtscheduled = None
		
		if (self.mode == "bbox"):
			self.textX_b.setText( "{:.2f}".format(self.omega) )
		if (self.mode == "object"):
			self.textX_o.setText( "{:.2f}".format(self.omega) )

	def xbutton2Clicked(self):
		#print("Button xbutton2Clicked")
		if self.timedTask :
			self.timedTask = False
		else:
			self.dox2buttonClickedTask()
			
			if (self.mode == "bbox"):
				self.textX_b.setText( "{:.2f}".format(self.omega) )
			if (self.mode == "object"):
				self.textX_o.setText( "{:.2f}".format(self.omega) )

		return True

	def doy1buttonClickedTask(self):
		if (self.mode == "xyz"):
			step = self.textStep.toPlainText()
		if (self.mode == "bbox"):
			step = self.textStep_b.toPlainText()
		if (self.mode == "object"):
			step = self.textStep_o.toPlainText()

		if ( self.phi - float(step) ) < -180:
			self.phi = ( self.phi - float(step) ) + 360
		else :
			self.phi = ( self.phi - float(step) )
		
		if (self.mode == "xyz"):
			self.sly.setValue ( int(self.phi) )
		if (self.mode == "bbox"):
			self.sly_b.setValue ( int(self.phi) )
		if (self.mode == "object"):
			self.sly_o.setValue ( int(self.phi) )

		self.transform()

	def ybutton1Pressed(self):
		self.rt = RepeatedTimer(1, self.initSchedule, self.doy1buttonClickedTask) # it auto-starts, no need of rt.start()

	def ybutton1Released(self):
		try:
			self.rt.stop()
			self.rtscheduled.stop()
		except:
			self.rt = None
			self.rtscheduled = None
		
		if (self.mode == "bbox"):
			self.textY_b.setText( "{:.2f}".format(self.phi) )
		if (self.mode == "object"):
			self.textY_o.setText( "{:.2f}".format(self.phi) )

	def ybutton1Clicked(self):
		#print("Button ybutton1Clicked")
		if self.timedTask :
			self.timedTask = False
		else:
			self.doy1buttonClickedTask()
			if (self.mode == "bbox"):
				self.textY_b.setText( "{:.2f}".format(self.phi) )
			if (self.mode == "object"):
				self.textY_o.setText( "{:.2f}".format(self.phi) )

		return True

	def doy2buttonClickedTask(self):
		if (self.mode == "xyz"):
			step = self.textStep.toPlainText()
		if (self.mode == "bbox"):
			step = self.textStep_b.toPlainText()
		if (self.mode == "object"):
			step = self.textStep_o.toPlainText()

		if ( self.phi + float(step) ) > 180:
			self.phi = ( self.phi + float(step) ) - 360
		else :
			self.phi = ( self.phi + float(step) )
		
		if (self.mode == "xyz"):
			self.sly.setValue ( int(self.phi) )
		if (self.mode == "bbox"):
			self.sly_b.setValue ( int(self.phi) )
		if (self.mode == "object"):
			self.sly_o.setValue ( int(self.phi) )

		self.transform()

	def ybutton2Pressed(self):
		self.rt = RepeatedTimer(1, self.initSchedule, self.doy2buttonClickedTask) # it auto-starts, no need of rt.start()

	def ybutton2Released(self):
		try:
			self.rt.stop()
			self.rtscheduled.stop()
		except:
			self.rt = None
			self.rtscheduled = None

		if (self.mode == "bbox"):
			self.textY_b.setText( "{:.2f}".format(self.phi) )
		if (self.mode == "object"):
			self.textY_o.setText( "{:.2f}".format(self.phi) )

	def ybutton2Clicked(self):
		#print("Button ybutton2Clicked")
		if self.timedTask :
			self.timedTask = False
		else:
			self.doy2buttonClickedTask()
			if (self.mode == "bbox"):
				self.textY_b.setText( "{:.2f}".format(self.phi) )
			if (self.mode == "object"):
				self.textY_o.setText( "{:.2f}".format(self.phi) )

		return True

	def doz1buttonClickedTask(self):
		if (self.mode == "xyz"):
			step = self.textStep.toPlainText()
		if (self.mode == "bbox"):
			step = self.textStep_b.toPlainText()
		if (self.mode == "object"):
			step = self.textStep_o.toPlainText()

		if ( self.kappa - float(step) ) < -180:
			self.kappa = ( self.kappa - float(step) ) + 360
		else :
			self.kappa = ( self.kappa - float(step) )
			
		if (self.mode == "xyz"):
			self.slz.setValue ( int(self.kappa) )
		if (self.mode == "bbox"):
			self.slz_b.setValue ( int(self.kappa) )
		if (self.mode == "object"):
			self.slz_o.setValue ( int(self.kappa) )

		self.transform()

	def zbutton1Pressed(self):
		self.rt = RepeatedTimer(1, self.initSchedule, self.doz1buttonClickedTask) # it auto-starts, no need of rt.start()

	def zbutton1Released(self):
		#print("Button zbutton1Released")
		try:
			self.rt.stop()
			self.rtscheduled.stop()
		except:
			self.rt = None
			self.rtscheduled = None

		if (self.mode == "bbox"):
			self.textZ_b.setText( "{:.2f}".format(self.kappa) )
		if (self.mode == "object"):
			self.textZ_o.setText( "{:.2f}".format(self.kappa) )

	def zbutton1Clicked(self):
		#print("Button zbutton1Clicked")
		if self.timedTask :
			self.timedTask = False
		else:
			self.doz1buttonClickedTask()
			if (self.mode == "bbox"):
				self.textZ_b.setText( "{:.2f}".format(self.kappa) )
			if (self.mode == "object"):
				self.textZ_o.setText( "{:.2f}".format(self.kappa) )

		return True

	def doz2buttonClickedTask(self):
		if (self.mode == "xyz"):
			step = self.textStep.toPlainText()
		if (self.mode == "bbox"):
			step = self.textStep_b.toPlainText()
		if (self.mode == "object"):
			step = self.textStep_o.toPlainText()

		if ( self.kappa + float(step) ) > 180:
			self.kappa = ( self.kappa + float(step) ) - 360
		else :
			self.kappa = ( self.kappa + float(step) )
		

		if (self.mode == "xyz"):
			self.slz.setValue ( int(self.kappa) )
		if (self.mode == "bbox"):
			self.slz_b.setValue ( int(self.kappa) )			
		if (self.mode == "object"):
			self.slz_o.setValue ( int(self.kappa) )			

		self.transform()

	def zbutton2Pressed(self):
		self.rt = RepeatedTimer(1, self.initSchedule, self.doz2buttonClickedTask) # it auto-starts, no need of rt.start()

	def zbutton2Released(self):
		try:
			self.rt.stop()
			self.rtscheduled.stop()
		except:
			self.rt = None
			self.rtscheduled = None

		if (self.mode == "bbox"):
			self.textZ_b.setText( "{:.2f}".format(self.kappa) )
		if (self.mode == "object"):
			self.textZ_o.setText( "{:.2f}".format(self.kappa) )

	def zbutton2Clicked(self):
		#print("Button zbutton2Clicked")
		if self.timedTask :
			self.timedTask = False
		else:
			self.doz2buttonClickedTask()
			if (self.mode == "bbox"):
				self.textZ_b.setText( "{:.2f}".format(self.kappa) )
			if (self.mode == "object"):
				self.textZ_o.setText( "{:.2f}".format(self.kappa) )

		return True

	def transform(self):
		if (self.mode == "xyz"):
			# Obtain Transformation Matrix from viewpoint
			R = self.getViewportTransformMatrix()
			# Obtain Omega/Phi/Kappa Rotation matrix
			newR = PhotoScan.Utils.opk2mat([self.omega, self.phi, self.kappa])
			# Apply transformation
			PhotoScan.app.model_view.viewpoint.rot = R.inv() * newR
		elif (self.mode == "bbox"):
			# Obtain Transformation Matrix from bbox
			chunk = doc.chunk
			T = chunk.transform.matrix
			region = chunk.region
			local = chunk.crs.localframe(T.mulp(region.center))
			# Obtain Omega/Phi/Kappa Rotation matrix
			newR = PhotoScan.Utils.opk2mat([self.omega, self.phi, self.kappa])
			# Apply transformation
			region.rot = (local * T).inv().rotation() * newR
			chunk.region = region
			PhotoScan.app.update()
		elif (self.mode == "object"):
			v_rot = PhotoScan.app.model_view.viewpoint.rot
			v_coo = PhotoScan.app.model_view.viewpoint.coo
			v_mag = PhotoScan.app.model_view.viewpoint.mag

			chunk = doc.chunk
			T = chunk.transform.matrix
			region = chunk.region
			local = chunk.crs.localframe(T.mulp(PhotoScan.Vector([0,0,0])))
			# Obtain Omega/Phi/Kappa Rotation matrix
			rot = PhotoScan.Matrix.Diag([1, -1, -1])
			newR = PhotoScan.Utils.opk2mat([self.omega, self.phi, self.kappa])
			# Apply transformation
			region.rot = (local * T).inv().rotation() * newR
			if(self.centerMode == "center"):
				chunk.transform.rotation = local.inv().rotation()*(newR * rot.inv())
			elif (self.centerMode == "point"):
				Xc = float(self.a1.text())
				Yc = float(self.a2.text())
				Zc = float(self.a3.text())

				new_center = PhotoScan.Vector([Xc, Yc, Zc]) #coordinates in the chunk coordinate system
				crs = chunk.crs
				p = T.inv().mulp(crs.unproject(new_center))
				new_rot = local.inv().rotation()*(R * rot.inv())
				chunk.transform.translation = chunk.transform.scale * (chunk.transform.rotation - new_rot) * p + chunk.transform.translation
				chunk.transform.rotation = new_rot
			else:
				chunk.transform.translation = PhotoScan.Vector(
					[ float(self.o_a14.Text()), 
					  float(self.o_a14.Text()), 
					  float(self.o_a14.Text())
					])
				chunk.transform.rotation = PhotoScan.utils.opk2mat(R)
				chunk.transform.scale = float(self.o_a44.Text())

			PhotoScan.app.update()
			PhotoScan.app.model_view.viewpoint.rot = v_rot
			PhotoScan.app.model_view.viewpoint.coo = v_coo
			PhotoScan.app.model_view.viewpoint.mag = v_mag

	def RegionChanged(self):
		Xc = float(self.textX2.text())
		Yc = float(self.textY2.text())
		Zc = float(self.textZ2.text())

		Xs = float(self.textX3.text())
		Ys = float(self.textY3.text())
		Zs = float(self.textZ3.text())

		new_center = PhotoScan.Vector([Xc, Yc, Zc]) #coordinates in the chunk coordinate system
		new_size = PhotoScan.Vector([Xs, Ys, Zs]) #size in the coordinate system units

		doc = PhotoScan.app.document
		chunk = doc.chunk
		T = chunk.transform.matrix
		S = chunk.transform.scale
		crs = chunk.crs

		region = chunk.region
		region.center = T.inv().mulp(crs.unproject(new_center))
		if (S != None):
			region.size = new_size / S
		else :
			region.size = new_size
		chunk.region = region

		PhotoScan.app.update()

	def omegaTextChanged(self):
		if (self.mode == "bbox"):
			value = self.textX_b.text()
		else :
			value = self.textX_o.text()

		if (float(value) > -180 and float(value) < 180):
			self.omega = float(value)
		
		if (self.mode == "bbox"):
			self.slx_b.setValue ( int(self.omega) )
		if (self.mode == "object"):
			self.slx_o.setValue ( int(self.omega) )

		self.transform()

	def phiTextChanged(self):
		if (self.mode == "bbox"):
			value = self.textX_b.text()
		else :
			value = self.textX_o.text()

		if (float(value) > -180 and float(value) < 180):
			self.phi = float(value)
		
		if (self.mode == "bbox"):
			self.sly_b.setValue ( int(self.phi) )
		if (self.mode == "object"):
			self.sly_o.setValue ( int(self.phi) )

		self.transform()

	def kappaTextChanged(self):
		if (self.mode == "bbox"):
			value = self.textX_b.text()
		else :
			value = self.textX_o.text()
		
		if (float(value) > -180 and float(value) < 180):
			self.kappa = float(value)
		
		if (self.mode == "bbox"):
			self.slz_b.setValue ( int(self.kappa) )
		if (self.mode == "object"):
			self.slz_o.setValue ( int(self.kappa) )

		self.transform()

	def tab2UI(self):
		self.resetButton2 = QtWidgets.QPushButton("Reset Region")
		buttonLayout1 = QtWidgets.QHBoxLayout()
		buttonLayout1.addWidget( self.resetButton2 )

		layout1 = QtWidgets.QVBoxLayout()
		layout1.addLayout( buttonLayout1 ) 

		labelStep = QtWidgets.QLabel("Step value:")
		self.textStep_b = QtWidgets.QPlainTextEdit()
		self.textStep_b.setFixedSize(75, 25)
		self.textStep_b.setPlainText("1.0")
		stepLayout = QtWidgets.QGridLayout()
		stepLayout.addWidget(labelStep, 0 , 6, 1, 1)
		stepLayout.addWidget(self.textStep_b, 0 , 9, 1, 1)

		##
		labelX = QtWidgets.QLabel("Omega:")
		self.textX_b = QtWidgets.QLineEdit()
		self.textX_b.setFixedSize(75, 25)
		self.xbutton1_b = QtWidgets.QPushButton("<")
		self.xbutton1_b.setFixedSize(25, 25)
		self.slx_b = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.slx_b.setMinimum(10)
		self.slx_b.setMaximum(30)
		self.slx_b.setValue(20)
		self.slx_b.setTickInterval(5)
		self.xbutton2_b = QtWidgets.QPushButton(">")
		self.xbutton2_b.setFixedSize(25, 25)

		__groupBoxLayout = QtWidgets.QGridLayout()
		__groupBoxLayout.addWidget(labelX, 0, 0, 1, 1)
		__groupBoxLayout.addWidget(self.textX_b, 0, 2, 1, 1)
		__groupBoxLayout.addWidget(self.xbutton1_b, 0, 3, 1, 1)
		__groupBoxLayout.addWidget(self.slx_b, 0, 4, 1, 1)
		__groupBoxLayout.addWidget(self.xbutton2_b, 0, 6, 1, 1)
		##

		##
		labelY = QtWidgets.QLabel("Phi:")
		self.textY_b = QtWidgets.QLineEdit()
		self.textY_b.setFixedSize(75, 25)
		self.ybutton1_b = QtWidgets.QPushButton("<")
		self.ybutton1_b.setFixedSize(25, 25)
		self.sly_b = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.sly_b.setMinimum(10)
		self.sly_b.setMaximum(30)
		self.sly_b.setValue(20)
		self.sly_b.setTickInterval(5)
		self.ybutton2_b = QtWidgets.QPushButton(">")
		self.ybutton2_b.setFixedSize(25, 25)

		__groupBoxLayout.addWidget(labelY, 1, 0, 1, 1)
		__groupBoxLayout.addWidget(self.textY_b, 1, 2, 1, 1)
		__groupBoxLayout.addWidget(self.ybutton1_b, 1, 3, 1, 1)
		__groupBoxLayout.addWidget(self.sly_b, 1, 4, 1, 1)
		__groupBoxLayout.addWidget(self.ybutton2_b, 1, 6, 1, 1)
		##

		##
		labelZ = QtWidgets.QLabel("Kappa:")
		self.textZ_b = QtWidgets.QLineEdit()
		self.textZ_b.setFixedSize(75, 25)
		self.zbutton1_b = QtWidgets.QPushButton("<")
		self.zbutton1_b.setFixedSize(25, 25)
		self.slz_b = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.slz_b.setMinimum(10)
		self.slz_b.setMaximum(30)
		self.slz_b.setValue(20)
		self.slz_b.setTickInterval(5)
		self.zbutton2_b = QtWidgets.QPushButton(">")
		self.zbutton2_b.setFixedSize(25, 25)

		__groupBoxLayout.addWidget(labelZ, 2, 0, 1, 1)
		__groupBoxLayout.addWidget(self.textZ_b, 2, 2, 1, 1)
		__groupBoxLayout.addWidget(self.zbutton1_b, 2, 3, 1, 1)
		__groupBoxLayout.addWidget(self.slz_b, 2, 4, 1, 1)
		__groupBoxLayout.addWidget(self.zbutton2_b, 2, 6, 1, 1)
		##

		rotateLayout = QtWidgets.QVBoxLayout()
		rotateLayout.addLayout( __groupBoxLayout )

		layout2 = QtWidgets.QVBoxLayout()
		layout2.addLayout( stepLayout )
		layout2.addLayout( rotateLayout )

		groupBoxRotateView = QtWidgets.QGroupBox(self.tr("Rotate Region"))
		groupBoxRotateView.setLayout( layout2 )

		labelStep2 = QtWidgets.QLabel("Step value:")
		self.textStep2_b = QtWidgets.QPlainTextEdit()
		self.textStep2_b.setFixedSize(75, 25)
		stepLayout2 = QtWidgets.QGridLayout()
		stepLayout2.addWidget(labelStep2, 0 , 6, 1, 1)
		stepLayout2.addWidget(self.textStep2_b, 0 , 9, 1, 1)

		self.textStep2_b.setPlainText("1.0")

		##
		labelX2 = QtWidgets.QLabel("Xc:")
		self.textX2 = QtWidgets.QLineEdit()
		self.textX2.setFixedSize(150, 25)
		self.xbutton12 = QtWidgets.QPushButton("<")
		self.xbutton12.setFixedSize(25, 25)
		self.xbutton22 = QtWidgets.QPushButton(">")
		self.xbutton22.setFixedSize(25, 25)

		__groupBoxLayout2 = QtWidgets.QGridLayout()
		__groupBoxLayout2.addWidget(labelX2, 0, 0, 1, 1)
		__groupBoxLayout2.addWidget(self.textX2, 0, 1, 1, 1)
		__groupBoxLayout2.addWidget(self.xbutton12, 0, 3, 1, 1)
		__groupBoxLayout2.addWidget(self.xbutton22, 0, 4, 1, 1)
		##

		##
		labelY2 = QtWidgets.QLabel("Yc:")
		self.textY2 = QtWidgets.QLineEdit()
		self.textY2.setFixedSize(150, 25)
		self.ybutton12 = QtWidgets.QPushButton("<")
		self.ybutton12.setFixedSize(25, 25)
		self.ybutton22 = QtWidgets.QPushButton(">")
		self.ybutton22.setFixedSize(25, 25)

		__groupBoxLayout2.addWidget(labelY2, 1, 0, 1, 1)
		__groupBoxLayout2.addWidget(self.textY2, 1, 1, 1, 1)
		__groupBoxLayout2.addWidget(self.ybutton12, 1, 3, 1, 1)
		__groupBoxLayout2.addWidget(self.ybutton22, 1, 4, 1, 1)
		##

		##
		labelZ2 = QtWidgets.QLabel("Zc:")
		self.textZ2 = QtWidgets.QLineEdit()
		self.textZ2.setFixedSize(150, 25)
		self.zbutton12 = QtWidgets.QPushButton("<")
		self.zbutton12.setFixedSize(25, 25)
		self.zbutton22 = QtWidgets.QPushButton(">")
		self.zbutton22.setFixedSize(25, 25)

		__groupBoxLayout2.addWidget(labelZ2, 2, 0, 1, 1)
		__groupBoxLayout2.addWidget(self.textZ2, 2, 1, 1, 1)
		__groupBoxLayout2.addWidget(self.zbutton12, 2, 3, 1, 1)
		__groupBoxLayout2.addWidget(self.zbutton22, 2, 4, 1, 1)
		##

		translateLayout = QtWidgets.QVBoxLayout()
		translateLayout.addLayout( __groupBoxLayout2 )

		##
		labelX3 = QtWidgets.QLabel("Length:")
		self.textX3 = QtWidgets.QLineEdit()
		self.textX3.setFixedSize(150, 25)
		self.xbutton13 = QtWidgets.QPushButton("<")
		self.xbutton13.setFixedSize(25, 25)
		self.xbutton23 = QtWidgets.QPushButton(">")
		self.xbutton23.setFixedSize(25, 25)

		__groupBoxLayout3 = QtWidgets.QGridLayout()
		__groupBoxLayout3.addWidget(labelX3, 0, 0, 1, 1)
		__groupBoxLayout3.addWidget(self.textX3, 0, 1, 1, 1)
		__groupBoxLayout3.addWidget(self.xbutton13, 0, 3, 1, 1)
		__groupBoxLayout3.addWidget(self.xbutton23, 0, 4, 1, 1)
		##

		##
		labelY3 = QtWidgets.QLabel("Width:")
		self.textY3 = QtWidgets.QLineEdit()
		self.textY3.setFixedSize(150, 25)
		self.ybutton13 = QtWidgets.QPushButton("<")
		self.ybutton13.setFixedSize(25, 25)
		self.ybutton23 = QtWidgets.QPushButton(">")
		self.ybutton23.setFixedSize(25, 25)

		__groupBoxLayout3.addWidget(labelY3, 1, 0, 1, 1)
		__groupBoxLayout3.addWidget(self.textY3, 1, 1, 1, 1)
		__groupBoxLayout3.addWidget(self.ybutton13, 1, 3, 1, 1)
		__groupBoxLayout3.addWidget(self.ybutton23, 1, 4, 1, 1)
		##

		##
		labelZ3 = QtWidgets.QLabel("Height:")
		self.textZ3 = QtWidgets.QLineEdit()
		self.textZ3.setFixedSize(150, 25)
		self.zbutton13 = QtWidgets.QPushButton("<")
		self.zbutton13.setFixedSize(25, 25)
		self.zbutton23 = QtWidgets.QPushButton(">")
		self.zbutton23.setFixedSize(25, 25)

		__groupBoxLayout3.addWidget(labelZ3, 2, 0, 1, 1)
		__groupBoxLayout3.addWidget(self.textZ3, 2, 1, 1, 1)
		__groupBoxLayout3.addWidget(self.zbutton13, 2, 3, 1, 1)
		__groupBoxLayout3.addWidget(self.zbutton23, 2, 4, 1, 1)
		##

		resizeLayout = QtWidgets.QVBoxLayout()
		resizeLayout.addLayout( __groupBoxLayout3 )

		layout3 = QtWidgets.QVBoxLayout()
		layout3.addLayout( stepLayout2 )
		layout3.addLayout( translateLayout )
		layout3.addLayout( resizeLayout )

		groupBoxTranslate = QtWidgets.QGroupBox(self.tr("Translate/Resize Region"))
		groupBoxTranslate.setLayout( layout3 )

		self.alignButton = QtWidgets.QPushButton("Align to CRS")
		self.viewButton = QtWidgets.QPushButton("Align to View")
		buttonLayout2 = QtWidgets.QHBoxLayout()
		buttonLayout2.addWidget( self.alignButton )
		buttonLayout2.addWidget( self.viewButton )

		internalLayout = QtWidgets.QVBoxLayout()
		internalLayout.addWidget( groupBoxRotateView )
		internalLayout.addStretch(1)
		internalLayout.addWidget( groupBoxTranslate )
		internalLayout.addStretch(1)
		internalLayout.addLayout( layout1 )
		internalLayout.addStretch(1)
		internalLayout.addLayout( buttonLayout2 )

		self.__tab2.setLayout( internalLayout )

		# Events
		self.slx_b.valueChanged.connect(self.sliderchangedX)
		self.sly_b.valueChanged.connect(self.sliderchangedY)
		self.slz_b.valueChanged.connect(self.sliderchangedZ)

		self.xbutton1_b.clicked.connect(self.xbutton1Clicked)
		self.xbutton2_b.clicked.connect(self.xbutton2Clicked)
		self.ybutton1_b.clicked.connect(self.ybutton1Clicked)
		self.ybutton2_b.clicked.connect(self.ybutton2Clicked)
		self.zbutton1_b.clicked.connect(self.zbutton1Clicked)
		self.zbutton2_b.clicked.connect(self.zbutton2Clicked)

		self.timedTask = False
		self.xbutton1_b.pressed.connect(self.xbutton1Pressed)
		self.xbutton1_b.released.connect(self.xbutton1Released)
		self.xbutton2_b.pressed.connect(self.xbutton2Pressed)
		self.xbutton2_b.released.connect(self.xbutton2Released)
		self.ybutton1_b.pressed.connect(self.ybutton1Pressed)
		self.ybutton1_b.released.connect(self.ybutton1Released)
		self.ybutton2_b.pressed.connect(self.ybutton2Pressed)
		self.ybutton2_b.released.connect(self.ybutton2Released)
		self.zbutton1_b.pressed.connect(self.zbutton1Pressed)
		self.zbutton1_b.released.connect(self.zbutton1Released)
		self.zbutton2_b.pressed.connect(self.zbutton2Pressed)
		self.zbutton2_b.released.connect(self.zbutton2Released)

		self.textX_b.returnPressed.connect(self.omegaTextChanged)
		self.textY_b.returnPressed.connect(self.phiTextChanged)
		self.textZ_b.returnPressed.connect(self.kappaTextChanged)

		self.textX2.returnPressed.connect(self.RegionChanged)
		self.textY2.returnPressed.connect(self.RegionChanged)
		self.textZ2.returnPressed.connect(self.RegionChanged)
		self.textX3.returnPressed.connect(self.RegionChanged)
		self.textY3.returnPressed.connect(self.RegionChanged)
		self.textZ3.returnPressed.connect(self.RegionChanged)

		self.xbutton12.clicked.connect(self.xbutton12Clicked)
		self.xbutton22.clicked.connect(self.xbutton22Clicked)
		self.ybutton12.clicked.connect(self.ybutton12Clicked)
		self.ybutton22.clicked.connect(self.ybutton22Clicked)
		self.zbutton12.clicked.connect(self.zbutton12Clicked)
		self.zbutton22.clicked.connect(self.zbutton22Clicked)

		self.xbutton13.clicked.connect(self.xbutton13Clicked)
		self.xbutton23.clicked.connect(self.xbutton23Clicked)
		self.ybutton13.clicked.connect(self.ybutton13Clicked)
		self.ybutton23.clicked.connect(self.ybutton23Clicked)
		self.zbutton13.clicked.connect(self.zbutton13Clicked)
		self.zbutton23.clicked.connect(self.zbutton23Clicked)

		self.resetButton2.clicked.connect(self.resetRegionClicked)
		self.alignButton.clicked.connect(self.alignBBoxToCRS)
		self.viewButton.clicked.connect(self.alignBBoxToView)

	def resetRegionClicked(self):
		doc = PhotoScan.app.document
		chunk = doc.chunk
		chunk.resetRegion()

		self.getTransformMatrix()

	def alignViewToBBox(self):
		R = self.getBBOXTransformMatrix()
		self.omega, self.phi, self.kappa = PhotoScan.utils.mat2opk(R) #current OPK

		self.transform()
		self.getTransformMatrix()

	def alignBBoxToView(self):
		R = self.getViewportTransformMatrix() * PhotoScan.app.model_view.viewpoint.rot
		self.omega, self.phi, self.kappa = PhotoScan.Utils.mat2opk(R)

		self.transform()
		self.getTransformMatrix()

	def alignBBoxToCRS(self):
		doc = PhotoScan.app.document
		chunk = doc.chunk

		T = chunk.transform.matrix
		v_t = T * PhotoScan.Vector( [0,0,0,1] )
		v_t.size = 3

		if chunk.crs:
			m = chunk.crs.localframe(v_t)
		else:
			m = PhotoScan.Matrix().Diag([1,1,1,1])

		m = m * T
		s = math.sqrt(m[0,0] ** 2 + m[0,1] ** 2 + m[0,2] ** 2) #scale factor
		R = PhotoScan.Matrix( [[m[0,0],m[0,1],m[0,2]], [m[1,0],m[1,1],m[1,2]], [m[2,0],m[2,1],m[2,2]]])
		R = R * (1. / s)

		reg = chunk.region
		reg.rot = R.t()
		chunk.region = reg

		self.getTransformMatrix()


	def xbutton12Clicked(self):
		value = float(self.textX2.text())
		step = float(self.textStep2_b.toPlainText())
		self.textX2.setText(str(value - step))

		self.RegionChanged()

	def xbutton22Clicked(self):
		value = float(self.textX2.text())
		step = float(self.textStep2_b.toPlainText())
		self.textX2.setText(str(value + step))

		self.RegionChanged()

	def ybutton12Clicked(self):
		value = float(self.textY2.text())
		step = float(self.textStep2_b.toPlainText())
		self.textY2.setText(str(value - step))

		self.RegionChanged()

	def ybutton22Clicked(self):
		value = float(self.textY2.text())
		step = float(self.textStep2_b.toPlainText())
		self.textY2.setText(str(value + step))

		self.RegionChanged()

	def zbutton12Clicked(self):
		value = float(self.textZ2.text())
		step = float(self.textStep2_b.toPlainText())
		self.textZ2.setText(str(value - step))

		self.RegionChanged()

	def zbutton22Clicked(self):
		value = float(self.textZ2.text())
		step = float(self.textStep2_b.toPlainText())
		self.textZ2.setText(str(value + step))

		self.RegionChanged()

	def xbutton13Clicked(self):
		value = float(self.textX3.text())
		step = float(self.textStep2_b.toPlainText())
		self.textX3.setText(str(value - step))

		self.RegionChanged()

	def xbutton23Clicked(self):
		value = float(self.textX3.text())
		step = float(self.textStep2_b.toPlainText())
		self.textX3.setText(str(value + step))

		self.RegionChanged()

	def ybutton13Clicked(self):
		value = float(self.textY3.text())
		step = float(self.textStep2_b.toPlainText())
		self.textY3.setText(str(value - step))

		self.RegionChanged()

	def ybutton23Clicked(self):
		value = float(self.textY3.text())
		step = float(self.textStep2_b.toPlainText())
		self.textY3.setText(str(value + step))

		self.RegionChanged()

	def zbutton13Clicked(self):
		value = float(self.textZ3.text())
		step = float(self.textStep2_b.toPlainText())
		self.textZ3.setText(str(value - step))

		self.RegionChanged()

	def zbutton23Clicked(self):
		value = float(self.textZ3.text())
		step = float(self.textStep2_b.toPlainText())
		self.textZ3.setText(str(value + step))

		self.RegionChanged()

	def centerradioClicked(self):
		self.center = "center"

	def pointradioClicked(self):
		self.center = "point"

	def tab3UI(self):

		self.radio1 = QtWidgets.QRadioButton("About Center")
		self.radio2 = QtWidgets.QRadioButton("About Point")
		self.radio1.setChecked(True)
		self.centerMode = "center"

		self.radio1.clicked.connect(self.centerradioClicked)
		self.radio2.clicked.connect(self.pointradioClicked)

		buttonsLayout = QtWidgets.QHBoxLayout()
		self.a1 = QtWidgets.QLineEdit()
		self.a1.setFixedSize(100, 25)
		self.a2 = QtWidgets.QLineEdit()
		self.a2.setFixedSize(100, 25)
		self.a3 = QtWidgets.QLineEdit()
		self.a3.setFixedSize(100, 25)
		buttonsLayout.addWidget(self.a1)
		buttonsLayout.addWidget(self.a2)
		buttonsLayout.addWidget(self.a3)

		##
		labelStep = QtWidgets.QLabel("Step value:")
		self.textStep_o = QtWidgets.QPlainTextEdit()
		self.textStep_o.setFixedSize(75, 25)
		self.textStep_o.setPlainText("1.0")
		stepLayout = QtWidgets.QGridLayout()
		stepLayout.addWidget(labelStep, 0 , 6, 1, 1)
		stepLayout.addWidget(self.textStep_o, 0 , 9, 1, 1)

		##
		labelX = QtWidgets.QLabel("Omega:")
		self.textX_o = QtWidgets.QLineEdit()
		self.textX_o.setFixedSize(55, 25)
		self.xbutton1_o = QtWidgets.QPushButton("<")
		self.xbutton1_o.setFixedSize(25, 25)
		self.slx_o = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.slx_o.setMinimum(10)
		self.slx_o.setMaximum(30)
		self.slx_o.setValue(20)
		self.slx_o.setTickInterval(5)
		self.xbutton2_o = QtWidgets.QPushButton(">")
		self.xbutton2_o.setFixedSize(25, 25)

		__groupBoxLayout = QtWidgets.QGridLayout()
		__groupBoxLayout.addWidget(labelX, 0, 0, 1, 1)
		__groupBoxLayout.addWidget(self.textX_o, 0, 2, 1, 1)
		__groupBoxLayout.addWidget(self.xbutton1_o, 0, 3, 1, 1)
		__groupBoxLayout.addWidget(self.slx_o, 0, 4, 1, 1)
		__groupBoxLayout.addWidget(self.xbutton2_o, 0, 6, 1, 1)
		##

		##
		labelY = QtWidgets.QLabel("Phi:")
		self.textY_o = QtWidgets.QLineEdit()
		self.textY_o.setFixedSize(55, 25)
		self.ybutton1_o = QtWidgets.QPushButton("<")
		self.ybutton1_o.setFixedSize(25, 25)
		self.sly_o = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.sly_o.setMinimum(10)
		self.sly_o.setMaximum(30)
		self.sly_o.setValue(20)
		self.sly_o.setTickInterval(5)
		self.ybutton2_o = QtWidgets.QPushButton(">")
		self.ybutton2_o.setFixedSize(25, 25)

		__groupBoxLayout.addWidget(labelY, 1, 0, 1, 1)
		__groupBoxLayout.addWidget(self.textY_o, 1, 2, 1, 1)
		__groupBoxLayout.addWidget(self.ybutton1_o, 1, 3, 1, 1)
		__groupBoxLayout.addWidget(self.sly_o, 1, 4, 1, 1)
		__groupBoxLayout.addWidget(self.ybutton2_o, 1, 6, 1, 1)
		##

		##
		labelZ = QtWidgets.QLabel("Kappa:")
		self.textZ_o = QtWidgets.QLineEdit()
		self.textZ_o.setFixedSize(55, 25)
		self.zbutton1_o = QtWidgets.QPushButton("<")
		self.zbutton1_o.setFixedSize(25, 25)
		self.slz_o = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.slz_o.setMinimum(10)
		self.slz_o.setMaximum(30)
		self.slz_o.setValue(20)
		self.slz_o.setTickInterval(5)
		self.zbutton2_o = QtWidgets.QPushButton(">")
		self.zbutton2_o.setFixedSize(25, 25)

		__groupBoxLayout.addWidget(labelZ, 2, 0, 1, 1)
		__groupBoxLayout.addWidget(self.textZ_o, 2, 2, 1, 1)
		__groupBoxLayout.addWidget(self.zbutton1_o, 2, 3, 1, 1)
		__groupBoxLayout.addWidget(self.slz_o, 2, 4, 1, 1)
		__groupBoxLayout.addWidget(self.zbutton2_o, 2, 6, 1, 1)
		##

		gridLayout = QtWidgets.QVBoxLayout()
		gridLayout.addLayout( stepLayout )
		gridLayout.addLayout( __groupBoxLayout )

		layout = QtWidgets.QGridLayout()
		layout.addWidget(self.radio1, 0 , 0, 1, 1)
		layout.addWidget(self.radio2, 3 , 0, 1, 1)
		layout.addLayout(buttonsLayout, 4, 0, 1, 1)
		layout.addLayout(gridLayout, 5, 0, 1, 1)

		groupBoxRotateView = QtWidgets.QGroupBox(self.tr("Rotate Object"))
		groupBoxRotateView.setLayout( layout )

		self.o_a11 = QtWidgets.QLineEdit()
		self.o_a11.setFixedSize(75, 25)
		self.o_a12 = QtWidgets.QLineEdit()
		self.o_a12.setFixedSize(75, 25)
		self.o_a13 = QtWidgets.QLineEdit()
		self.o_a13.setFixedSize(75, 25)
		self.o_a14 = QtWidgets.QLineEdit()
		self.o_a14.setFixedSize(75, 25)

		self.o_a21 = QtWidgets.QLineEdit()
		self.o_a21.setFixedSize(75, 25)
		self.o_a22 = QtWidgets.QLineEdit()
		self.o_a22.setFixedSize(75, 25)
		self.o_a23 = QtWidgets.QLineEdit()
		self.o_a23.setFixedSize(75, 25)
		self.o_a24 = QtWidgets.QLineEdit()
		self.o_a24.setFixedSize(75, 25)

		self.o_a31 = QtWidgets.QLineEdit()
		self.o_a31.setFixedSize(75, 25)
		self.o_a32 = QtWidgets.QLineEdit()
		self.o_a32.setFixedSize(75, 25)
		self.o_a33 = QtWidgets.QLineEdit()
		self.o_a33.setFixedSize(75, 25)
		self.o_a34 = QtWidgets.QLineEdit()
		self.o_a34.setFixedSize(75, 25)

		self.o_a41 = QtWidgets.QLineEdit()
		self.o_a41.setFixedSize(75, 25)
		self.o_a42 = QtWidgets.QLineEdit()
		self.o_a42.setFixedSize(75, 25)
		self.o_a43 = QtWidgets.QLineEdit()
		self.o_a43.setFixedSize(75, 25)
		self.o_a44 = QtWidgets.QLineEdit()
		self.o_a44.setFixedSize(75, 25)

		layout3 = QtWidgets.QGridLayout()
		layout3.addWidget(self.o_a11, 0, 0, 1, 1)
		layout3.addWidget(self.o_a12, 0, 1, 1, 1)
		layout3.addWidget(self.o_a13, 0, 2, 1, 1)
		layout3.addWidget(self.o_a14, 0, 3, 1, 1)
		layout3.addWidget(self.o_a21, 1, 0, 1, 1)
		layout3.addWidget(self.o_a22, 1, 1, 1, 1)
		layout3.addWidget(self.o_a23, 1, 2, 1, 1)
		layout3.addWidget(self.o_a24, 1, 3, 1, 1)
		layout3.addWidget(self.o_a31, 2, 0, 1, 1)
		layout3.addWidget(self.o_a32, 2, 1, 1, 1)
		layout3.addWidget(self.o_a33, 2, 2, 1, 1)
		layout3.addWidget(self.o_a34, 2, 3, 1, 1)
		layout3.addWidget(self.o_a41, 3, 0, 1, 1)
		layout3.addWidget(self.o_a42, 3, 1, 1, 1)
		layout3.addWidget(self.o_a43, 3, 2, 1, 1)
		layout3.addWidget(self.o_a44, 3, 3, 1, 1)

		groupBoxCurrentMatrix = QtWidgets.QGroupBox(self.tr("Current Matrix"))
		groupBoxCurrentMatrix.setLayout( layout3 )

		self.matrixButton = QtWidgets.QPushButton("Load Matrix from File")
		self.applyButton = QtWidgets.QPushButton("Apply")
		buttonLayout2 = QtWidgets.QHBoxLayout()
		buttonLayout2.addWidget( self.matrixButton )
		buttonLayout2.addWidget( self.applyButton )
		
		self.matrixButton.clicked.connect(self.buttonmatrixClicked)
		self.applyButton.clicked.connect(self.buttonapplyClicked)

		resetButton3 = QtWidgets.QPushButton("Reset Transform to Ground Control Values")
		buttonLayout1 = QtWidgets.QHBoxLayout()
		buttonLayout1.addWidget( resetButton3 )

		resetButton3.setEnabled(False)

		layout1 = QtWidgets.QVBoxLayout()
		layout1.addLayout( buttonLayout1 ) 

		internalLayout = QtWidgets.QVBoxLayout()
		internalLayout.addWidget( groupBoxRotateView )
		internalLayout.addStretch(1)
		internalLayout.addWidget( groupBoxCurrentMatrix )
		internalLayout.addStretch(1)
		internalLayout.addLayout( buttonLayout2 )
		internalLayout.addStretch(1)
		internalLayout.addLayout( layout1 )

		self.__tab3.setLayout( internalLayout )

		# Events
		self.slx_o.valueChanged.connect(self.sliderchangedX)
		self.sly_o.valueChanged.connect(self.sliderchangedY)
		self.slz_o.valueChanged.connect(self.sliderchangedZ)

		self.xbutton1_o.clicked.connect(self.xbutton1Clicked)
		self.xbutton2_o.clicked.connect(self.xbutton2Clicked)
		self.ybutton1_o.clicked.connect(self.ybutton1Clicked)
		self.ybutton2_o.clicked.connect(self.ybutton2Clicked)
		self.zbutton1_o.clicked.connect(self.zbutton1Clicked)
		self.zbutton2_o.clicked.connect(self.zbutton2Clicked)

		self.timedTask = False
		self.xbutton1_o.pressed.connect(self.xbutton1Pressed)
		self.xbutton1_o.released.connect(self.xbutton1Released)
		self.xbutton2_o.pressed.connect(self.xbutton2Pressed)
		self.xbutton2_o.released.connect(self.xbutton2Released)
		self.ybutton1_o.pressed.connect(self.ybutton1Pressed)
		self.ybutton1_o.released.connect(self.ybutton1Released)
		self.ybutton2_o.pressed.connect(self.ybutton2Pressed)
		self.ybutton2_o.released.connect(self.ybutton2Released)
		self.zbutton1_o.pressed.connect(self.zbutton1Pressed)
		self.zbutton1_o.released.connect(self.zbutton1Released)
		self.zbutton2_o.pressed.connect(self.zbutton2Pressed)
		self.zbutton2_o.released.connect(self.zbutton2Released)

		self.textX_o.returnPressed.connect(self.omegaTextChanged)
		self.textY_o.returnPressed.connect(self.phiTextChanged)
		self.textZ_o.returnPressed.connect(self.kappaTextChanged)


	def showDialog(self):
		msgBox = QtWidgets.QMessageBox()
		msgBox.setText("Warning!.")
		msgBox.setInformativeText("This transformation reset the model coordinates. Are you sure?")
		msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
		msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
		retval = msgBox.exec_()
		return retval

	def objectClicked(self):
		if self.modeobject:
			self.mode = "object"
		else :
			retval = self.showDialog()

			if retval == QtWidgets.QMessageBox.Ok:
				self.mode = "object"
				self.modeobject = True
			else:
				if self.mode == "xyz":	
					self.__tabWidget.setCurrentWidget(self.__tab1)
				else :
					self.__tabWidget.setCurrentWidget(self.__tab2)

		return True

	def buttonmatrixClicked(self):
		#print("Button Matrix")

		fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', 'c:\\',"Matrix files (*.txt *.csv *.py)")
		if (fname[0]):
			name = fname[0]
			w, h = 4,4;
			Matrix = [[0 for x in range(w)] for y in range(h)]

			fila, col = 0,0
			try:
				lines = [line.rstrip('\n') for line in open(name)]
				for l in lines:
					if (l[:3] != 'VER' and l[:3] != 'MAT'):
						n = l.split(' ')
						numbers = []
						for elem in n:
							if (elem != ''):
								Matrix[fila][col] = float(elem)
								col = col + 1
						fila = fila +1
						col = 0
			except:
				msgBox = QtWidgets.QMessageBox()
				msgBox.setText("Warning!.")
				msgBox.setInformativeText("Failed open Matrix file. Test if format is valid.")
				msgBox.exec_()
			else:
				#print (Matrix)

				self.o_a11.setText( "{:.5f}".format(Matrix[0][0]) )
				self.o_a12.setText( "{:.5f}".format(Matrix[0][1]) )
				self.o_a13.setText( "{:.5f}".format(Matrix[0][2]) )
				self.o_a14.setText( "{:.5f}".format(Matrix[0][3]) )

				self.o_a21.setText( "{:.5f}".format(Matrix[1][0]) )
				self.o_a22.setText( "{:.5f}".format(Matrix[1][1]) )
				self.o_a23.setText( "{:.5f}".format(Matrix[1][2]) )
				self.o_a24.setText( "{:.5f}".format(Matrix[1][3]) )

				self.o_a31.setText( "{:.5f}".format(Matrix[2][0]) )
				self.o_a32.setText( "{:.5f}".format(Matrix[2][1]) )
				self.o_a33.setText( "{:.5f}".format(Matrix[2][2]) )
				self.o_a34.setText( "{:.5f}".format(Matrix[2][3]) )

				self.o_a41.setText( "{:.5f}".format(Matrix[3][0]) )
				self.o_a42.setText( "{:.5f}".format(Matrix[3][1]) )
				self.o_a43.setText( "{:.5f}".format(Matrix[3][2]) )
				self.o_a44.setText( "{:.5f}".format(Matrix[3][3]) )

		return True

	def buttonapplyClicked(self):
		self.centerMode = "matrix"

		R = PhotoScan.Matrix( [ 
			 [float(self.o_a11.Text()), float(self.o_a12.Text()), float(self.o_a13.Text())],
			 [float(self.o_a21.Text()), float(self.o_a22.Text()), float(self.o_a23.Text())],
			 [float(self.o_a31.Text()), float(self.o_a32.Text()), float(self.o_a33.Text())]
			] )

		self.omega, self.phi, self.kappa = PhotoScan.utils.mat2opk(R) #current OPK

		self.transform()
		self.getTransformMatrix()

	def orthoButtonClicked(self):
		PhotoScan.app.model_view.viewpoint.fov = 0.0

	def perspButtonClicked(self):
		PhotoScan.app.model_view.viewpoint.fov = 30.0

		return True

def main():

	global doc
	doc = PhotoScan.app.document
	app = QtWidgets.QApplication.instance()
	parent = app.activeWindow()
	dlg = GeoBitTransformDialog(parent)

PhotoScan.app.addMenuItem("Helpers/Geobit Transform", main)
