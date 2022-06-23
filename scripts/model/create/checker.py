from eval import stats
import utils

def checkFaces(data):
    faces = {}
    for person in data.values():
        for image in person['images'].values():
            stats.countFaces(image, faces)
    total = utils.countProperty(data, {'images': True})['images']
    print(f"{sum(faces.values())}/{total}")