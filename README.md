# Wikipeople
This is Diploma Thesis created in 2021/2022 summer semester. This work focus on creating big database of annotated pictures, which can be used to train AI models.

I am using Wikimedia API to access a lot of information. I am trying to follow all API Etiquette rules, which are mentioned [here](https://www.mediawiki.org/wiki/API:Etiquette), but please let me know if I am doing something I should not. 

kotrblu2@fel.cvut.cz

## How to use this project
Only tested with Python 3.10, but everything above Python 3.9 should work. The dictionary union operator (|) is used couple of times.
* Clone this repo
```
git clone https://github.com/dreamwaffer/wikipeople.git
cd wikipeople/
```
- Install all required packages
    - Only the CPU part - database creation without face detection:
    ```
    pip install -r requirementsCPU.txt
    ```
    - The whole process (CPU and GPU part):
    ```
    pip install -r requirements.txt
    ```
- Add modules to PYTHONPATH, most IDEs do this automatically, when using python in terminal run:
```
export PYTHONPATH="${PYTHONPATH}:FullPathToTheScriptsDir"
```
- Run processCPU.py for creating of database
```
cd scripts/create
python processCPU.py
```
- Run processGPU.py for face detection
```
cd scripts/create
python processGPU.py
```