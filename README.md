
# Wikipeople  
This project was part of diploma thesis created in 2021/2022 summer semester on CTU FEE. Its main focus is on creating big database of facial pictures annotated with multiple attributes. The most important attribute is the age of a person in an image, but the created dataset comes with other attributes related to the person such as birth date, death date, gender, occupation, and so on. The created dataset can be used in wide variety of machine learning tasks (age, gender or general attribute prediction).
  
This project uses Wikimedia API excessively to access a lot of information. The author is aware of all API Etiquette rules, which are mentioned [here](https://www.mediawiki.org/wiki/API:Etiquette) and tries to follow them, but please notify the author on kotrblu2@fel.cvut.cz if you think the project is doing something it should not.
## About the project
All the information about the created project, how it works, what is the final structure as well as statistics of created datasets can be found in [written thesis](https://dspace.cvut.cz/bitstream/handle/10467/103677/F3-DP-2022-Kotrbaty-Lukas-Database_of_personal_web_pages_from_Wikipedia.pdf).

### Structure of the project
- Directory scripts contains:
    - module constants.py with definition of all constants used in this project.
    - package create, which contains source code divided into modules, which is capable of building the dataset.
    - package eval and model are used only for statistical evaluation and include code snippets used for:
        - generating all the statistics over Wikipeople and Wikifaces datasets.
        - transforming all images into smaller dimension.
        - creating dataset Wikifaces, which is used for ML training.
        - generating sample for manual evaluation.
        - checking results of face detection.
- File requierementsCPU.txt contains required modules needed for the data collection part of the dataset creation process.
- File requierements.txt contains required modules needed for both the data collection part and face detection part of the dataset creation process.
  
## How to use this project  
Only tested with Python 3.10, but everything above Python 3.9 should work. The dictionary union operator (|) is used couple of times.  
* Clone this repo  
```  
git clone https://github.com/dreamwaffer/wikipeople.git  
cd wikipeople/  
```  
- Install all required packages  
  - Only the data collection part without face detection:  
	```
	pip install -r requirementsCPU.txt
	```
  - The whole process (data collection and face detection):  
	```
	pip install -r requirements.txt
	```
- Add modules to PYTHONPATH, most IDEs do this automatically, when using python in terminal run:  
```  
export PYTHONPATH="${PYTHONPATH}:FullPathToTheScriptsDir"  
```  
- Check your Pillow version. If it is anything below Pillow 9.1.0, than check line 53 in module corrector in package create.
  - on linux run: 
	```  
	pip list | grep "Pillow"
	```  
  - on windows run: 
	```  
	pip list | findstr "Pillow"
	```  
- Change your email in constants.HEADER, this header is used in all API calls and with proper header your request will not be banned. If you leave the original email there it might get banned if someone is using it at the same time.
- Check the directories to save your database in constants.DATA_DIRECTORY and constants.IMAGES_DIRECTORY.  
- Set desired start and end year for the script in constants.START_YEAR and constants.END_YEAR.  
- Run dataCollectionProcess for creating of database.
```  
cd scripts/create  
python dataCollectionProcess.py  
```  
- After processCPU is done download the processedImages.json from this [link](https://drive.google.com/file/d/14cwCIZTupPD0LFlhmlPVCgJvOyUo3FoE/view?usp=sharing). This file contains bounding boxes for faces in images that have already been put through face detection.   
- Place downloaded JSON file into your constants.DATA_DIRECTORY.  
- Run faceDetectionProcess for face detection (you can omit first two steps in case you are using different face detection settings, but mind that the process will quite likely run much longer).  
```  
cd scripts/create  
python faceDetectionProcess.py  
```
## Debugging of data collection process
It is important to remember that Wikipedia is a live site, so its data are added and edited every minute. This can be observed for example with this live [tool ](http://listen.hatnote.com/). This constantly changing nature can introduce a lot of unexpected errors. They can be prevented, but the complexity would be much complicated, because of the compounded try-catch clauses. To keep the script simple, solution of these unexpected errors was omitted and the work was focused on script robustness instead. 
So, the adopted approach is just rerunning the script from the year that was not successfully processed. Therefore check the process every now and then and in case you find it crashed do this:
- go to the logs directory and open errors.log
- scroll down to see the last year which was successfully processed. It should look something like this:
	```
	2022-08-09 17:54:17.175 INFO dataCollectionProcess - fullDataDownload: Year 1877 was completed!
	```
	This means that year 1877 was successfuly processed and something went wrong whilst processing the year 1878.
- change the constants.START_YEAR to the year you found in previous step.
- rerun the dataCollectionProcess.

If you discover a different error please consider contributing or raising an issue.
