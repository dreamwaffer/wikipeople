import constants
from tqdm import tqdm
import requests

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

def getAllTags(data, properties):
    """This method creates a set of all labels presented in the dataset. Tags are wikidata
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