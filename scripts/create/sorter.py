from collections import OrderedDict
from tqdm import tqdm
import constants


def orderData(data):
    """This method recursivelly orders data in dataset alphabetically. It is usually called before the method
       changeOrderOfProperties, because this method is used to sort mostly list of strings anywhere in the dataset.

        Keyword arguments:
        data -- any JSON, dictionary or list
    """

    if isinstance(data, dict):
        return dict(sorted((k, orderData(v)) for k, v in data.items()))
    if isinstance(data, list):
        # Necessary check, because faces data contains list of dictionaries, we need to distinguish between dicts
        # and normal values. Faces are compared by their confidence values.
        if data:
            if isinstance(data[0], dict):  # neseradim si nahodou hodnoty boxu?
                return list(sorted(data, key=lambda d: d['score']))
            else:
                return list(sorted(orderData(x) for x in data))
        else:
            return data
    else:
        return data


def changeOrderOfProperties(data):
    """This method reorders properties in dataset according to structure defined in constants.PERSON_STRUCTURE,
       constants.IMAGE_STRUCTURE and constants.FACE_STRUCTURE

        Keyword arguments:
        data -- processed data from sparql endpoint
    """
    for wikidataID, person in tqdm(data.items(), desc='changeOrderOfProperties', miniters=int(len(data) / 100)):
        orderedPerson = OrderedDict(
            (property, person[property]) for property in constants.PERSON_STRUCTURE if property in person)
        if 'images' in person:
            for fileName, image in person['images'].items():
                orderedImage = OrderedDict(
                    (property, image[property]) for property in constants.IMAGE_STRUCTURE if property in image)
                if 'faces' in image:
                    orderedImage['faces'] = []
                    for face in image['faces']:
                        orderedFace = OrderedDict(
                            (property, face[property]) for property in constants.FACE_STRUCTURE if property in face)
                        orderedImage['faces'].append(orderedFace)
                orderedPerson['images'][fileName] = orderedImage
        data[wikidataID] = orderedPerson
    return data