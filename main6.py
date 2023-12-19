import sys
import os
import shutil
import tempfile
import numpy
import vtk
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QWidget, QSlider, QPushButton, QHBoxLayout, QInputDialog, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit 
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk import vtkImageAnisotropicDiffusion3D, vtkImageMedian3D, vtkImageConvolve

class ClickInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, parent=None):
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)

        self.parent = parent  # store the parent (i.e., MainWindow) to call its methods.

    def leftButtonPressEvent(self, obj, event):
        if self.parent.annotate_mode:  # Check if annotate_mode is True
            click_pos = self.GetInteractor().GetEventPosition()
            self.parent.add_annotation_at_position(click_pos)
            self.parent.annotate_mode = False  # Reset the annotate_mode to False
        else:
            # Normal behavior
            self.OnLeftButtonDown()

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        # Initialize the annotate mode flag
        self.annotate_mode = False
        self.box_widget = None 
        self.bounding_box_threshold = 10  # Set the default value or any other value you prefer

        #Initiliaze the slice_actor
        self.slice_actor = None

        # GUI setup
        self.frame = QFrame(self)
        self.vl = QVBoxLayout()
        self.hl = QHBoxLayout()
        self.create_filter_controls()

        # Initialize filters
        self.medianFilter = vtkImageMedian3D()  # Median filter
        self.anisotropicDiffusionFilter = vtkImageAnisotropicDiffusion3D()  # Anisotropic diffusion filter
        self.sharpeningFilter = vtkImageConvolve()  # Sharpening filter

        # Bounding Box Width Slider
        self.bounding_box_width_slider = QSlider(Qt.Horizontal, self.frame)
        self.bounding_box_width_slider.setMinimum(1)
        self.bounding_box_width_slider.setMaximum(100)  # Adjust max value as needed
        self.bounding_box_width_slider.setValue(10)  # Default value
        self.bounding_box_width_slider.setTickPosition(QSlider.TicksBelow)
        self.bounding_box_width_slider.setTickInterval(5)
        self.bounding_box_width_slider.valueChanged.connect(self.onBoundingBoxWidthChanged)
        self.vl.addWidget(self.bounding_box_width_slider)

        # VTK Setup
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.vl.addWidget(self.vtkWidget)
        
        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Click Interactor Style Setup
        self.click_interactor_style = ClickInteractorStyle(parent=self)
        self.click_interactor_style.SetDefaultRenderer(self.ren)
        self.iren.SetInteractorStyle(self.click_interactor_style)

        # Load DICOM Data
        self.volume_mapper = self.loadDICOM("C:\\Users\\HP\\Desktop\\DICOM DataSet\\Circle of Willis")

        # Box Widget Setup
        self.init_box_widget()

        # Button to Display Slice View
        self.display_slice_button = QPushButton("Display Slice View", self.frame)
        self.display_slice_button.clicked.connect(self.onDisplaySliceClicked)
        self.hl.addWidget(self.display_slice_button)

        # Add Toggle View Button
        self.toggle_view_button = QPushButton("Toggle View", self.frame)
        self.toggle_view_button.clicked.connect(self.toggle_view)
        self.hl.addWidget(self.toggle_view_button)
        # Attribute to store the current view state
        self.is_slice_view = False
        # Add Annotation Button
        self.add_annotation_button = QPushButton("Add Annotation", self.frame)
        self.add_annotation_button.clicked.connect(self.add_annotation)
        self.hl.addWidget(self.add_annotation_button)

        # Finalize GUI Setup
        self.vl.addLayout(self.hl)
        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)

        # Annotations storage
        self.annotations = []

        # Display the main window
        self.show()

        # Initialize the interactor
        self.iren.Initialize()

    def create_filter_controls(self):
        # Label and Input for Median Filter Kernel Size
        self.medianKernelLabel = QLabel("Median Filter Kernel Size:")
        self.vl.addWidget(self.medianKernelLabel)
        
        self.medianKernelInput = QLineEdit(self.frame)
        self.medianKernelInput.setText("1")  # Default value
        self.medianKernelInput.editingFinished.connect(self.onMedianKernelChanged)
        self.vl.addWidget(self.medianKernelInput)

        # Label and Input for Anisotropic Diffusion Iterations
        self.anisoIterationsLabel = QLabel("Anisotropic Diffusion Iterations:")
        self.vl.addWidget(self.anisoIterationsLabel)
        
        self.anisoIterationsInput = QLineEdit(self.frame)
        self.anisoIterationsInput.setText("1")  # Default value
        self.anisoIterationsInput.editingFinished.connect(self.onAnisoIterationsChanged)
        self.vl.addWidget(self.anisoIterationsInput)

        # Label and Input for Sharpening Filter Strength
        self.sharpeningStrengthLabel = QLabel("Sharpening Filter Strength:")
        self.vl.addWidget(self.sharpeningStrengthLabel)
        
        self.sharpeningStrengthInput = QLineEdit(self.frame)
        self.sharpeningStrengthInput.setText("3")  # Default value
        self.sharpeningStrengthInput.editingFinished.connect(self.onSharpeningStrengthChanged)
        self.vl.addWidget(self.sharpeningStrengthInput)

    def onMedianKernelChanged(self):
        value = int(self.medianKernelInput.text())  # Get the value from the input
        if value % 2 == 0:  # Ensure the kernel size is odd
            value += 1
        self.medianKernelLabel.setText(f"Median Filter Kernel Size: {value}")
        self.medianFilter.SetKernelSize(value, value, value)
        self.medianFilter.Update()
        self.updateVTKPipeline()

    def onAnisoIterationsChanged(self):
        value = int(self.anisoIterationsInput.text())  # Get the value from the input
        self.anisoIterationsLabel.setText(f"Anisotropic Diffusion Iterations: {value}")
        self.anisotropicDiffusionFilter.SetNumberOfIterations(value)
        self.anisotropicDiffusionFilter.Update()
        self.updateVTKPipeline()

    def onSharpeningStrengthChanged(self):
        value = float(self.sharpeningStrengthInput.text())  # Get the value from the input
        self.sharpeningStrengthLabel.setText(f"Sharpening Filter Strength: {value}")
        # Example: Adjust kernel based on strength value
        kernel_strength = value  # Adjust this formula as needed
        kernel = [0, -kernel_strength, 0, -kernel_strength, 1 + 4 * kernel_strength, -kernel_strength, 0, -kernel_strength, 0]
        self.sharpeningFilter.SetKernel3x3(kernel)
        self.sharpeningFilter.Update()
        self.updateVTKPipeline()


    def updateVTKPipeline(self):
        # Update the VTK pipeline and re-render the image
        self.volumeMapper.Update()
        self.vtkWidget.GetRenderWindow().Render()


# Initialize the filter control sliders in the __init__ method

    def toggle_view(self):
        # Toggle only the visibility of the slice_actor
        if self.slice_actor:
            self.slice_actor.SetVisibility(not self.slice_actor.GetVisibility())
            text = "Hide Slice View" if self.slice_actor.GetVisibility() else "Show Slice View"
            self.toggle_view_button.setText(text)
        else:
            # If there is no slice_actor, create and show it
            self.show_slice_view()
        self.vtkWidget.GetRenderWindow().Render()

    def show_slice_view(self):
        if not self.slice_actor:
            # Create the slice view if it doesn't exist
            transform = vtk.vtkTransform()
            self.box_widget.GetTransform(transform)
            plane = self.get_slicing_plane(transform)
            self.slice_volume(plane)  # This will create the slice_actor
            self.ren.AddActor2D(self.slice_actor)  # Add the slice actor to the renderer
        else:
            # If the slice actor exists, make sure it's visible
            self.slice_actor.SetVisibility(True)

        # The slice view should be on top of the volume rendering
        self.slice_actor.SetPosition(0, 0, 0)
        self.ren.ResetCamera()
        self.toggle_view_button.setText("Hide Slice View")

    def show_model_view(self):
        # Make sure the model view is always visible
        self.volume.SetVisibility(True)

        # If the slice_actor exists, hide it without deleting
        if self.slice_actor:
            self.slice_actor.SetVisibility(False)
        self.toggle_view_button.setText("Show Slice View")
        self.ren.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()

    def init_box_widget(self):
        self.box_widget = vtk.vtkBoxWidget()
        self.box_widget.SetInteractor(self.iren)
        self.box_widget.SetPlaceFactor(1.0)
        self.box_widget.PlaceWidget(self.volume_mapper.GetBounds())
        self.box_widget.InsideOutOn()
        self.box_widget.AddObserver("StartInteractionEvent", self.start_interaction)
        self.box_widget.AddObserver("InteractionEvent", self.interaction)
        self.box_widget.AddObserver("EndInteractionEvent", self.end_interaction)
        self.box_widget.On()  # Enable the box widget


    def start_interaction(self, obj, event):
        pass

    def interaction(self, obj, event):
        self.planes = vtk.vtkPlanes()
        obj.GetPlanes(self.planes)
        self.volume_mapper.SetClippingPlanes(self.planes)

    def end_interaction(self, obj, event):
        pass

    def loadDICOM(self, dicom_directory):
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()

        # Copy all .dcm files from the original directory to the temporary directory
        for filename in os.listdir(dicom_directory):
            if filename.lower().endswith(".dcm"):  # Ensuring we only copy .dcm files
                shutil.copy(os.path.join(dicom_directory, filename), temp_dir)

        # Create a reader for DICOM data
        reader = vtk.vtkDICOMImageReader()
        reader.SetDirectoryName(temp_dir)
        reader.Update()

        # Create a volume mapper
        self.volumeMapper = vtk.vtkSmartVolumeMapper()

        # Create a Median Filter for Pre-Filtering
        #self.medianFilter = vtk.vtkImageMedian3D()
        self.medianFilter.SetInputConnection(reader.GetOutputPort())
        self.medianFilter.SetKernelSize(3, 3, 3)  # Adjust these values as needed
        self.medianFilter.Update()

        # Apply the anisotropic diffusion filter to the image data
        # Apply the Anisotropic Diffusion Filter to the output of the Median Filter
        self.anisotropicDiffusionFilter.SetInputConnection(self.medianFilter.GetOutputPort())
        self.anisotropicDiffusionFilter.SetDiffusionFactor(1.0)  # Adjust as needed
        self.anisotropicDiffusionFilter.SetDiffusionThreshold(0.1)  # Adjust as needed
        self.anisotropicDiffusionFilter.SetNumberOfIterations(1)  # Adjust as needed
        self.anisotropicDiffusionFilter.Update()
        # Create a Sharpening Filter for Post-Processing
        self.sharpeningFilter.SetInputConnection(self.anisotropicDiffusionFilter.GetOutputPort())

        # Set up a sharpening kernel
        kernel = [0, -1, 0, -1, 5, -1, 0, -1, 0]
        self.sharpeningFilter.SetKernel3x3(kernel)
        self.sharpeningFilter.Update()

        # Set the volume mapper's input to the output of the sharpening filter
        self.volumeMapper.SetInputConnection(self.sharpeningFilter.GetOutputPort())

        # Update the rest of the pipeline to use the output of the diffusion filter
        #self.volumeMapper.SetInputConnection(self.anisotropicDiffusionFilter.GetOutputPort())

        # Create a volume
        self.volume = vtk.vtkVolume()
        self.volume.SetMapper(self.volumeMapper)

        # Set up the volume properties
        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.ShadeOn()
        volumeProperty.SetInterpolationTypeToLinear()

        # Set up the opacity transfer function
        opacityTransferFunction = vtk.vtkPiecewiseFunction()
        opacityTransferFunction.AddPoint(20, 0.0)
        opacityTransferFunction.AddPoint(255, 0.2)
        volumeProperty.SetScalarOpacity(opacityTransferFunction)

        # Set up the color transfer function
        colorTransferFunction = vtk.vtkColorTransferFunction()
        colorTransferFunction.AddRGBPoint(0, 0.0, 0.0, 0.0)
        colorTransferFunction.AddRGBPoint(64, 1.0, 0.0, 0.0)
        colorTransferFunction.AddRGBPoint(128, 0.0, 0.0, 1.0)
        colorTransferFunction.AddRGBPoint(192, 0.0, 1.0, 0.0)
        colorTransferFunction.AddRGBPoint(255, 0.0, 0.2, 0.0)
        volumeProperty.SetColor(colorTransferFunction)

        # Apply the properties to the volume
        self.volume.SetProperty(volumeProperty)

        # Add the volume to the renderer
        self.ren.AddVolume(self.volume)
        self.ren.ResetCamera()

        # Clean up temporary files
        shutil.rmtree(temp_dir, ignore_errors=True)

        return self.volumeMapper

    def onBoundingBoxWidthChanged(self, value):
        self.bounding_box_threshold = value

    def onDisplaySliceClicked(self):
        # Check if the box is planar according to the manually set threshold
        if self.is_box_planar():
            transform = vtk.vtkTransform()
            self.box_widget.GetTransform(transform)
            plane = self.get_slicing_plane(transform)
            self.slice_volume(plane)

    def is_box_planar(self):
        # Check if the box is small enough in one dimension to be considered planar
        # For the sake of this example, let's assume we've decided that if any side is
        # less than 10 units, we consider it a plane.
        bounds = [0]*6
        # Create a vtkPlanes object to store the planes of the box
        planes = vtk.vtkPlanes()
        # Get the planes from the box widget
        self.box_widget.GetPlanes(planes)
        return any(abs(bounds[i * 2 + 1] - bounds[i * 2]) < self.bounding_box_threshold for i in range(3))

    def get_slicing_plane(self, transform):
        # This method extracts the position and orientation of the box to create a plane
        plane = vtk.vtkPlane()
        
        # Obtain the origin (translation) from the transformation
        origin = [0, 0, 0]
        transformed_origin = [0, 0, 0]
        transform.TransformPoint(origin, transformed_origin)
        plane.SetOrigin(transformed_origin)
        
        # Extract the normal (z-direction) from the transformation matrix
        matrix = transform.GetMatrix()
        normal = [matrix.GetElement(0, 2), matrix.GetElement(1, 2), matrix.GetElement(2, 2)]
        plane.SetNormal(normal)
        
        return plane

    def slice_volume(self, plane):
        reslice = vtk.vtkImageReslice()
        # Set the input connection from the sharpening filter
        reslice.SetInputConnection(self.sharpeningFilter.GetOutputPort())

        normal = plane.GetNormal()

        # Calculate two vectors that are orthogonal to the plane's normal
        v1 = [0, 1, 0]
        if (normal[0] == 0 and normal[1] == 0):
            v1 = [1, 0, 0]

        v2 = numpy.cross(normal, v1)
        v1 = numpy.cross(v2, normal)

        # Normalize the vectors to get direction cosines
        v1 = v1 / numpy.linalg.norm(v1)
        v2 = v2 / numpy.linalg.norm(v2)
        normal = normal / numpy.linalg.norm(normal)

        reslice.SetResliceAxesDirectionCosines(list(v1), list(v2), list(normal))
        reslice.SetResliceAxesOrigin(plane.GetOrigin())

        # Set the output extent to the dimensions of the input data
        inputDimensions = self.anisotropicDiffusionFilter.GetOutput().GetDimensions()
        reslice.SetOutputExtent(0, inputDimensions[0]-1, 0, inputDimensions[1]-1, 0, 0)

        # Perform the reslice
        reslice.Update()

        if not self.slice_actor:
            # Create the slice_actor only if it does not exist
            slice_mapper = vtk.vtkImageMapper()
            slice_mapper.SetInputConnection(reslice.GetOutputPort())
            slice_mapper.SetColorWindow(255)
            slice_mapper.SetColorLevel(127.5)
            self.slice_actor = vtk.vtkActor2D()
            self.slice_actor.SetMapper(slice_mapper)
            # Add the slice actor to the renderer
            self.ren.AddActor2D(self.slice_actor)
        else:
            # If the slice_actor already exists, just update the input
            self.slice_actor.GetMapper().SetInputConnection(reslice.GetOutputPort())

        # Adjust the camera to center the slice view, only if slice view is being shown
        if self.is_slice_view:
            camera = self.ren.GetActiveCamera()
            camera.ParallelProjectionOn()
            width, height = inputDimensions[0], inputDimensions[1]
            camera.SetParallelScale(height / 2)
            center = [width / 2, height / 2, 0]
            camera.SetFocalPoint(center[0], center[1], center[2])
            camera.SetPosition(center[0], center[1], camera.GetPosition()[2])
            self.ren.ResetCameraClippingRange()

        # Render the updated scene
        self.vtkWidget.GetRenderWindow().Render()



    def add_annotation(self):
        # Get annotation text from user
        text, ok = QInputDialog.getText(self, 'Text Input Dialog', 'Enter your annotation:')
        
        if ok and text:
            self.annotation_text = text  # Store the user's text
            self.annotate_mode = True  # Set annotate_mode to True

    def add_annotation_at_position(self, position):
        # Check if the user entered text
        if hasattr(self, 'annotation_text') and self.annotation_text:
            text_to_display = self.annotation_text
            del self.annotation_text  # Clear it once displayed
        else:
            text_to_display = "Annotation"

        # Create an annotation
        textActor = vtk.vtkTextActor()
        textActor.SetInput(text_to_display)
        textActor.SetTextScaleMode(vtk.vtkTextActor.TEXT_SCALE_MODE_NONE)  # To prevent the text from being scaled
        textActor.GetTextProperty().SetColor(1.0, 0.0, 0.0)  # set color as red
        
        # Position text using screen coordinates
        textActor.SetPosition(position[0], position[1])

        # Add it to the renderer
        self.ren.AddActor2D(textActor)
        # Store it in the annotations list
        self.annotations.append(textActor)

        # Render the scene
        self.vtkWidget.GetRenderWindow().Render()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())  # Starts the Qt event loop