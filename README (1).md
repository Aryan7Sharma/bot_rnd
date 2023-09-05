# Step for running this code

### Step 1: Install Python 3.6 or 3.7

1.1. Check Python Version: First, check if Python 3.6 or 3.7 is already installed on your system by running:

```bash
python3.6 --version
# OR
python3.7 --version
```
Install Python: If Python 3.6 or 3.7 is not installed, you can download and install it from the official Python website: https://www.python.org/downloads/

### Step 2: Create a Virtual Environment

2.1. Install Virtualenv (if not already installed): You can install virtualenv using pip, the Python package manager, by running:

```bash
pip install virtualenv
```

#### 2.2. Create a Virtual Environment: Navigate to the directory where you want to create your virtual environment and run:

```bash
python3.6 -m venv venv_name  # For Python 3.6
# OR
python3.7 -m venv venv_name  # For Python 3.7
```

### Step 3: Activate the Virtual Environment

#### 3.1. On Linux:

```bash
source venv_name/bin/activate  # For Any Python Version
```


### Step 4: Install NLTK and TensorFlow

#### 4.1. Install NLTK:

```bash
pip install nltk
```

#### 4.2. Install TensorFlow:

```bash
pip install tensorflow
```

### Step 5: Run Your Python Script

#### 5.1. Navigate to Your Script's Directory: Use the cd command to navigate to the directory where your Python script (scriptname.py) is located.

#### 5.2. Run Your Script: Execute your Python script using the following command:


#### 5.3 Run the Command for rule based basic chat bot in your terminal go to the directory where ist located cd /bots then run the script

```bash
python3 staticmodel1.py
```

#### 5.3 Run the Command for running simple dynamic chat bot in your terminal go to the directory where ist located cd /bots then run the script

```bash
python3 dynamic1.py
```


### Step 6: Deactivate the Virtual Environment

#### 6.1. When you're done with your work, deactivate the virtual environment by running the following command:

```bash
deactivate
```

This will return you to your system's global Python environment.





