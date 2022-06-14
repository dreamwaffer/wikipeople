import hashlib
from datetime import datetime
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import unquote
import constants
from create import utils
import logging
import os
import requests

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
                    OPTIONAL {{ ?wikipediaTitle schema:about ?wikidataID; 
                             schema:isPartOf <https://en.wikipedia.org/>.
                    }}                    
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
                    logging.exception(f'Exception in request happened')
                except ValueError as ve:
                    numOfErrors += 1
                    success = False
                    logging.exception(f'Exception in JSON happened')
                else:
                    success = True
                finally:
                    logging.info("Year " + str(i) + " had " + str(numOfErrors) + " errors.")

    return data


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
            toProcess = []
        if 'wikipediaTitle' in person:
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
                        image[
                            'fileNameLocal'] = f'{wikidataID}{os.path.splitext(fileNameWiki)[constants.FILE_EXT_INDEX]}'
                        image['fileNameWiki'] = fileNameWiki
                        utils.addDistinctValues(fileNameWiki, image, people[wikidataID]['images'])


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
                # Some pictures can be used at multiple people, those picture usually would not be used for
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
                    person = data[wikidataID]
                    image = person['images'][fileName]
                    metadata = page['imageinfo'][0]['extmetadata']

                    image['url'] = page['original']['source']
                    if 'DateTime' in metadata:
                        image['exifDate'] = metadata['DateTime']['value']
                    if 'ImageDescription' in metadata:  # pujde to prepsat pomoci addDistinct value?
                        caption = metadata['ImageDescription']['value']
                        caption = BeautifulSoup(caption, features="html.parser").get_text()
                        utils.addDistinctValues('caption', caption, image)
                    if 'DateTimeOriginal' in metadata:
                        date = metadata['DateTimeOriginal']['value']
                        date = BeautifulSoup(date, features="html.parser").get_text()
                        utils.addDistinctValues('date', date, image)
            else:
                logging.error(f'picture {page["title"]} from {person["wikidataID"]} does not exist')


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
            person = getPicturesForPerson(person)
        except Exception as e:
            logging.exception(f'Exception happened during downloading picture for {person["wikidataID"]}')

    return data


def getPicturesForPerson(person):
    """This method downloads all the picture for specific person

        Keyword arguments:
        person --  one person from processed dataset
    """
    with requests.Session() as session:
        if 'images' in person:
            for image in list(person['images'].values()):
                # When the database is created for the first time, all the pictures will be downloaded
                # The check if the image is already in the directory works only if we have the data with
                # fileNameLocal in them
                if 'fileNameLocal' not in image or not os.path.isfile(f'{constants.IMAGES_DIRECTORY}/{image["fileNameLocal"]}'):
                    if 'url' in image:
                        # print(f'{person["wikidataID"]} {image["fileNameWiki"]}')
                        response = session.get(url=image['url'], headers=constants.HEADERS)
                        if response.ok:
                            hash = hashlib.sha256(response.content).hexdigest()
                            image["fileNameLocal"] = f"{hash}{image['extension']}"
                            location = f'{constants.IMAGES_DIRECTORY}/{image["fileNameLocal"]}'
                            with open(location, "wb+") as f:
                                f.write(response.content)
                        else:
                            logging.error(
                                f'Image {image["fileNameWiki"]} which belongs to {person["wikidataID"]} not found! REMOVING IT!')
                            del person['images'][image['fileNameWiki']]
                    else:
                        logging.error(
                            f'Image {image["fileNameWiki"]} - {person["wikidataID"]} has no URL! REMOVING IT!')
                        del person['images'][image['fileNameWiki']]

    return person