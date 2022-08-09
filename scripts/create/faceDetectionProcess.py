# Module name: FaceDetectionProcess
# Purpose: This module contains main function for detecting faces in the dataset.

import os

from create.utils import readData, saveData
from create.faceDetectionSetup import config
from create.faceDetector import detectFaces
from eval.checker import checkFaceDetection, checkFaces
from constants import DATA_DIRECTORY, START_YEAR, END_YEAR, YEAR_STEP


def detectFacesJob():
    """This method detects all the faces in database. Checks for the processedImages.json file
       and uses it, if it is found.

       Keyword arguments:
        None
    """

    config()
    if os.path.exists(f'{DATA_DIRECTORY}/processedImages.json'):
        processedImages = readData(f'{DATA_DIRECTORY}/processedImages.json')
    else:
        processedImages = {}
    for year in range(START_YEAR, END_YEAR, YEAR_STEP):
        print(f'Starting year: {year}!')
        data = readData(f'{DATA_DIRECTORY}/{year}.json')
        checkFaceDetection(data)
        processedImages, data = detectFaces(data, processedImages)
        checkFaceDetection(data)

        saveData(data, f'{DATA_DIRECTORY}/{year}.json')
        saveData(processedImages, f'{DATA_DIRECTORY}/processedImages.json')

if __name__ == '__main__':
    detectFacesJob()