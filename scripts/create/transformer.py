# Module name: Transformer
# Purpose: This module contains functions for transforming data into various forms used for
#          training, evaluating or processing.

import random
import os
import copy

from tqdm import tqdm
from urllib.parse import unquote

from create.utils import addDistinctValues, getLastPartOfURL
from create.merger import mergeAllDataForEvaluation
from constants import BROKEN_DATA, PERSON_PROPERTIES_FOR_TRAINING, IMAGE_PROPERTIES_FOR_TRAINING, GENERAL_DATE_OFFSET, \
    WIKIPEDIA_FILE_NAME_OFFSET, FILE_EXT_INDEX, WIKIDATA_ENTITY_OFFSET, BANNED_EXTENSIONS, \
    PERSON_PROPERTIES_FOR_EVALUATION, IMAGE_PROPERTIES_FOR_EVALUATION


def removeBrokenData(data):
    """This method removes unknown data from the dataset, some data available on wikidata
       are marked as unknown and looks like URLs to empty page
       (e.g., http://www.wikidata.org/.well-known/genid/eccd559869b138d54f88eb750777c1e2).
       We can just remove that property and merge it as usual in simplifySparqlData step.

        Keyword arguments:
        data -- raw data from sparql endpoint
    """

    for record in tqdm(data, desc='removeBrokenData', miniters=int(len(data) / 100)):
        for property in list(record):
            for brokenData in BROKEN_DATA:
                if brokenData in record[property]['value']:
                    del record[property]

    return data


def simplifySparqlData(data):
    """This method simplifies raw data from sparql endpoint into more usable format,
       creates all necessary object properties or transform them.
       This is a custom function, change this if you want to process data differently.

        Keyword arguments:
        data -- raw data from sparql endpoint
    """

    result = []

    for record in tqdm(data, desc='simplifySparqlData', miniters=int(len(data) / 100)):
        simpRec = {}  # simpRec -- simplified record
        # Have to process wikidataID first as it is used with other properties
        if 'wikidataID' in record:
            value = record['wikidataID']['value'][WIKIDATA_ENTITY_OFFSET:]
            simpRec['wikidataID'] = value
        # Have to create images object before filling it with other properties (date, caption, etc.)
        if 'imageUrl' in record:
            image = {
                "caption": [],
                "date": [],
            }
        for key, value in record.items():
            if key in ['occupation', 'nationality', 'gender']:
                simpRec[key] = [getLastPartOfURL(value['value'])]
            if key in ['description', 'name']:
                simpRec[key] = value['value']
            elif key == 'wikipediaTitle':
                simpRec[key] = getLastPartOfURL(value['value'])
            elif key == 'birthDate' or key == 'deathDate':
                simpRec[key] = value['value'][:GENERAL_DATE_OFFSET]
            elif key == 'imageUrl':
                # urllib.parse.unquote gets rid of the special characters in URL (%20, etc.)
                # I need to do it, so I can use name of the file to distinguish
                # whether the image is in the set already or not
                # I cannot use getLastPartOfURL, because fileNames can contain special characters which will result in
                # stripping incorrect part of URL
                fileName = value['value'][WIKIPEDIA_FILE_NAME_OFFSET:]
                image['fileNameWiki'] = unquote(fileName).replace(" ", "_")
                image['extension'] = f'{os.path.splitext(image["fileNameWiki"])[FILE_EXT_INDEX].lower()}'
                simpRec['images'] = {image['fileNameWiki']: image}
            elif key == 'imageDate':
                image['date'].append(value['value'][:GENERAL_DATE_OFFSET])
            elif key == 'caption':
                image['caption'].append(value['value'])

        result.append(simpRec)

    return result


def processSparqlData(data):
    """This method processes simplified data from sparql endpoint,
       checks for duplicities in RDF triplets and only save distinct values.
       This is a custom function, change this if you want to process data differently.

       Keyword arguments:
       data -- simplified data from sparql endpoint
    """

    peopleDictionary = {}

    for person in tqdm(data, desc='processSparqlData', miniters=int(len(data) / 100)):
        wikidataID = person['wikidataID']
        if wikidataID in peopleDictionary:
            for key, value in person.items():
                addDistinctValues(key, value, peopleDictionary[wikidataID])
        else:
            # having all pictures in a dictionary is better for processing even if there is just one
            if 'images' not in person:
                person['images'] = {}
            peopleDictionary[wikidataID] = person

    return peopleDictionary


def toImageData(data):
    """This method creates dataset, which is images oriented. This dataset is better usable for model training.

       Keyword arguments:
        data -- processed data from sparql endpoint
    """

    images = []
    for person in list(data.values()):
        info = {k: v for (k, v) in person.items() if k in PERSON_PROPERTIES_FOR_TRAINING}
        for image in list(person['images'].values()):
            imageObj = copy.deepcopy(info) | {k: v for (k, v) in image.items() if k in IMAGE_PROPERTIES_FOR_TRAINING}
            images.append(imageObj)

    return images


def toTrainingPeople(data):
    """This method creates dataset, which contains only people used for training. This dataset is then returned.

       Keyword arguments:
        data -- processed data from sparql endpoint
    """

    newData = copy.deepcopy(data)
    for wikidataID, person in list(newData.items()):
        for key, image in list(person['images'].items()):
            age = 'age' in image and image['age'] is not None
            faces = 'faces' in image and len(image['faces']) == 1
            if not age or not faces:
                del person['images'][key]
        if not person['images']:
            del newData[wikidataID]

    return newData


def toPeopleWithGender(data):
    """This method creates dataset, which contains only people with exactly one gender value.

       Keyword arguments:
        data -- processed data from sparql endpoint
    """

    newData = copy.deepcopy(data)
    for wikidataID, person in list(newData.items()):
        if 'gender' not in person or len(person['gender']) > 1 or person['gender'][0] not in ['male', 'female']:
            del newData[wikidataID]

    return newData


def toImagesBetween17And80(data):
    """This method creates dataset, which contains only images with detected age between 17 and 80 inclusive.

       Keyword arguments:
        data -- processed data from sparql endpoint
    """

    newData = [image for image in data if image['age'] <= 80 and image['age'] >= 17]
    return newData


def toImagesWithoutTif(data):
    """This method creates dataset, which contains only images without the .tif extension.

       Keyword arguments:
        data -- processed data from sparql endpoint
    """

    newData = [image for image in data if image['extension'] not in BANNED_EXTENSIONS]
    return newData


def toPeopleWithWikipedia(data):
    """This method creates dataset, which contains only people that are associated with Wikipedia page.

       Keyword arguments:
        data -- processed data from sparql endpoint
    """

    newData = copy.deepcopy(data)
    for wikidataID, person in list(newData.items()):
        if 'wikipediaTitle' not in person:
            del newData[wikidataID]

    return newData


def toPeopleWithAllProps(data):
    """This method creates dataset, which contains only people with all the props.

       Keyword arguments:
        data -- processed data from sparql endpoint
    """

    newData = copy.deepcopy(data)
    properties = ['name', 'description', 'gender', 'birthDate', 'deathDate', 'nationality', 'occupation']
    for wikidataID, person in list(newData.items()):
        if not all(key in person for key in properties) or len(person['images']) != 1:
            del newData[wikidataID]

    return newData


def toImageDataEvaluation(data):
    """This method creates smaller dataset, which contains only images usable for evaluation.

       Keyword arguments:
        data -- processed data from sparql endpoint
    """

    images = []
    for person in list(data.values()):
        info = {k: v for (k, v) in person.items() if k in PERSON_PROPERTIES_FOR_EVALUATION}
        for image in list(person['images'].values()):
            imageObj = copy.deepcopy(info) | {k: v for (k, v) in image.items() if k in IMAGE_PROPERTIES_FOR_EVALUATION}
            images.append(imageObj)

    return images


def toEvaluationSample():
    """This method creates evaluation sample. All the training data,
       annotated images with exactly one face detected in them and age found, are put together.
       These images are further filtered for related Wikipedia page. All images without a related
       Wikipedia page are filtered out. From those 1000 are pseudorandomly chosen.

       Keyword arguments:
        data -- processed data from sparql endpoint
    """

    data = mergeAllDataForEvaluation()
    print(len(data))
    data = random.sample(data, 1000)
    for image in data:
        image['imageLink'] = f"https://commons.wikimedia.org/wiki/File:{image['fileNameWiki']}"
        image['wikipediaLink'] = f"https://en.wikipedia.org/wiki/{image['wikipediaTitle']}"
        image['wikidataLink'] = f"https://www.wikidata.org/wiki/{image['wikidataID']}"
        image['imageYear'] = 0
        del image['fileNameWiki']
        del image['wikipediaTitle']
        del image['wikidataID']

    return data