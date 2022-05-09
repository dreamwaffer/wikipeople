from PIL.Image import Resampling
from PIL import ExifTags
from modules.process import *



# TODO vytvorit skript na tvorbu datasetu a filtry

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
    pictureInDir = constants.IMAGES_DIRECTORY
    pictureOutDir = constants.DATASET_DIRECTORY
    peopleCSV = f'{constants.DATASET_DIRECTORY}/people.csv'
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
            resized = cropped.resize((size, size), Resampling.LANCZOS)
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
    config()
    step = 5
    data = {}
    for year in range(constants.START_YEAR, constants.END_YEAR, step):
        print(f'Starting years: {year}, {year + step}!')
        partData = readData(f'{constants.DATA_DIRECTORY}/{year}_{year + step}.json')
        data = mergeDatasets([data, partData])

    print(len(data))
    data = shuffleDataset(data)
    data = filterDataset(data)
    data = shuffleDataset(data)
    print(len(data))
    countProperty(data, {'images': True})
    saveData(data, f'{constants.DATASET_DIRECTORY}/people.json')
    # data = readData(f'{constants.DATA_DIRECTORY}/people.json')
    createImgDirAndCSV(data)


def main():
    creatingDatasetJob()


if __name__ == '__main__':
    main()
