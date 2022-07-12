import logging
import os
import random
import shutil

from PIL import Image, ExifTags
from tqdm import tqdm

import constants
from create.merger import mergeAllDataForTraining, mergeAllDataForTrainingAge, mergeAllDataForTrainingGender


def toImagesAge(dir):
    files = os.listdir(dir)
    images = []
    for image in tqdm(files, desc=f'toImagesAge', miniters=int(len(files) / 100)):
        name = os.path.splitext(image)[0]
        _, _, age, gender = name.split('_')
        imageObject = {
            'age': int(age),
            'fileNameLocal': image,
        }
        if 17 <= imageObject['age'] <= 80:
            images.append(imageObject)

    return images


def toImagesGender(dir):
    files = os.listdir(dir)
    images = []
    for image in tqdm(files, desc=f'toImagesGender', miniters=int(len(files) / 100)):
        name = os.path.splitext(image)[0]
        _, _, age, gender = name.split('_')
        imageObject = {
            'gender': 'male' if gender == 'm' else 'female',
            'fileNameLocal': image,
        }
        images.append(imageObject)

    return images


def createDirectoriesForAge():
    classes = [i for i in range(17, 81)]
    dirs = [
        f'{constants.DATASET_DIRECTORY}/age',
        f'{constants.DATASET_DIRECTORY}/age/eval',
        f'{constants.DATASET_DIRECTORY}/age/eval/test',
        f'{constants.DATASET_DIRECTORY}/age/eval/val',
        f'{constants.DATASET_DIRECTORY}/age/0',
        f'{constants.DATASET_DIRECTORY}/age/0/train'
    ]
    for dir in dirs:
        if not os.path.exists(dir):
            os.makedirs(dir)
    for item in classes:
        os.makedirs(f'{constants.DATASET_DIRECTORY}/age/eval/test/{item}')
        os.makedirs(f'{constants.DATASET_DIRECTORY}/age/eval/val/{item}')
        os.makedirs(f'{constants.DATASET_DIRECTORY}/age/0/train/{item}')

    # ageDB part - ageDB is used in:
    # - train/directory 0
    # - val
    # - test

    data = toImagesAge(constants.AGE_DB_IMAGES_DIRECTORY)
    random.shuffle(data)
    split = {
        'train': int(len(data) * constants.TRAIN),
        'val': int(len(data) * constants.VAL),
        'test': int(len(data) * constants.TEST)
    }
    lengthAgeDB = len(data)
    print(f"number of people from ageDB: {lengthAgeDB}")

    for part, number in tqdm(split.items(), desc=f'create directories for age from AgeDB'):
        for j in range(number):
            image = data.pop()
            fromLocation = f"{constants.AGE_DB_IMAGES_DIRECTORY}/{image['fileNameLocal']}"
            if part in ['val', 'test']:
                toLocation = f"{constants.DATASET_DIRECTORY}/age/eval/{part}/{image['age']}/{image['fileNameLocal']}"
            else:
                toLocation = f"{constants.DATASET_DIRECTORY}/age/0/{part}/{image['age']}/{image['fileNameLocal']}"
            shutil.copyfile(fromLocation, toLocation)

    # my dataset part - used in:
    # - directory 1-n
    data = mergeAllDataForTrainingAge()
    amount = [1000, 10000, 100000, len(data)]
    datasets = [random.sample(data, number) for number in amount[:-1]]
    datasets.append(data)
    for i, data in tqdm(enumerate(datasets), desc="create directories for age from my dataset"):
        srcDir = f"{constants.DATASET_DIRECTORY}/age/0"
        destDir = f"{constants.DATASET_DIRECTORY}/age/{i + 1}"
        shutil.copytree(srcDir, destDir)
        for image in list(data):
            fromLocation = f"{constants.DATASET_DIRECTORY}/transformedImages/{image['fileNameLocal']}"
            toLocation = f"{constants.DATASET_DIRECTORY}/age/{i + 1}/train/{image['age']}/{image['fileNameLocal']}"
            if os.path.exists(fromLocation) and not os.path.exists(toLocation):
                shutil.copyfile(fromLocation, toLocation)


def createDirectoriesForGender():
    classes = ['male', 'female']
    dirs = [
        f'{constants.DATASET_DIRECTORY}/gender',
        f'{constants.DATASET_DIRECTORY}/gender/eval',
        f'{constants.DATASET_DIRECTORY}/gender/eval/test',
        f'{constants.DATASET_DIRECTORY}/gender/eval/val',
        f'{constants.DATASET_DIRECTORY}/gender/0',
        f'{constants.DATASET_DIRECTORY}/gender/0/train'
    ]
    for dir in dirs:
        if not os.path.exists(dir):
            os.makedirs(dir)
    for item in classes:
        os.makedirs(f'{constants.DATASET_DIRECTORY}/gender/eval/test/{item}')
        os.makedirs(f'{constants.DATASET_DIRECTORY}/gender/eval/val/{item}')
        os.makedirs(f'{constants.DATASET_DIRECTORY}/gender/0/train/{item}')

    # ageDB part - ageDB is used in:
    # - train/directory 0
    # - val
    # - test

    data = toImagesGender(constants.AGE_DB_IMAGES_DIRECTORY)
    random.shuffle(data)
    split = {
        'train': int(len(data) * constants.TRAIN),
        'val': int(len(data) * constants.VAL),
        'test': int(len(data) * constants.TEST)
    }
    lengthAgeDB = len(data)
    print(f"number of people from ageDB: {lengthAgeDB}")

    for part, number in tqdm(split.items(), desc=f'create directories for age from AgeDB'):
        for j in range(number):
            image = data.pop()
            fromLocation = f"{constants.AGE_DB_IMAGES_DIRECTORY}/{image['fileNameLocal']}"
            if part in ['val', 'test']:
                toLocation = f"{constants.DATASET_DIRECTORY}/gender/eval/{part}/{image['gender']}/{image['fileNameLocal']}"
            else:
                toLocation = f"{constants.DATASET_DIRECTORY}/gender/0/{part}/{image['gender']}/{image['fileNameLocal']}"
            shutil.copyfile(fromLocation, toLocation)

    # my dataset part - used in:
    # - directory 1-n

    data = mergeAllDataForTrainingGender()
    amount = [1000, 10000, 100000, len(data)]
    datasets = [random.sample(data, number) for number in amount[:-1]]
    datasets.append(data)
    for i, data in tqdm(enumerate(datasets), desc="create directories for age from my dataset"):
        srcDir = f"{constants.DATASET_DIRECTORY}/gender/0"
        destDir = f"{constants.DATASET_DIRECTORY}/gender/{i + 1}"
        shutil.copytree(srcDir, destDir)
        for image in data:
            fromLocation = f"{constants.DATASET_DIRECTORY}/transformedImages/{image['fileNameLocal']}"
            toLocation = f"{constants.DATASET_DIRECTORY}/gender/{i + 1}/train/{image['gender'][0]}/{image['fileNameLocal']}"
            if os.path.exists(fromLocation) and not os.path.exists(toLocation):
                shutil.copyfile(fromLocation, toLocation)


def transformAllPics():
    if not os.path.exists(f"{constants.DATASET_DIRECTORY}/transformedImages"):
        os.makedirs(f"{constants.DATASET_DIRECTORY}/transformedImages")
    data = mergeAllDataForTraining()
    print(len(data))
    for image in tqdm(list(data), desc="transform all images for training"):
        toLocation = f"{constants.DATASET_DIRECTORY}/transformedImages/{image['fileNameLocal']}"
        if not os.path.exists(toLocation):
            fromLocation = f"{constants.IMAGES_DIRECTORY}/{image['fileNameLocal']}"
            transformImage(fromLocation,
                           toLocation,
                           image['faces'][0]['box'], constants.IMAGES_SIZE)
        else:
            data.remove(image)


def transformImage(inLocation, outLocation, box, size):
    try:
        with Image.open(inLocation) as img:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = img._getexif()
            if exif is not None and orientation in exif:
                if exif[orientation] == 3:
                    img = img.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    img = img.rotate(270, expand=True)
                elif exif[orientation] == 8:
                    img = img.rotate(90, expand=True)

            cropped = img.crop(box)

            resized = cropped.resize((size, size), Image.ANTIALIAS)
            # resized = cropped.resize((size, size), Resampling.LANCZOS)
            resized.save(outLocation)
    except Exception as e:
        print(f'Corrupted picture {inLocation} - {e}')
        logging.error(f'Corrupted picture {inLocation} - {e}')


if __name__ == '__main__':
    transformAllPics()
    createDirectoriesForAge()
    createDirectoriesForGender()