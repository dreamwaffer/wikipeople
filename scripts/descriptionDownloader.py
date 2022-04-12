from bs4 import BeautifulSoup
from requests import utils
import requests

import json
import os
from urllib.parse import urlparse
import logging
import time

logging.basicConfig(filename='errors.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.ERROR)


def getFileName(url):
    parsed = urlparse(url)
    return os.path.basename(parsed.path)


# rename properties, shorten IDs (wikipedia, wikidata)
def transformData(inFile, outFile, indent=2):
    with open(inFile, 'r', encoding="UTF-8") as f:
        people = json.loads(f.read())

    newPeople = {}
    for person in people.values():
        wikidataID = person['item'][31:]
        newPerson = {}
        if 'itemLabel' in person:
            newPerson['name'] = person['itemLabel']
        if 'description' in person:
            newPerson['description'] = person['description']
        if 'sex' in person:
            if isinstance(person['sex'], str):
                newPerson['gender'] = person['sex']
            if (isinstance(person['sex'], list)):
                newPerson['gender'] = [gender for gender in person['sex']]
        if 'birthdate' in person:
            newPerson['birthDate'] = person['birthdate'][:10]
        if 'deathdate' in person:
            newPerson['deathDate'] = person['deathdate'][:10]
        if 'nationality' in person:
            if isinstance(person['nationality'], str):
                newPerson['nationality'] = person['nationality']
            if isinstance(person['nationality'], list):
                newPerson['nationality'] = [nationality for nationality in person['nationality']]
        if 'occupation' in person:
            if isinstance(person['occupation'], str):
                newPerson['occupation'] = person['occupation']
            if isinstance(person['occupation'], list):
                newPerson['occupation'] = [occupation for occupation in person['occupation']]
        if 'image' in person:
            newPerson['image'] = {
                'fileName': utils.unquote(getFileName(person['image'])),
                'caption': [],
                'date': []
            }
        if 'legend' in person:
            newPerson['image']['caption'].append(person['legend'])
        if 'imageDate' in person:
            newPerson['image']['date'].append(person['imageDate'][:10])
        if 'article' in person:
            newPerson['wikipediaTitle'] = person['article'][30:]
        if 'item' in person:
            newPerson['wikidataID'] = wikidataID

        newPeople[wikidataID] = newPerson

    print(len(newPeople))

    with open(outFile, 'w', encoding="UTF-8") as f:
        json.dump(newPeople, f, ensure_ascii=False, indent=indent)


def getMetadataAndLink(inFile, outFile, chunkSize=50, indent=2):
    with open(inFile, 'r', encoding="UTF-8") as f:
        people = json.loads(f.read())

    url = 'https://en.wikipedia.org/w/api.php'
    # url = 'https://commons.wikimedia.org/w/api.php'
    headers = {
        "User-Agent": "wikipeople-bot/0.0 (https://github.com/dreamwaffer/wikipeople; kotrblu2@fel.cvut.cz)"
    }

    # example
    # https://commons.wikimedia.org/w/api.php?action=query&prop=pageimages|imageinfo&iiprop=metadata|extmetadata&piprop=original&titles=File:Ayn_Rand_(1943_Talbot_portrait).jpg&formatversion=2&format=json

    params = {
        'action': 'query',
        'titles': '',
        'prop': 'pageimages|imageinfo',
        'piprop': 'original',
        'iiprop': 'extmetadata',
        'format': 'json',
        'formatversion': 2
    }

    titles = ""
    titlesToID = {}
    counter = 0
    errors = []
    for index, person in enumerate(people.values()):
        if 'image' in person:
            counter += 1
            titles = f'{titles}|File:{person["image"]["fileName"]}'
            titlesToID[f'File:{person["image"]["fileName"].replace("_"," ")}'] = people[person['wikidataID']]
            if counter >= chunkSize or counter == len(people):
                # start = time.time()
                titles = titles[1:]  # to strip the |File: at the beginning
                params['titles'] = titles
                r = requests.get(url=url, params=params, headers=headers)
                data = r.json()['query']['pages']
                titles = ""
                counter = 0
                # end = time.time()
                # print(end - start)

                for image in data:
                    try:
                        foundPerson = titlesToID[image['title']]
                        metadata = image['imageinfo'][0]['extmetadata']
                        if 'DateTime' in metadata:
                            foundPerson['image']['exifDate'] = metadata['DateTime']['value']
                        if 'original' in image:
                            foundPerson['image']['url'] = image['original']['source']
                        if 'ImageDescription' in metadata:
                            caption = metadata['ImageDescription']['value']
                            if caption not in foundPerson['image']['caption']: #if the new caption is different add it
                                soup = BeautifulSoup(caption, features="html.parser")
                                foundPerson['image']['caption'].append(soup.get_text())
                        if 'DateTimeOriginal' in metadata:
                            date = metadata['DateTimeOriginal']['value']
                            if date not in foundPerson['image']['date']:
                                soup = BeautifulSoup(date, features="html.parser")
                                foundPerson['image']['date'].append(soup.get_text())
                    except KeyError:
                        errors.append(foundPerson)
                        logging.exception("Exception occurred")
                        logging.error(json.dumps(image, ensure_ascii=False, indent=2))



        if index % 50000 == 0:
            print(f'currently at {index} out of {len(people)}')

    logging.error(json.dumps(errors, ensure_ascii=False, indent=2))
    with open(outFile, 'w', encoding="UTF-8") as f:
        json.dump(people, f, ensure_ascii=False, indent=indent)

if __name__ == '__main__':
    getMetadataAndLink('outputs/dated/2022_03_27.json', 'outputs/dated/2022_03_27_1.json')
    # transformData('outputs/processed/mwapi_img_added.json','outputs/dated/2022_03_27.json')
    # print(getFileName('http://commons.wikimedia.org/wiki/Special:FilePath/Olivier%20De%20Schutter%20in%202019%20%28cropped%29.jpg'))
    # print(getFileName('https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Nikolaev_commune_2008_stairs_01.jpg/37px-Nikolaev_commune_2008_stairs_01.jpg'))

    # with open('outputs/dated/2022_03_27.json', 'r', encoding="UTF-8") as f:
    #     people = json.loads(f.read())
    #
    # allPeopleCount = len(people)
    #
    #
    # peopleWithPropertyCount = 0
    # for person in people.values():
    #     if 'image' in person and 'imageCaption' in person and 'imageDate' in person:
    #         peopleWithPropertyCount += 1
    #
    # print(f"There are {peopleWithPropertyCount} with all properties out of {allPeopleCount} people in total")
    #
    # url = 'https://en.wikipedia.org/w/api.php'
    # title = requests.utils.unquote('File:Kardinal%20Maurer%20am%2031.05.1981%20in%20K%C3%A4rlich.jpg')
    # params = {
    #     'action': 'query',
    #     'titles': title,
    #     'prop': 'pageimages|imageinfo',
    #     'piprop': 'original',
    #     'iiprop': 'extmetadata',
    #     'format': 'json',
    #     'formatversion': 2
    # }
    # headers = {
    #     "User-Agent": "wikipeople-bot/0.0 (https://github.com/dreamwaffer/wikipeople; kotrblu2@fel.cvut.cz)"
    # }
    # r = requests.get(url=url, params=params, headers=headers)
    # data = r.json()['query']['pages']
    # print(json.dumps(data, ensure_ascii=False, indent=2))
