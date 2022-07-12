# Module name: Labeler
# Purpose: This module contains functions to label Wikidata tags in dataset.

import requests

from tqdm import tqdm

from constants import WIKIDATA_ENTITY_OFFSET, HEADERS, SPARQL_URL, PROPERTIES_WITH_TAGS


def labelTags(data):
    """This method labels all Wikidata tags in a dataset passed into the method.

        Keyword arguments:
        data -- processed data from sparql endpoint
    """

    tagsDictionary = createTagsDictionary(data)
    for person in tqdm(data.values(), desc='labelTags', miniters=int(len(data) / 100)):
        for key, value in list(person.items()):
            if key in PROPERTIES_WITH_TAGS:
                if isinstance(value, str):
                    if value in tagsDictionary:
                        person[key] = tagsDictionary[value]
                    else:
                        del person[key]
                if isinstance(value, list):
                    value[:] = [tagsDictionary[item] for item in value if item in tagsDictionary]

    return data


def createTagsDictionary(data, chunkSize=500):
    """This method creates a dictionary with tags and their labels from all the data passed into the method.

        Keyword arguments:
        data -- processed data from sparql endpoint
        chunkSize -- number of tags that can be labeled at once, there is a limitation on the endpoint (default: 500)
    """

    tags = getAllTags(data, PROPERTIES_WITH_TAGS)
    tagsDictionary = {}

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
            r = session.get(url=SPARQL_URL, params={'format': 'json', 'query': query},
                            headers=HEADERS)
            data = r.json()['results']['bindings']

            for tag in data:
                item = tag['item']['value'][WIKIDATA_ENTITY_OFFSET:]
                itemLabel = tag['itemLabel']['value']
                # This condition removes tags, that does not have an english label,
                # all data with no label are removed
                if item != itemLabel:
                    tagsDictionary[item] = itemLabel

    return tagsDictionary


def getAllTags(data, properties):
    """This method creates a set of all labels presented in the dataset. Tags are Wikidata
       identifiers. Usually they can be labeled by the service, but because these SPARQL calls
       are already quite heavy, they can be labelled afterwards.

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