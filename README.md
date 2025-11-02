# GUI Installation Guide + Dataset Card
Team members:
Dhruv Ramachundrah (M01012616)
Dylan Iyasawmy (M01013579) 
Aayush Lochun (M01004726)
-------------------------------------------------------------

# Office Item Classifier GUI 

For this project pyside6 was used due to its performance level which allows efficient rendering of video frames and overlays. It is easy to create complex interfaces with detection logs, confidence scores, and control panels. It works consistently on Windows, Linux, and macOS.

To install the necessary libraries and packages needed/required for the running of Office Item Classifier GUI, Follow these instructions:

## 1. Download folder(zipped file of Project folder R2D2_Robotics_CW  and unzip it or clone the github repository in a new folder)
## 2. Open the folder using PyCharm-IDE (Preferably)
## 3. Add a new Python (preferable PyCharm - IDE) Interpreter version 3.12 (compatible with the Libraries/packages) in the root folder (a virtual environment folder(.venv) will be created in the root directory)

**After adding the virtual environment, the hierarchy should look like this:**


<p align="center">
  <img src="folder structure.jpg" width="400">
</p>



## 4. Activate the newly created virtual environment for windows:

**.venv/Scripts/activate**

## 5. Open the folder  Office-Item-Classifier :

**cd Office-Item-Classifier**

## 6. Install all the libraries in requirements.txt file for the GUI to run, the downloads keep on running in the background (indexing) - Might take some time:

**pip install -r requirements.txt**

## 7. Starting the GUI program:

**Run main.py**

After the program has been run, it will generate 3 folders: 

input, output and snapshots

input folder-  Images can be saved to upload for detection and classification
output folder- All the images detected will be saved
snapshots folder- Snapshots will be saved from live camera
---------------------------------------------------------------------------

# **Dataset card**

Link to the Roboflow dataset: **https://app.roboflow.com/dhruvs-dataset-kszei/project-1-0-2-htazc/browse?queryText=&pageSize=50&startingIndex=0&browseQuery=true**

This dataset consists of 10 classes of items which are commonly found in an office. The number of images per class are listed below: 
1. Pen (513)
2. Mouse (214)
3. Keyboard (162)
4. Phone (254)
5. Bottle (201)
6. Mug (332)
7. Stapler (235)
8. Laptop (219)
9. Bin (119)
10. Notebook (359)

The total number of images in the dataset is 1506 images. It provides an appropriate amout of data for a proper YOLO model to be trained. 

The code for training the model can be found in the Model Training Code directory, which must be opened ideally in Google Colab, and the best model is saved as best.pt in the trained model directory. It is used for object classifications by the GUI.

