import os
import threading
from collections import Counter

from constants import START_YEAR, END_YEAR, YEAR_STEP, DATA_DIRECTORY, DATASET_DIRECTORY
# from corrector import removeBrokenImages
from model.datasetCreator import createDirsGender, createDirsGenderAge
# from setupGPU import config
from create.downloader import getPictures
from create.setupCPU import config
from create.transformer import toUsableImageData
from create.utils import readData

def procedureGender(start, results, index):
    data = readData(f'{DATA_DIRECTORY}/{start}_{start + YEAR_STEP}.json')
    data = toUsableImageData(data)
    results[index] = createDirsGender(data, 'gender', ['male', 'female'], index)

def genderJob():
    config()

    for item in ['male', 'female']:
        if not os.path.exists(f'{DATASET_DIRECTORY}/{item}'):
            os.makedirs(f'{DATASET_DIRECTORY}/{item}')

    stats = {}
    threads = [None] * 35
    results = [None] * 35
    for index, year in enumerate(range(START_YEAR, END_YEAR, YEAR_STEP)):
        t = threading.Thread(target=procedureGender, args=(year, results, index))
        threads[index] = t

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    for stat in results:
        stats = Counter(stats) + Counter(stat)

    print(stats)


def procedureGenderAge(start, results, classes, index):
    data = readData(f'{DATA_DIRECTORY}/{start}_{start + YEAR_STEP}.json')
    data = toUsableImageData(data)
    results[index] = createDirsGenderAge(data, classes, index)

def genderAgeJob():
    config()
    stats = {}
    classes = ['male,young', 'female,young', 'male,adult', 'female,adult', 'male,old', 'female,old']

    for item in classes:
        if not os.path.exists(f'{DATASET_DIRECTORY}/{item}'):
            os.makedirs(f'{DATASET_DIRECTORY}/{item}')

    stats = {}
    threads = [None] * 35
    results = [None] * 35
    for index, year in enumerate(range(START_YEAR, END_YEAR, YEAR_STEP)):
        t = threading.Thread(target=procedureGenderAge, args=(year, results, classes, index))
        threads[index] = t

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    for stat in results:
        stats = Counter(stats) + Counter(stat)

    print(stats)

if __name__ == '__main__':
    # genderAgeJob()

    config()
    stats = {}
    classes = ['male,young', 'female,young', 'male,adult', 'female,adult', 'male,old', 'female,old']

    for item in classes:
        if not os.path.exists(f'{DATASET_DIRECTORY}/{item}'):
            os.makedirs(f'{DATASET_DIRECTORY}/{item}')

    data = readData('../../data/subsetDataShort.json')
    data = getPictures(data)
    data = toUsableImageData(data)
    stats = createDirsGenderAge(data, classes, 1)

    print(stats)