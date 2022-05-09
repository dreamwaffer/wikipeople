from collections import OrderedDict
from tqdm import tqdm
from urllib.parse import unquote
from modules import constants
import os
import requests
# import tensorflow as tf
# from retinaface import RetinaFace


def removeBrokenData(data):
    """This method removes unknown data from the dataset, some data available on wikidata
       are marked as unknown and looks like URLs to empty page
       (e.g., http://www.wikidata.org/.well-known/genid/eccd559869b138d54f88eb750777c1e2)

        Keyword arguments:
        data -- raw data from sparql endpoint
    """

    for record in tqdm(data, desc='removeBrokenData', miniters=int(len(data) / 100)):
        for property in list(record):
            for brokenData in constants.BROKEN_DATA:
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
            value = record['wikidataID']['value'][constants.WIKIDATA_ENTITY_OFFSET:]
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
                simpRec[key] = value['value'][:constants.GENERAL_DATE_OFFSET]
            elif key == 'imageUrl':
                # urllib.parse.unquote gets rid of the special characters in URL (%20, etc.)
                # I need to do it, so I can use name of the file to distinguish
                # whether the image is in the set already or not
                # I cannot use getLastPartOfURL, because fileNames can contain special characters which will result in
                # stripping incorrect part of URL
                fileName = value['value'][constants.WIKIPEDIA_FILE_NAME_OFFSET:]
                image['fileNameWiki'] = unquote(fileName).replace(" ", "_")
                image['fileNameLocal'] = f'{simpRec["wikidataID"]}' \
                                         f'{os.path.splitext(image["fileNameWiki"])[constants.FILE_EXT_INDEX]}'
                simpRec['images'] = {image['fileNameWiki']: image}
            elif key == 'imageDate':
                image['date'].append(value['value'][:constants.GENERAL_DATE_OFFSET])
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
                addDistinctValues(key, value, peopleDictionary[wikidataID])
        else:
            # having all pictures in a dictionary is better for processing even if there is just one
            if 'images' not in person:
                person['images'] = {}
            peopleDictionary[wikidataID] = person

    return peopleDictionary


def labelTags(data):
    """This method labels all tags in a dataset

        Keyword arguments:
        data -- processed data from sparql endpoint
    """

    tagsDictionary = createTagsDictionary(data)
    for person in tqdm(data.values(), desc='labelTags', miniters=int(len(data) / 100)):
        for key, value in list(person.items()):
            if key in constants.PROPERTIES_WITH_TAGS:
                if isinstance(value, str):
                    if value in tagsDictionary:
                        person[key] = tagsDictionary[value]
                    else:
                        del person[key]
                if isinstance(value, list):
                    value[:] = [tagsDictionary[item] for item in value if item in tagsDictionary]

    return data

def getAllTags(data, properties):
    """This method creates a set of all tags presented in the dataset. Tags are wikidata
       identifiers. Usually they can be labeled by the service, but because these sparql calls
       are already quite heavy, we can just label them afterwards.

        Keyword arguments:
        data -- processed data from sparql endpoint
        properties -- list of properties which contain tags to be labeled
    """

    tags = set()

    for person in data.values():
        for property in properties:
            if property in person:
                if (isinstance(person[property], str)):
                    tags.add(person[property])
                if (isinstance(person[property], list)):
                    for item in person[property]:
                        tags.add(item)

    return list(tags)


def createTagsDictionary(data, chunkSize=500):
    """This method creates a dictionary with tags and their labels

        Keyword arguments:
        data -- processed data from sparql endpoint
        chunkSize -- number of tags that can be labeled at once, there is a limitation on the endpoint (default: 500)
    """
    tags = getAllTags(data, constants.PROPERTIES_WITH_TAGS)
    tagsDictionary = {}
    session = requests.Session()

    for i in range(0, len(tags), chunkSize):
        queryValues = "wd:" + " wd:".join(tags[i:i + chunkSize])
        query = f'''
            SELECT DISTINCT ?item ?itemLabel
            WHERE {{
                VALUES ?item {{ {queryValues} }}
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }}
        '''
        r = session.get(url=constants.SPARQL_URL, params={'format': 'json', 'query': query}, headers=constants.HEADERS)
        data = r.json()['results']['bindings']

        for tag in data:
            item = tag['item']['value'][constants.WIKIDATA_ENTITY_OFFSET:]
            itemLabel = tag['itemLabel']['value']
            # This condition removes tags, that does not have an english label,
            # all data with no label are removed
            if item != itemLabel:
                tagsDictionary[item] = itemLabel

    return tagsDictionary



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


def changeOrderOfProperties(data):
    """This method reorders properties in dataset according to structure defined in constants.PERSON_STRUCTURE
       and constants IMAGE_STRUCTURE

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
