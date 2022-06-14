import os
import random
import shutil

from PIL import Image
from tqdm import tqdm

from constants import DATASET_DIRECTORY, AGE_DB_IMAGES_DIRECTORY, IMAGES_SIZE, TRAIN, VAL, TEST
from model.datasetCreator import transformImage
from create.setupCPU import config


def toImages(dir):
    files = os.listdir(dir)
    images = []
    for image in tqdm(files, desc=f'toImages', miniters=int(len(files) / 100)):
        name = os.path.splitext(image)[0]
        _, _, age, gender = name.split('_')
        im = Image.open(f'{dir}/{image}')
        width, height = im.size
        shorterSide = min(width, height)
        imageObject = {
            'age': int(age),
            'gender': 'male' if gender == 'm' else 'female',
            'fileNameLocal': image,
            'box': [0, 0, shorterSide, shorterSide]
        }
        images.append(imageObject)

    return images


def createDirsGenderAgeCD(data, classes, index):
    stats = {item: 0 for item in classes}

    for image in tqdm(data, desc=f'createDirs-{index}', miniters=int(len(data) / 100)):
        if image['age'] < 33:
            image['age'] = 'young'
        elif 33 <= image['age'] < 66:
            image['age'] = 'adult'
        elif image['age'] >= 66:
            image['age'] = 'old'
        image['genderAge'] = f"{image['gender']},{image['age']}"
        transformImage(f'{AGE_DB_IMAGES_DIRECTORY}/{image["fileNameLocal"]}',
                       f'{DATASET_DIRECTORY}/{image["genderAge"]}/{image["fileNameLocal"]}',
                       image['box'], IMAGES_SIZE)
        stats[image['genderAge']] += 1

    return stats


def trainValTestSplitMin(number):
    inDataset = DATASET_DIRECTORY
    outDataset = '../controlDatasetSplit'

    # inDataset = '/datagrid/personal/kotrblu2/1/genderAge'
    # outDataset = '/datagrid/personal/kotrblu2/1/genderAgeSplit'
    classes = os.listdir(inDataset)
    directories = []
    directories.extend([f'{outDataset}/train/{item}' for item in classes])
    directories.extend([f'{outDataset}/val/{item}' for item in classes])
    directories.extend([f'{outDataset}/test/{item}' for item in classes])
    files = []
    split = {
        'train': 0,
        'val': 0,
        'test': 0
    }

    # create fileLists and shuffle them
    for item in classes:
        itemFiles = os.listdir(f'{inDataset}/{item}')
        random.shuffle(itemFiles)
        files.append(itemFiles)

    # check if all directories exists or create them
    for dir in directories:
        if not os.path.exists(dir):
            os.makedirs(dir)

    split['train'] = int(number * TRAIN)
    split['val'] = int(number * VAL)
    split['test'] = int(number * TEST)

    for part, numFiles in split.items():
        for i in tqdm(range(numFiles), desc=f'trainValTestSplit-{part}', miniters=int(numFiles / 100)):
            # for i in range(train):
            for j, itemFiles in enumerate(files):
                image = itemFiles[i]
                shutil.copyfile(f'{inDataset}/{classes[j]}/{image}', f'{outDataset}/{part}/{classes[j]}/{image}')


def trainValTestSplitAll():
    inDataset = DATASET_DIRECTORY
    outDataset = '../controlDatasetSplit'

    # inDataset = '/datagrid/personal/kotrblu2/1/genderAge'
    # outDataset = '/datagrid/personal/kotrblu2/1/genderAgeSplit'
    classes = os.listdir(inDataset)
    directories = []
    directories.extend([f'{outDataset}/train/{item}' for item in classes])
    directories.extend([f'{outDataset}/val/{item}' for item in classes])
    directories.extend([f'{outDataset}/test/{item}' for item in classes])
    files = []
    split = {
        'train': 0,
        'val': 0,
        'test': 0
    }
    result = {
        'train': {k: 0 for k in classes},
        'val': {k: 0 for k in classes},
        'test': {k: 0 for k in classes}
    }

    # create fileLists and shuffle them
    for item in classes:
        itemFiles = os.listdir(f'{inDataset}/{item}')
        print(f'{inDataset}/{item}: {str(len(itemFiles))}')
        random.shuffle(itemFiles)
        files.append(itemFiles)

    # check if all directories exists or create them
    for dir in directories:
        if not os.path.exists(dir):
            os.makedirs(dir)

    split['train'] = TRAIN
    split['val'] = VAL
    split['test'] = TEST

    startIndices = [0] * len(classes)

    for part, multiplier in tqdm(split.items(), desc=f'controlDatasetSplitAll'):
        for i, item in enumerate(classes):
            number = int(len(files[i]) * multiplier)
            for j in range(number):
                image = files[i][startIndices[i] + j]
                shutil.copyfile(f'{inDataset}/{classes[i]}/{image}', f'{outDataset}/{part}/{classes[i]}/{image}')
                result[part][item] += 1
            startIndices[i] += number

    return result


if __name__ == '__main__':
    config()
    # stats = {}
    # classes = ['male,young', 'female,young', 'male,adult', 'female,adult', 'male,old', 'female,old']
    #
    # for item in classes:
    #     if not os.path.exists(f'{DATASET_DIRECTORY}/{item}'):
    #         os.makedirs(f'{DATASET_DIRECTORY}/{item}')

    # data = toImages(AGE_DB_IMAGES_DIRECTORY)
    # data = readData('../data/controlDataset.json')
    # stats = createDirsGenderAgeCD(data, classes, 1)
    # print(stats)
    # createStatsAgeCD(data, f'{STATS_DIRECTORY}/age.png')
    # createStatsGenderCD(data, f'{STATS_DIRECTORY}/gender.png')
    # saveData(data, '../data/controlDataset.json')

    stats = trainValTestSplitAll()
    print(stats)

    # print(json.dumps(data, ensure_ascii=False, indent=2))
