import re
from datetime import datetime
from functools import reduce
import random
from PIL import Image
from bs4 import BeautifulSoup
from collections import OrderedDict
from tqdm import tqdm
from urllib.parse import urlparse, unquote
from modules import constants
import itertools
import json
import logging
import os
import requests
import tensorflow as tf
from retinaface import RetinaFace
# import cv2
# import matplotlib.pyplot as plt
import warnings


def config():
    logging.basicConfig(filename='errors.log',
                        filemode='a',
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    # I am using beautiful soup for getting rid of HTML characters in caption and dates, in few cases it contains
    # a name of a file, which triggers BS4 warning
    warnings.filterwarnings("ignore", category=UserWarning, module='bs4')
    tf.get_logger().setLevel('ERROR')

    if not os.path.exists(constants.IMAGES_DIRECTORY):
        os.makedirs(constants.IMAGES_DIRECTORY)

    if not os.path.exists(constants.DATA_DIRECTORY):
        os.makedirs(constants.DATA_DIRECTORY)

    if not os.path.exists(constants.FIX_DATA_DIRECTORY):
        os.makedirs(constants.FIX_DATA_DIRECTORY)

    if not os.path.exists(constants.STATS_DIRECTORY):
        os.makedirs(constants.STATS_DIRECTORY)


def getRawSparqlData(fromYear=None, toYear=None):
    """This method gets data about all the people from wikidata between certain years.

        Keyword arguments:
        fromYear -- beginning of the range (default 1840)
        toYear -- end of the range (default 2015)
    """

    if fromYear is None:
        fromYear = constants.START_YEAR
    if toYear is None:
        toYear = datetime.now().year

    data = []
    # session = requests.Session()
    with requests.Session() as session:
        for i in tqdm(range(fromYear, toYear), desc='getRawSparqlData'):
            success = False
            numOfErrors = 0
            # Double parantheses as an escape for a F-string, otherwise the content between them is considered a variable
            query = f'''
                SELECT DISTINCT ?wikidataID ?name ?description ?imageUrl ?caption ?imageDate ?birthDate ?deathDate ?gender ?nationality ?occupation ?wikipediaTitle WITH {{ 
                SELECT ?wikidataID ?name ?birthDate WHERE {{
                    ?wikidataID wdt:P31 wd:Q5;
                                rdfs:label ?name;
                                wdt:P569 ?birthDate.
                                hint:Prior hint:rangeSafe "true"^^xsd:boolean.
                    FILTER(("{i}-00-00"^^xsd:dateTime <= ?birthDate) && (?birthDate < "{i + 1}-00-00"^^xsd:dateTime))
                    FILTER((LANG(?name)) = "en")
                }} }} as %i
                WHERE {{
                    INCLUDE %i
                    OPTIONAL {{ ?wikidataID schema:description ?description.   FILTER((LANG(?description)) = "en") }}
                    OPTIONAL {{ ?wikidataID wdt:P734 ?lastname. }}
                    OPTIONAL {{ ?wikidataID wdt:P570 ?deathDate. }}
                    OPTIONAL {{ ?wikidataID wdt:P27 ?nationality . }}
                    OPTIONAL {{ ?wikidataID wdt:P106 ?occupation . }}
                    OPTIONAL {{ ?wikidataID wdt:P21 ?gender. }}
                    OPTIONAL {{
                        ?wikidataID p:P18 ?stat.
                        ?stat ps:P18 ?imageUrl.
                        OPTIONAL {{ ?stat pq:P2096 ?caption. FILTER (langmatches(lang(?caption), "en")) }}
                        OPTIONAL {{ ?stat pq:P585 ?imageDate. }}
                    }}
                    ?wikipediaTitle schema:about ?wikidataID;
                    schema:isPartOf <https://en.wikipedia.org/>.
                }}
            '''
            while not success:
                try:
                    r = session.get(url=constants.SPARQL_URL, params={'format': 'json', 'query': query},
                                    headers=constants.HEADERS)
                    data.extend(r.json()['results']['bindings'])
                except requests.exceptions.RequestException as e:
                    numOfErrors += 1
                    success = False
                    logging.exception(e)
                except ValueError as ve:
                    numOfErrors += 1
                    success = False
                    logging.exception(ve)
                else:
                    success = True
                finally:
                    logging.info("Year " + str(i) + " had " + str(numOfErrors) + " errors.")

    return data


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


def addDistinctValues(property, value, node):
    """This method checks for duplicate values and only adds it once,
       in case there are multiple unique values create a list for them

        Keyword arguments:
        property -- name of the property to be added
        value -- value of the property to be added
        node -- any object that contains data, object to check the duplicity against
    """

    # This check is necessary, because some records might be missing some values, which could have been
    # deleted (they were marked as unknown values - removeBrokenData).
    # If the property is missing we can just add the property-value pair.
    if property in node:
        if isinstance(node[property], str):
            if value != node[property]:
                node[property] = [node[property], value]
        elif isinstance(value, list) and isinstance(node[property], list):
            node[property].extend(item for item in value if item not in node[property])
            # node[property] = value + list(set(node[property]) - set(value))
        elif isinstance(value, str) and isinstance(node[property], list):
            if value not in node[property]:
                node[property].append(value)
        elif isinstance(value, list) and isinstance(node[property], str):
            if node[property] not in value:
                value.append(node[property])
        elif isinstance(node[property], dict):
            for k, v in value.items():
                if k in node[property]:  # tento check je mozna zbytecny protoze uz je zahrnut v tom na radku 225, if property in node
                    addDistinctValues(k, v, node[property])
                else:
                    node[property][k] = v
    else:
        node[property] = value


def mergeListOfValues(data):
    for person in tqdm(data.values(), desc='mergeListOfValues', miniters=int(len(data) / 100)):
        if 'birthDate' in person and isinstance(person['birthDate'], list):
            if len(person['birthDate']) == 1:
                person['birthDate'] = person['birthDate'][0]
            else:
                person['birthDate'] = reduce(reduceDate, person['birthDate'])
        if 'deathDate' in person and isinstance(person['deathDate'], list):
            if len(person['deathDate']) == 1:
                person['deathDate'] = person['deathDate'][0]
            else:
                person['deathDate'] = reduce(reduceDate, person['deathDate'])
    return data


def reduceDate(date1, date2):
    if date1[:constants.YEAR_OFFSET] == date2[:constants.YEAR_OFFSET]:
        # -01-01 means, that wikidata record contains just year intead the full date
        # so we can choose the other one instead which is more likely to be the full date
        if date1[constants.YEAR_OFFSET:] == '-01-01':
            return date2
        elif date2[constants.YEAR_OFFSET:] == '-01-01':
            return date1

    return random.choice([date1, date2])


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
                if isinstance(person[property], str):
                    tags.add(person[property])
                if isinstance(person[property], list):
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
    # session = requests.Session()
    with requests.Session() as session:
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


def getThumbnails(data, chunkSize=50):
    """This method adds thumbnail images to all people in dataset if there are any on the wikipedia,
       the picture is only added if it is not in the set already (from wikidata or other source)

        Keyword arguments:
        data -- processed data from sparql endpoint
        chunkSize -- number of people that can be processed at once, limited by mediawiki API to 50 (default: 50)
    """

    toProcess = []
    for index, person in enumerate(tqdm(data.values(), desc='getThumbnails', miniters=int(len(data) / 100))):
        if len(toProcess) >= chunkSize or index >= len(data) - 1:
            getThumbnailsForChunk(toProcess, data)
            toProcess = [person['wikipediaTitle']]
        else:
            toProcess.append(person['wikipediaTitle'])

    if toProcess:
        getThumbnailsForChunk(toProcess, data)

    return data


def getThumbnailsForChunk(titles, people):
    """This method fetches images for wikipedia titles passed in

        Keyword arguments:
        titles -- list of wikipedia titles
        people -- processed data from sparql endpoint
    """
    # example:
    # https://en.wikipedia.org/w/api.php?action=query&titles=Ayn%20Rand&prop=pageprops&format=json&formatversion=2

    params = {
        'action': 'query',
        'prop': 'pageprops',
        'titles': '',
        'format': 'json',
        'formatversion': 2
    }
    # session = requests.Session()
    with requests.Session() as session:
        titlesString = "|".join(titles)
        params['titles'] = titlesString
        r = session.get(url=constants.MWAPI_URL, params=params, headers=constants.HEADERS)
        data = r.json()['query']['pages']
        for page in data:
            if 'pageprops' in page:
                pageprops = page['pageprops']
                # Necessary check, because some pictures can lack this link to wikidata
                if 'wikibase-item' in pageprops:
                    wikidataID = pageprops["wikibase_item"]
                    image = {
                        "caption": [],
                        "date": [],
                    }
                    key = None
                    if 'page_image' in pageprops:
                        key = 'page_image'
                    elif 'page_image_free' in pageprops:
                        key = 'page_image_free'
                    if key is not None:
                        fileNameWiki = unquote(pageprops[key]).replace(" ", "_")
                        image['fileNameLocal'] = f'{wikidataID}{os.path.splitext(fileNameWiki)[constants.FILE_EXT_INDEX]}'
                        image['fileNameWiki'] = fileNameWiki
                        addDistinctValues(fileNameWiki, image, people[wikidataID]['images'])


def getMetadataAndLinks(data, chunkSize=50):
    """This method fetches metadata and links of all images in dataset and adds it back to it

        Keyword arguments:
        data -- processed data from sparql endpoint
        chunkSize -- number of files that can be processed at once, limited by mediawiki API to 50 (default: 50)
    """
    toProcess = {}
    for i, person in enumerate(tqdm(data.values(), desc='getMetadataAndLinks', miniters=int(len(data) / 100))):
        for j, image in enumerate(person['images'].values()):
            if len(toProcess) >= chunkSize:
                getMetadataAndLinksForChunk(toProcess, data)
                toProcess = {image["fileNameWiki"]: [
                    person['wikidataID']]}  # TODO zkontrolovat druhou metodu s toProcess jestli nema stejny problem
            else:
                # Some pictures can be used at multiple people, those picture usually would not be used
                # model training, as they would not contain a person. That is the reason, why all the wikidataIDs
                # needs to be put in the list
                if image['fileNameWiki'] in toProcess:
                    toProcess[image["fileNameWiki"]].append(person['wikidataID'])
                else:
                    toProcess[image["fileNameWiki"]] = [person['wikidataID']]

    # Easy way how to check if dictionary is empty or not
    if toProcess:
        getMetadataAndLinksForChunk(toProcess, data)

    return data


def getMetadataAndLinksForChunk(titlesDict, data):
    """This method fetches metadata and links of images in titlesDict and adds it to the dataset

        Keyword arguments:
        titlesDict -- dictionary with image file names as keys and wikidataID as values, used for storing the fetched data in correct place
        data -- processed data from sparql endpoint
    """
    # example
    # https://commons.wikimedia.org/w/api.php?action=query&prop=pageimages|imageinfo&iiprop=extmetadata&piprop=original&titles=File:Ayn_Rand_(1943_Talbot_portrait).jpg&formatversion=2&format=json
    params = {
        'action': 'query',
        'titles': '',
        'prop': 'pageimages|imageinfo',
        'piprop': 'original',
        'iiprop': 'extmetadata',
        'format': 'json',
        'formatversion': 2
    }
    # session = requests.Session()
    with requests.Session() as session:
        titlesString = f'File:{"|File:".join(list(titlesDict.keys()))}'
        params['titles'] = titlesString
        r = session.get(url=constants.MWAPI_URL, params=params, headers=constants.HEADERS)
        pages = r.json()['query']['pages']

        for page in pages:
            if 'original' in page:
                # I also cannot use getLastPartOfURL on this image, because there might be some odd names of files
                # (e.g., they can contain a ? or ;) which mess up with the method
                fileName = unquote(page['title'][constants.FILE_TITLE_OFFSET:]).replace(' ', '_')
                # all dict value is a list instead of a single value so it is easier to use
                for wikidataID in titlesDict[fileName]:
                    # wikidataID = titlesDict[fileName]
                    person = data[wikidataID]
                    image = person['images'][fileName]
                    metadata = page['imageinfo'][0]['extmetadata']

                    image['url'] = page['original']['source']
                    if 'DateTime' in metadata:
                        image['exifDate'] = metadata['DateTime']['value']
                    if 'ImageDescription' in metadata:  # pujde to prepsat pomoci addDistinct value?
                        caption = metadata['ImageDescription']['value']
                        caption = BeautifulSoup(caption, features="html.parser").get_text()
                        addDistinctValues('caption', caption, image)
                    if 'DateTimeOriginal' in metadata:
                        date = metadata['DateTimeOriginal']['value']
                        date = BeautifulSoup(date, features="html.parser").get_text()
                        addDistinctValues('date', date, image)
            else:
                logging.error(f'picture {page["title"]} from {person["wikidataID"]} does not exist')


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


def getPictures(data, startIndex=None, endIndex=None):
    """This method downloads all the picture from the dataset,

        Keyword arguments:
        data -- processed data from sparql endpoint
        startIndex -- starting point in dataset, can be used for dividing dataset or for threading
        endIndex -- ending point in dataset, can be used for dividing dataset or for threading
    """
    if startIndex is None:
        startIndex = 0
    if endIndex is None:
        endIndex = len(data)

    for person in tqdm(list(data.values())[startIndex:endIndex], desc='getPictures',
                       miniters=int((endIndex - startIndex) / 100)):
        try:
            getPicturesForPerson(person)
        except Exception as e:
            logging.error(f'Exception happened during downloading picture for {person["wikidataID"]}')
            logging.error(e)

    return data


def getPicturesForPerson(person):
    """This method downloads all the picture for specific person

        Keyword arguments:
        person --  one person from processed dataset
    """
    # session = requests.Session()
    with requests.Session() as session:
        if 'images' in person:
            for image in list(person['images'].values()):
                if not os.path.isfile(f'{constants.IMAGES_DIRECTORY}/{image["fileNameLocal"]}'):
                    if 'url' in image:
                        # print(f'{person["wikidataID"]} {image["fileNameWiki"]}')
                        response = session.get(url=image['url'], headers=constants.HEADERS)
                        if response.ok:
                            location = f'{constants.IMAGES_DIRECTORY}/{image["fileNameLocal"]}'
                            with open(location, "wb+") as f:
                                f.write(response.content)
                        else:
                            logging.error(
                                f'Image {image["fileNameWiki"]} which belongs to {person["wikidataID"]} not found! REMOVING IT!')
                            del person['images'][image['fileNameWiki']]
                    else:
                        logging.error(f'Image {image["fileNameWiki"]} - {person["wikidataID"]} has no URL! REMOVING IT!')
                        del person['images'][image['fileNameWiki']]


def isImageBroken(location):
    """This method checks if image is broken by trying to open it and performing transposition

        Keyword arguments:
        location -- location of a specific image
    """
    extension = os.path.splitext(location)[1]
    allowedExtensions = []
    for ext in constants.ALLOWED_EXTENSIONS:
        # create all combinations of lower and uppercase
        allowedExtensions.extend(map(''.join, itertools.product(*zip(ext.upper(), ext.lower()))))
    # PIL does not work with all formats (e.g., svg), so I am only checking those I can work with tensorflow
    if extension in allowedExtensions:
        try:
            with Image.open(location) as im:
                im.verify()

            with Image.open(location) as im:
                im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

            # Potential test if retina-face is able to open the image.
            # with cv2.imread('foo.jpg') as img
            #     test = img.shape
        # PIL cannot read big tiff files and raises this error, for keeping the code simple we can just consider
        # that file correct by skipping all .tif and .tiff
        # except UnidentifiedImageError:
        #     return False
        except Exception as e:
            logging.error(f'Exception happened while checking image {location} - {e}')
            return True
    return False


def removeBrokenImages(data):
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


def mergeDatasets(datasets):
    """This method merges all datasets from list that is passed as an argument

        Keyword arguments:
        datasets -- list of datasets to be merged
    """
    uniqueDumps = list(set([json.dumps(data) for data in datasets]))
    unique = [data for data in datasets if json.dumps(data) in uniqueDumps]
    result = unique[0]

    for data in tqdm(datasets[1:], desc='mergeDatasets', miniters=(len(datasets[1:]) / 100)):
        for person in data.values():
            if person['wikidataID'] in result:
                for property, value in person.items():
                    addDistinctValues(property, value, result[person['wikidataID']])
            else:
                result[person['wikidataID']] = person

    return result


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


def detectFaces(data, processedImages=None):
    """This method detects faces in images in dataset. There is a limitation on images' extensions.

        Keyword arguments:
        data -- processed data from sparql endpoint
        processedImages -- dictionary of images that was already processed with face detection (default: None)
    """

    if processedImages is None:
        processedImages = {}
    allowedExtensions = []
    for extension in constants.ALLOWED_EXTENSIONS:
        # create all combinations of lower and uppercase
        allowedExtensions.extend(map(''.join, itertools.product(*zip(extension.upper(), extension.lower()))))

    for index, person in enumerate(
            tqdm(data.values(), desc='detectFaces', miniters=int(len(data) / 100))):
        for image in person['images'].values():
            if image['fileNameWiki'] not in processedImages:
                if os.path.splitext(image["fileNameLocal"])[1] in allowedExtensions:
                    if 'faces' not in image:
                        logging.info(f'Image {image["fileNameWiki"]} not found in dictionary')
                        try:
                            processedImages[image['fileNameWiki']] = detectFacesInImage(image)
                        except Exception as e:
                            logging.error(f'Exception happened in {image["fileNameWiki"]} from {person["wikidataID"]}')
                            logging.error(e)
                    elif image['fileNameWiki'] not in processedImages:
                        processedImages[image['fileNameWiki']] = image['faces']
            else:
                image['faces'] = processedImages[image['fileNameWiki']]


    return processedImages, data


def detectFacesInImage(image):
    """This method detects faces in one specific image.

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
                box = [int(value) for value in face['facial_area']]
                x1, y1, x2, y2 = box
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


def createStats(data, histogramImgFile):
    """This method creates histogram for detected faces

        Keyword arguments:
        data -- processed data from sparql endpoint
        histogramImgFile -- location where to save the histogram
    """
    stats = {}
    for person in tqdm(data.values(), desc='createStats', miniters=int(len(data) / 100)):
        for image in person['images'].values():
            # Images with bad extensions are skipped during the face detection phase
            # We are only interested in those images, that were through successful face detection and got an age assigned to them
            if 'faces' in image and 'age' in image and image['age'] is not None:
                numberOfFaces = len(image['faces'])
                if numberOfFaces in stats:
                    stats[numberOfFaces] += 1
                else:
                    stats[numberOfFaces] = 1

    plt.bar(list(stats.keys()), stats.values(), color='green')
    plt.ylabel('# of occurences in dataset')
    plt.xlabel('# of faces detected')
    plt.title('Distribution of detected faces')
    plt.savefig(histogramImgFile)

    return data


def addAgeToImages(data):
    for person in tqdm(data.values(), desc='addAgeToImages', miniters=int(len(data) / 100)):
        if 'images' in person:
            for image in person['images'].values():
                addAgeToImage(image, person)

    return data


def addAgeToImage(image, person):
    # dat je do slovniku, pak to projet podle vyskytu a vybrat ten co je v range a ma nejvice vyskytu
    stats = {}
    years = []
    if 'date' in image:
        for item in image['date']:
            years.extend(findPotentialYears(item))

    if 'caption' in image:
        for item in image['caption']:
            years.extend(findPotentialYears(item))

    if 'fileNameWiki' in image:
        years.extend(findPotentialYears(image['fileNameWiki']))

    for year in years:
        year = int(year)
        if isYearInRange(year, person) and constants.START_YEAR <= year <= datetime.now().year:
            if year in stats:
                stats[year] += 1
            else:
                stats[year] = 1

    sortedStats = {k: v for k, v in sorted(stats.items(), key=lambda item: item[1])}

    counter = 0
    while True:
        if counter < len(sortedStats):
            year = list(sortedStats.keys())[counter]
            counter += 1
        else:
            image['age'] = None
            break
        if year is None:
            image['age'] = None
            break
        else:
            age = year - int(person['birthDate'][:constants.YEAR_OFFSET])
            if 0 < age < 100:
                image['age'] = age
                break


def findPotentialYears(text):
    regex = '([1-2][0-9]{3})'
    years = re.findall(regex, text)
    return years


def isYearInRange(year, person):
    """This method checks if year is in range of years, when specified person was alive.

        Keyword arguments:
        year -- year to be checked
        person -- specific person to check year agains
    """
    if 'birthDate' in person:
        birthYear = int(person['birthDate'][:constants.YEAR_OFFSET])
    else:
        birthYear = 0
    if 'deathDate' in person:
        deathYear = int(person['deathDate'][:constants.YEAR_OFFSET])
    else:
        deathYear = 3000
    if year > birthYear and year < deathYear:
        return True
    return False


def getLastPartOfURL(url):
    """This method returns last part of passed URL, it can be either file, ID, basically anything behind the last slash,
       be aware of this methods limitation, if there is a special character like ? or ; in the last part of URL,
       the method would not work properly and it is better to use custom string strip

        Keyword arguments:
        url -- desired url
    """
    return unquote(os.path.basename(urlparse(url).path))


def saveData(data, file, indent=2):
    """This method saves data to a file with a specific indent

        Keyword arguments:
        data -- processed data from sparql endpoint
        file -- file and location to save data to
        indent -- number of spaces for nicer formatting of JSON (default: 2)
    """

    with open(file, 'w', encoding="UTF-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def readData(file):
    """This method reads data from a file

        Keyword arguments:
        file -- file and location to read data from
    """

    with open(file, 'r', encoding="UTF-8") as f:
        data = json.loads(f.read())
    return data


def countProperty(data, properties={}):
    """This method does a basic statistics on data and counts desired properties

        Keyword arguments:
        data -- processed data from sparql endpoint
        properties -- dictionary of desired properties to count with assigned boolean value,
                      True -- add all values from lists
                      False -- only count a number of occurences of property
                      eg: {'images': True} will count number of all images in data, adding the length of the list
                      in comparison to: {'deathDate': False} will only count number of deathDate is present in data.

                      NOTE: all properties with non-list values are percieved as False
    """

    stats = {property: 0 for property in properties}

    for person in tqdm(data.values(), desc='countProperty', miniters=int(len(data) / 100)):
        for property in properties:
            if property in person:
                # properties[property] is a boolean value passed to the method in dictionary
                if isinstance(person[property], list) and properties[property] or isinstance(person[property], dict) and \
                        properties[property]:
                    stats[property] += len(person[property])
                else:
                    stats[property] += 1

    print(f'Total number of people: {len(data)}')
    for property in properties:
        print(f'{property}: {properties[property]} = {stats[property]}')

    return stats


def fullDataDownload():
    config()
    step = 5
    for year in range(constants.START_YEAR, constants.END_YEAR, step):
        print(f'Starting years: {year}, {year + step}!')
        data = getRawSparqlData(year, year + step)
        data = removeBrokenData(data)
        data = simplifySparqlData(data)
        data = processSparqlData(data)
        data = mergeListOfValues(data)
        # ordering just because of saving
        data = orderData(data)
        data = changeOrderOfProperties(data)
        saveData(data, f'{constants.DATA_DIRECTORY}/{year}_{year + step}.json')

        data = labelTags(data)
        data = getThumbnails(data)
        data = getMetadataAndLinks(data)
        # Ordering data here is necessary, so 2 similar datasets can be joined by merge,
        # otherwise people with two pictures could lose some of them by overwriting
        data = orderData(data)
        data = changeOrderOfProperties(data)
        data = addIndexToImageNames(data)

        # probably useless, needs to be ordered after faces are added too
        data = orderData(data)
        data = changeOrderOfProperties(data)
        data = addAgeToImages(data)

        saveData(data, f'{constants.DATA_DIRECTORY}/{year}_{year + step}.json')
        getPictures(data)
        data = removeBrokenImages(data)
        saveData(data, f'{constants.DATA_DIRECTORY}/{year}_{year + step}.json')


def detectFacesJob():
    config()
    step = 5
    processedImages = readData(f'{constants.DATA_DIRECTORY}/processedImages.json')
    for year in range(constants.START_YEAR, constants.END_YEAR, step):
        print(f'Starting years: {year}, {year + step}!')
        data = readData(f'{constants.DATA_DIRECTORY}/{year}_{year + step}.json')
        processedImages, data = detectFaces(data, processedImages)
        saveData(data, f'{constants.DATA_DIRECTORY}/{year}_{year + step}.json')
        saveData(processedImages, f'{constants.DATA_DIRECTORY}/processedImages.json')

def main():
    pass


if __name__ == '__main__':
    pass

    # print(json.dumps(data, ensure_ascii=False, indent=2))

# TODO: upravit docstring podle sphinx stylu nebo jineho a pridat returny
# TODO: rozdelit lepe metody do jednotlivych modulu, pozor na utils
# TODO podivat se jestli nekde nepredavam data zbytecne
# TODO pridat max hodnotu na vrchol grafu u statistiky
# TODO dodelat paralelizaci, at pak muzu poustet tensorflow s bezpecnym uvolnovanim pameti
# TODO dodelat batch u vsech metod, abych je mohl spoustet paralelne
# TODO dodelat prubezne ukladani u vsech metod a kontrolu jestli tam data jiz nejsou

# TODO dodelat filter pomoci list comprehension, ktere by mohli byt za sebou,
# nebo jeste lepe udelat metody na filtrovani jednotlivych props, ktere pak muzu poskladat za sebou
# nebo jeste lepe udelat metodu na filtrovani props u jednotlivych lidi, ty metody pak mohu dat do pole a v labde je
# postupne vybirat, jakmile narazim na jednu, ktera brati false, tak tam toho cloveka nedam

# pridat velikosti obrazku do datasetu, aby se podle nej mohlo filtrovat - nepotrebujeme, tato informace uy je v boxu

