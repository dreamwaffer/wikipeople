import checker
import constants
import downloader
from create import utils, setupGPU, faceDetector
import os

def detectFacesJob():
    """This method detects all the faces in database. Checks for the processedImages.json file
       and uses it, if found.

       Keyword arguments:
        None
    """
    detected = 0
    total = 0

    setupGPU.config()
    step = 1
    # TODO requestem stahnout proccessedImages z githubu
    if os.path.exists(f'{constants.DATA_DIRECTORY}/processedImages.json'):
        processedImages = utils.readData(f'{constants.DATA_DIRECTORY}/processedImages.json')
    else:
        processedImages = {}
    for year in range(constants.START_YEAR, constants.END_YEAR, step):
        print(f'Starting year: {year}!')
        data = utils.readData(f'{constants.DATA_DIRECTORY}/{year}.json')
        checker.checkFaces(data)
        processedImages, data = faceDetector.detectFacesWithHashing(data, processedImages)
        val = checker.checkFaces(data)
        detected += val[0]
        total += val[1]


        utils.saveData(data, f'{constants.DATA_DIRECTORY}/{year}.json')
        utils.saveData(processedImages, f'{constants.DATA_DIRECTORY}/processedImages.json')
    print(f"{detected}/{total}")


if __name__ == '__main__':
    detectFacesJob()

    # data = utils.readData(f'{constants.DATA_DIRECTORY}/short.json')
    # processedImages, data = faceDetector.detectFacesWithHashing(data, {})
    # utils.saveData(data, f'{constants.DATA_DIRECTORY}/short2.json')