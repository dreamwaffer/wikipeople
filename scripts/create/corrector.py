# Module name: Corrector
# Purpose: This module contains functions to check and remove broken images in the dataset.

import logging
import os

import cv2
from tqdm import tqdm
from PIL import Image

from constants import ALLOWED_EXTENSIONS, IMAGES_DIRECTORY


def removeBrokenImages(data):
    """This method removes broken images in passed dataset. Broken images are images that cannot be opened
       or worked with packages Pillow or cv2.

        Keyword arguments:
        data -- processed data from sparql endpoint
    """
    for person in tqdm(list(data.values()), desc='removeBrokenImages', miniters=int(len(data) / 100)):
        if 'images' in person:
            for image in list(person['images'].values()):
                if os.path.exists(f'{IMAGES_DIRECTORY}/{image["fileNameLocal"]}'):
                    if isImageBroken(f'{IMAGES_DIRECTORY}/{image["fileNameLocal"]}'):
                        logging.info(f'Removing image - {image["fileNameLocal"]} because it is broken')
                        print(f'Removing image - {image["fileNameLocal"]} because it is broken')
                        del person['images'][image['fileNameWiki']]
                        os.remove(f'{IMAGES_DIRECTORY}/{image["fileNameLocal"]}')
                else:
                    logging.info(f'Removing image - {image["fileNameLocal"]} because it does not exists')
                    print(f'Removing image - {image["fileNameLocal"]} because it does not exists')
                    del person['images'][image['fileNameWiki']]

    return data


def isImageBroken(location):
    """This method checks if image is broken by trying to open it and performing some basic transposition
       with Pillow package. The image is also verified with package cv2.

        Keyword arguments:
        location -- location of a specific image
    """
    extension = os.path.splitext(location)[1]
    # PIL does not work with all formats (e.g., svg), so I am only checking those I can work with tensorflow
    if extension in ALLOWED_EXTENSIONS:
        try:
            with Image.open(location) as im:
                im.verify()

            with Image.open(location) as im:
                # TODO Image.Transpose.FLIP... does not exist prior Pillow 9.1.0, check your version
                # Otherwise all you pics might get deleted
                # im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)  # Pillow 9.1.0 and above
                im.transpose(Image.ROTATE_90) # Anything below Pillow 9.1.0

            # Potential test if retina-face is able to open the image.
            im = cv2.imread(location)
            test = im.shape

        # PIL cannot read big tiff files and raises this error, for keeping the code simple we can just consider
        # that file correct by skipping all .tif and .tiff
        # https://stackoverflow.com/questions/48944819/image-open-gives-error-cannot-identify-image-file

        except Exception as e:
            logging.exception(f'Exception happened while checking image {location}')
            return True
    return False