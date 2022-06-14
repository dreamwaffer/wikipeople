import cv2
from tqdm import tqdm
import logging
import os
from PIL import Image

import constants


def removeBrokenImages(data):
    """This method removes broken images in data.

        Keyword arguments:
        data -- processed data from sparql endpoint
    """
    for person in tqdm(list(data.values()), desc='removeBrokenImages', miniters=int(len(data) / 100)):
        if 'images' in person:
            for image in list(person['images'].values()):
                if os.path.exists(f'{constants.IMAGES_DIRECTORY}/{image["fileNameLocal"]}'):
                    if isImageBroken(f'{constants.IMAGES_DIRECTORY}/{image["fileNameLocal"]}'):
                        logging.info(f'Removing image - {image["fileNameLocal"]} because it is broken')
                        print(f'Removing image - {image["fileNameLocal"]} because it is broken')
                        del person['images'][image['fileNameWiki']]
                        os.remove(f'{constants.IMAGES_DIRECTORY}/{image["fileNameLocal"]}')
                else:
                    logging.info(f'Removing image - {image["fileNameLocal"]} because it does not exists')
                    print(f'Removing image - {image["fileNameLocal"]} because it does not exists')
                    del person['images'][image['fileNameWiki']]

    return data

def isImageBroken(location):
    """This method checks if image is broken by trying to open it and performing transposition

        Keyword arguments:
        location -- location of a specific image
    """
    extension = os.path.splitext(location)[1]
    # PIL does not work with all formats (e.g., svg), so I am only checking those I can work with tensorflow
    # if extension in allowedExtensions:
    if extension in constants.ALLOWED_EXTENSIONS:
        try:
            with Image.open(location) as im:
                im.verify()

            with Image.open(location) as im:
                # Image.Transpose.FLIP... does not exist in older version of pillow, use Image.FLIP... instead
                im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

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