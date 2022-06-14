from tqdm import tqdm
import constants
import logging
import os
from retinaface import RetinaFace

def detectFacesWithHashing(data, processedImages=None):
    """This method detects faces in images in dataset. There is a limitation on images' extensions.

        Keyword arguments:
        data -- processed data from sparql endpoint
        processedImages -- dictionary of images that was already processed with face detection (default: None)
    """

    if processedImages is None:
        processedImages = {}

    for index, person in enumerate(
            tqdm(data.values(), desc='detectFaces', miniters=int(len(data) / 100))):
        for image in person['images'].values():
            if image['fileNameWiki'] not in processedImages:
                if os.path.splitext(image["fileNameLocal"])[1] in constants.ALLOWED_EXTENSIONS:
                    if 'faces' not in image:
                        logging.info(f'Image {image["fileNameWiki"]} not found in dictionary')
                        try:
                            processedImages[image['fileNameWiki']] = detectFacesInImage(image)
                        except Exception as e:
                            logging.exception(f'Exception happened in {image["fileNameWiki"]} from {person["wikidataID"]}')
                            # logging.error(e)
                    elif image['fileNameWiki'] not in processedImages:
                        processedImages[image['fileNameWiki']] = image['faces']
            else:
                image['faces'] = processedImages[image['fileNameWiki']]


    return processedImages, data




def detectFaces(data, processedImages=None):
    """This method detects faces in images in dataset. There is a limitation on images' extensions.

        Keyword arguments:
        data -- processed data from sparql endpoint
        processedImages -- dictionary of images that was already processed with face detection (default: None)
    """

    if processedImages is None:
        processedImages = {}

    for index, person in enumerate(
            tqdm(data.values(), desc='detectFaces', miniters=int(len(data) / 100))):
        for image in person['images'].values():
            if image['fileNameWiki'] not in processedImages:
                if os.path.splitext(image["fileNameLocal"])[1] in constants.ALLOWED_EXTENSIONS:
                    if 'faces' not in image:
                        logging.info(f'Image {image["fileNameWiki"]} not found in dictionary')
                        try:
                            processedImages[image['fileNameWiki']] = detectFacesInImage(image)
                        except Exception as e:
                            logging.exception(f'Exception happened in {image["fileNameWiki"]} from {person["wikidataID"]}')
                            # logging.error(e)
                    # TODO this next line is duplicate - remove it and make it simpler!
                    elif image['fileNameWiki'] not in processedImages:
                        processedImages[image['fileNameWiki']] = image['faces']
            else:
                image['faces'] = processedImages[image['fileNameWiki']]


    return processedImages, data


def detectFacesInImage(image):
    """This method detects faces in one specific image.
       TODO mention what is the structure of box, how box is defined

        Keyword arguments:
        image -- image from dataset to find faces in
    """

    location = f'{constants.IMAGES_DIRECTORY}/{image["fileNameLocal"]}'
    # necessary check, broken images are deleted, so not all people have one donwloaded
    if os.path.exists(location):
        faces = RetinaFace.detect_faces(location)
        # Retina face returns tuple if no face is found
        if (isinstance(faces, dict)):
            # Removes keys that are not needed
            faces = [{key: face[key] for key in ['facial_area', 'score']} for face in faces.values()]
            for face in faces:
                x1, y1, x2, y2 = [int(value) for value in face['facial_area']]
                width = x2 - x1
                height = y2 - y1
                longerSide = max(width, height) * constants.FACE_BOX_MULTIPLIER
                x = x1 - (longerSide - width) / 2
                y = y1 - (longerSide - height) / 2
                box = [x, y, x + longerSide, y + longerSide]
                box[:] = [int(number) for number in box]
                face['box'] = box
                face['score'] = float(face['score'])
                del face['facial_area']
            image['faces'] = faces
        else:
            image['faces'] = []

    return image['faces']

