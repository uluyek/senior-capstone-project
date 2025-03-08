  # Keyu Lu - Medical Imaging Visualization Tool
  
  This application provides a sophisticated platform for the visualization and analysis of medical imaging data. Designed to assist medical professionals, researchers, and educators, it leverages the Visualization Toolkit (VTK) for high-quality imaging capabilities.
  ### Main Features
  
  #### Medical Imaging Display

  The core of this application is its ability to render medical images with exceptional detail. It can display DICOM datasets, which are the standard for handling, storing, processing, and transmitting information in medical imaging. The rendering engine ensures that users can view these images in their full resolution, offering a true representation of the scanned data for accurate interpretation.
  
  #### Annotation
  
  Understanding that communication is vital in medical imaging, I have included an annotation feature in this application. Users can mark specific areas on the medical images and add descriptive notes. This feature facilitates the sharing of findings and is especially useful for teaching purposes, providing a platform for insightful discussion on particular aspects of the imaging data.
  
  #### Slice View
  
  The slice view functionality allows users to interactively cut through the 3D volume data along arbitrary planes, offering a multi-dimensional perspective of the internal anatomy. This feature is invaluable for exploring complex structures and identifying pathologies that may be hidden in a single plane of view.
  
  #### Bounding Box
  The bounding box tool offers users the ability to focus on a particular area of interest within a 3D volume. By selecting a specific region, users can isolate and investigate a segment of the image, enhancing the visibility of smaller, detailed structures without the distraction of surrounding data.
  
  #### Advanced Denoising Pipeline
  Image quality is paramount for accurate diagnosis and analysis. The denoising pipeline I developed combines median filtering with anisotropic diffusion filtering to reduce noise while preserving critical structural details. This results in clearer and more reliable images, aiding in the detection and diagnosis of medical conditions.
  ![Denoising Pipeline](https://github.com/uluyek/senior-capstone-project/blob/main/image/Denoising%20Pipeline.jpg)

  ### Denoiser Result with Different Parameters
  #### Base Setting
  Median Filter Kernel Size: 5, Anisotropic Diffusion Iteration: 5, Sharpening Filter Strength: 5
  ![](https://github.com/uluyek/senior-capstone-project/blob/main/image/555%20proof.jpg)

  #### Setting 1
  Median Filter Kernel Size: 9, Anisotropic Diffusion Iteration: 5, Sharpening Filter Strength: 5
  ![](https://github.com/uluyek/senior-capstone-project/blob/main/image/9%205%205%20demo.jpg)

  #### Setting 2
  Median Filter Kernel Size: 5, Anisotropic Diffusion Iteration: 10, Sharpening Filter Strength: 5
  ![](https://github.com/uluyek/senior-capstone-project/blob/main/image/5%2010%205%20proof%20with%208%20and%200.8.jpg)

  #### Setting 3
  Median Filter Kernel Size: 5, Anisotropic Diffusion Iteration: 5, Sharpening Filter Strength: 10
  ![](https://github.com/uluyek/senior-capstone-project/blob/main/image/55%2010%20demo.jpg)

  #### Ideal Setting 3
  Median Filter Kernel Size: 7, Anisotropic Diffusion Iteration: 10, Sharpening Filter Strength: 5
  ![](https://github.com/uluyek/senior-capstone-project/blob/main/image/ideal%20view.jpg)
  
  #### Initial Approach (Simple Gaussian Blur)
  ![](https://github.com/uluyek/senior-capstone-project/blob/main/image/simple%20guassian%20blur.jpg)


  ### Demo for all other main features
  
  ![](https://github.com/uluyek/senior-capstone-project/blob/main/Other%20Features.gif)
