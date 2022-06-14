import logging
import os
from PIL import ExifTags, Image
from tqdm import tqdm
import random

from constants import START_YEAR, END_YEAR, IMAGES_DIRECTORY, DATASET_DIRECTORY, DATA_DIRECTORY, IMAGES_SIZE, YEAR_STEP, \
    BANNED_EXTENSIONS
from create.merger import mergeDatasets
from create.utils import readData, countProperty, saveData


def filterData(data, properties=None):
    if properties is None:
        properties = {}

    result = {}

    dataList = [{property: person[property] for property in properties.keys()} for person in list(data.values()) if
                all(property in person.keys() for property in list(properties.keys()))]
    # return createDictionaryFromList(dataList)

    # for person in tqdm(data.values(), desc='filterData', miniters=int(len(data) / 100)):
    #     for property in person.keys():
    #         if property in properties.keys():


def createDictionaryFromList(dataList):
    result = {}
    for person in dataList:
        result[person['wikidataID']] = person

    return result


def filterDataset(data):
    counter = 1
    limit = 10000
    genders = {'male': 0, 'female': 0}

    result = {}

    for person in tqdm(list(data.values()), desc='filterDataset', miniters=int(len(data) / 100)):
        for image in list(person['images'].values()):
            if counter > limit:
                return result
            # error on pillow side - segmentation fault (https://github.com/python-pillow/Pillow/pull/4033)
            if os.path.splitext(image['fileNameLocal'])[1].lower() not in ['.tif', '.tiff']:
                if 'age' in image and image['age'] is not None and 5 < image['age'] < 100:
                    if 'faces' in image and len(image['faces']) == 1:
                        if 'gender' in person and len(person['gender']) == 1 and person['gender'][0] in ['male',
                                                                                                         'female']:
                            gender = person['gender'][0]
                            if genders[gender] < limit / 2:
                                genders[gender] += 1
                                counter += 1
                                if person['wikidataID'] not in result:
                                    del person['images']
                                    person['images'] = {}
                                    person['images'][image['fileNameWiki']] = image
                                    result[person['wikidataID']] = person
                                else:
                                    result[person['wikidataID']]['images'][image['fileNameWiki']] = image
    return result


def createImgDirAndCSV(data):
    pictureInDir = IMAGES_DIRECTORY
    pictureOutDir = DATASET_DIRECTORY
    peopleCSV = f'{DATASET_DIRECTORY}/people.csv'
    counter = 1
    result = {}

    with open(peopleCSV, 'w') as f:
        for person in tqdm(data.values(), desc='createImgDirAndCSV', miniters=int(len(data) / 100)):
            for image in person['images'].values():
                extension = os.path.splitext(image["fileNameWiki"])[1]
                gender = 0 if person['gender'][0] == 'male' else 1
                f.write(f'{image["age"]},{gender}\n')
                result[person['wikidataID']] = person
                transformImage(f'{pictureInDir}/{image["fileNameLocal"]}',
                               f'{pictureOutDir}/{str(counter).zfill(7)}{extension}', image['faces'][0]['box'], 256)
                counter += 1


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


def shuffleDataset(data):
    l = list(data.items())
    random.shuffle(l)
    data = dict(l)
    return data


def creatingDatasetJob():
    data = {}
    for year in range(START_YEAR, END_YEAR, YEAR_STEP):
        print(f'Starting years: {year}, {year + YEAR_STEP}!')
        partData = readData(f'{DATA_DIRECTORY}/{year}_{year + YEAR_STEP}.json')
        data = mergeDatasets([data, partData])

    print(len(data))
    data = shuffleDataset(data)
    data = filterDataset(data)
    data = shuffleDataset(data)
    print(len(data))
    countProperty(data, {'images': True})
    saveData(data, f'{DATASET_DIRECTORY}/people.json')
    # data = readData(f'{constants.DATA_DIRECTORY}/people.json')
    createImgDirAndCSV(data)


def createDirsGender(data, property, classes, index):
    stats = {item: 0 for item in classes}

    for image in tqdm(data, desc=f'createDirs-{index}', miniters=int(len(data) / 100)):
        extension = os.path.splitext(image['fileNameLocal'])[1]
        if extension not in BANNED_EXTENSIONS:
            if property in image:
                # gender property is a list as some people can identify as multi-gender
                # next line filters out people with different gender than male or female
                image[property] = [x for x in image[property] if x in classes]
                if len(image[property]) == 1:
                    image[property] = image[property][0]
                    transformImage(f'{IMAGES_DIRECTORY}/{image["fileNameLocal"]}',
                                   f'{DATASET_DIRECTORY}/{image[property]}/{image["fileNameLocal"]}',
                                   image['faces'][0]['box'], IMAGES_SIZE)
                    stats[image[property]] += 1

    return stats


def createDirsGenderAge(data, classes, index):
    # classes = ['male,10', 'female,10',
    #            'male,20', 'female,20',
    #            'male,30', 'female,30',
    #            'male,40', 'female,40',
    #            'male,50', 'female,50',
    #            'male,60', 'female,60',
    #            'male,70', 'female,70',
    #            'male,80', 'female,80',
    #            'male,90', 'female,90',
    #            'male,100', 'female,100',
    #           ]
    stats = {item: 0 for item in classes}

    for image in tqdm(data, desc=f'createDirs-{index}', miniters=int(len(data) / 100)):
        extension = os.path.splitext(image['fileNameLocal'])[1]
        if extension not in BANNED_EXTENSIONS:
            if 'gender' in image and 'age' in image:
                # gender property is a list as some people can identify as multi-gender
                # next line filters out people with different gender than male or female
                image['gender'] = [x for x in image['gender'] if x in ['male', 'female']]
                # this check: 0 < image['age'] < 100 is already in the dataset, but I was not sure
                # if I ran it with the last version, so just to be sure
                if image['age'] is not None and 0 < image['age'] < 100 and len(image['gender']) == 1:
                    image['gender'] = image['gender'][0]
                    if image['age'] < 33: image['age'] = 'young'
                    elif 33 <= image['age'] < 66: image['age'] = 'adult'
                    elif 66 <= image['age'] < 100: image['age'] = 'old'
                    image['genderAge'] = f"{image['gender']},{image['age']}"
                    transformImage(f'{IMAGES_DIRECTORY}/{image["fileNameLocal"]}',
                                   f'{DATASET_DIRECTORY}/{image["genderAge"]}/{image["fileNameLocal"]}',
                                   image['faces'][0]['box'], IMAGES_SIZE)
                    stats[image['genderAge']] += 1

    return stats


def main():
    creatingDatasetJob()


if __name__ == '__main__':
    pass
