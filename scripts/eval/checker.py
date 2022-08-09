import constants
import utils

def checkFaceDetection(data):
    facesCount = 0
    bannedCount = 0
    allCount = 0
    for person in data.values():
        for image in person['images'].values():
            allCount += 1
            if image['extension'] not in constants.ALLOWED_EXTENSIONS:
                bannedCount +=1
            else:
                if 'faces' in image:
                    facesCount += 1

    print(f'Detected faces: {facesCount}')
    print(f'Banned faces: {bannedCount}')
    print(f'All images: {allCount}')

def countFaces(image, stats):
    if 'faces' in image:
        numberOfFaces = str(len(image['faces']))
        if numberOfFaces in stats:
            stats[numberOfFaces] += 1
        else:
            stats[numberOfFaces] = 1

def checkFaces(data):
    faces = {}
    for person in data.values():
        for image in person['images'].values():
            countFaces(image, faces)
    total = utils.countProperty(data, {'images': True})['images']
    print(f"{sum(faces.values())}/{total}")
    return sum(faces.values()), total

if __name__ == '__main__':
    data = utils.readData(f'{constants.DATA_DIRECTORY}/1840.json')
    for person in data.values():
        for image in person['images'].values():
            if 'faces' not in image and image['extension'] != '.gif':
                print(person['wikidataID'])