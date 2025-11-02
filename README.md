# GUI Installation Guide + Dataset Card

-------------------------------------------------------------

# Office Item Classifier GUI 

For this project pyside6 was used due to its performance level which allows efficient rendering of video frames and overlays. It is easy to create complex interfaces with detection logs, confidence scores, and control panels. It works consistently on Windows, Linux, and macOS.

To install the necessary libraries and packages needed/required for the running of Office Item Classifier GUI, Follow these instructions:

# 1. Download folder(zipped file of Project folder R2D2_Robotics_CW  and unzip it)
# 2. Open the folder using PyCharm-IDE (Preferably)
# 3. Add a new Python (preferable PyCharm - IDE) Interpreter version 3.12 (compatible with the Libraries/packages) in the root folder (a virtual environment folder(.venv) will be created in the root directory)

**After adding the virtual environment, the hierarchy should look like this:**

R2D2_Robotics_CW
│
├── .venv/                                 
│
├── Office-Item-classifier/
│   ├── trained_model/
│   │   └── best.pt
│   │
│   ├── ui/
│   │   ├── main_window.py
│   │
│   │─ camera_handler.py
│   │─ file_processor.py
│   │─ main.py
│   │─ model_loader.py
│   │─ requirements.txt                   
│   └── README.md                               
│ 
└─────────────────────────────

<p align="center">
  <img src="folder structure.jpg" width="400">
</p>

<pre> ```text R2D2_Robotics_CW │ ├── .venv/ │ ├── Office-Item-classifier/ │ ├── trained_model/ │ │ └── best.pt │ │ │ ├── ui/ │ │ └── main_window.py │ │ │ ├── camera_handler.py │ ├── file_processor.py │ ├── main.py │ ├── model_loader.py │ ├── requirements.txt │ └── README.md │ └───────────────────────────── ``` </pre>

# 4. Activate the newly created virtual environment for windows:

**.venv/Scripts/activate**

# 5. Open the folder  Office-Item-Classifier :

**cd Office-Item-Classifier**

# 6. Install all the libraries in requirements.txt file for the GUI to run, the downloads keep on running in the background (might take some time):

**pip install -r requirements.txt**

# 7. Starting the GUI program:

**Run main.py**
---------------------------------------------------------------------------