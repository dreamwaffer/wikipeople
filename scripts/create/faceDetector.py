# Module name: FaceDetector
# Purpose: This module contains functions to detect faces in images.

import logging
import os

from tqdm import tqdm
from retinaface import RetinaFace

from constants import FACE_BOX_MULTIPLIER, ALLOWED_EXTENSIONS


def detectFaces(data, processedImages=None):
    """This method detects faces in images in the passed dataset. There is a limitation on images' extensions.
       If processedImages dictionary is passed as well then before detecting faces the image is searched
       in the dictionary of images that have been already put through face detection.

        Keyword arguments:
        data -- processed data from sparql endpoint
        processedImages -- dictionary of images that was already processed with face detection (default: None)
    """

    if processedImages is None:
        processedImages = {}

    for index, person in enumerate(
            tqdm(data.values(), desc='detectFaces', miniters=int(len(data) / 100))):
        for image in person['images'].values():
            if image['fileNameLocal'] not in processedImages:
                if image['extension'] in ALLOWED_EXTENSIONS:
                    if 'faces' not in image:
                        try:
                            processedImages[image['fileNameLocal']] = detectFacesInImage(image)
                        except Exception as e:
                            logging.exception(
                                f'Exception happened in {image["fileNameWiki"]} from {person["wikidataID"]}')
                            # logging.error(e)
                    elif image['fileNameLocal'] not in processedImages:
                        processedImages[image['fileNameLocal']] = image['faces']
            else:
                image['faces'] = processedImages[image['fileNameLocal']]

    return processedImages, data


def detectFacesInImage(image):
    """This method detects faces in one specific image passed into the method. Detected faces are saved
       directly into the image which is part of the dataset being build. The structore of faces looks
       like this:

       "faces": [
          {                              - face 1
            "score": 0.9997634291648865, - probability of detected face being a real face
            "box": [                     - bounding box of the detected face
              296,                       - X coordinate of left top point of box
              189,                       - Y coordinate of left top point of box
              707,                       - X coordinate of right bottom point of box
              600                        - Y coordinate of right bottom point of box
            ]
          },
          {}                             - face 2
        ]

        Keyword arguments:
        image -- image from dataset to find faces in
    """

    location = f'{IMAGES_DIRECTORY}/{image["fileNameLocal"]}'
    # necessary check, broken images are deleted, so not all people have one downloaded
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
                longerSide = max(width, height) * FACE_BOX_MULTIPLIER
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