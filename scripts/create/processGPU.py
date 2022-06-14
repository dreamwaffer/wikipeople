import constants
from create import utils, setupGPU, faceDetector
import os

def detectFacesJob():
    """This method detects all the faces in database. Checks for the processedImages.json file
       and uses it, if found.

       Keyword arguments:
        None
    """
    setupGPU.config()
    step = 5
    # TODO requestem stahnout proccessedImages z githubu
    if os.path.exists(f'{constants.DATA_DIRECTORY}/processedImages.json'):
        processedImages = utils.readData(f'{constants.DATA_DIRECTORY}/processedImages.json')
    else:
        processedImages = {}
    for year in range(constants.START_YEAR, constants.END_YEAR, step):
        print(f'Starting years: {year}, {year + step}!')
        data = utils.readData(f'{constants.DATA_DIRECTORY}/{year}_{year + step}.json')
        processedImages, data = faceDetector.detectFaces(data, processedImages)
        utils.saveData(data, f'{constants.DATA_DIRECTORY}/{year}_{year + step}.json')
        utils.saveData(processedImages, f'{constants.DATA_DIRECTORY}/processedImages.json')


if __name__ == '__main__':
    detectFacesJob()