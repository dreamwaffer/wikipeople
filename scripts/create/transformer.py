from tqdm import tqdm
from urllib.parse import unquote
from create import utils
import os
import copy

from constants import BROKEN_DATA, PERSON_PROPERTIES_FOR_TRAINING, IMAGE_PROPERTIES_FOR_TRAINING, GENERAL_DATE_OFFSET, WIKIPEDIA_FILE_NAME_OFFSET, FILE_EXT_INDEX, WIKIDATA_ENTITY_OFFSET


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

       Custom function, change this if you want to process data differently.

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
                simpRec[key] = [utils.getLastPartOfURL(value['value'])]
            if key in ['description', 'name']:
                simpRec[key] = value['value']
            elif key == 'wikipediaTitle':
                simpRec[key] = utils.getLastPartOfURL(value['value'])
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

       Custom function, change this if you want to process data differently.

       Keyword arguments:
       data -- simplified data from sparql endpoint
    """

    peopleDictionary = {}

    for person in tqdm(data, desc='processSparqlData', miniters=int(len(data) / 100)):
        wikidataID = person['wikidataID']
        if wikidataID in peopleDictionary:
            for key, value in person.items():
                utils.addDistinctValues(key, value, peopleDictionary[wikidataID])
        else:
            # having all pictures in a dictionary is better for processing even if there is just one
            if 'images' not in person:
                person['images'] = {}
            peopleDictionary[wikidataID] = person

    return peopleDictionary


# TODO: PROBABLY NOT NEEDED ANYMORE
def addIndexToImageNames(data):
    """This method adds indexes to local image file names (fileNameLocal),
       it is needed because, some of the people have more pictures on wikidata
       and the local names were originally just ther wikidata IDs.

       Keyword arguments:
        data -- processed data from sparql endpoint
    """

    for person in tqdm(data.values(), desc='addIndexToImageNames', miniters=int(len(data) / 100)):
        if 'images' in person:
            for index, image in enumerate(person['images'].values()):
                name, extension = os.path.splitext(image["fileNameLocal"])
                image['fileNameLocal'] = f'{name}_{index + 1}{extension}'
    return data


def toUsableImageData(data):
    """This method creates smaller dataset, which contains only images usable for model training
       (images with only one detected face)

       Keyword arguments:
        data -- processed data from sparql endpoint
    """
    images = []
    for person in list(data.values()):
        info = {k: v for (k, v) in person.items() if k in PERSON_PROPERTIES_FOR_TRAINING}
        for image in list(person['images'].values()):
            imageObj = copy.deepcopy(info) | {k: v for (k, v) in image.items() if k in IMAGE_PROPERTIES_FOR_TRAINING}
            if 'faces' in imageObj and len(imageObj['faces']) == 1:
                images.append(imageObj)

    return images