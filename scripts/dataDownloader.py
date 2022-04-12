import requests
import json
import gzip
import logging
import time

logging.basicConfig(filename='errors.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


def getDataAboutPeople(fromYear, toYear):
    url = 'https://query.wikidata.org/sparql'
    headers = {
        "User-Agent": "wikipeople-bot/0.0 (https://github.com/dreamwaffer/wikipeople; kotrblu2@fel.cvut.cz)"
    }

    with open("outputs/wikidata/errors.log", 'w', encoding="UTF-8") as logFile:
        for i in range(fromYear, toYear):
            success = False
            numOfErrors = 0
            # Double parantheses as an escape for a F-string, otherwise the content between them is considered a variable
            query = f'''
                SELECT DISTINCT ?item ?itemLabel ?description ?image ?legend ?imageDate ?birthdate ?deathdate ?sex ?nationality ?occupation ?article WITH {{ 
      SELECT ?item ?itemLabel ?birthdate WHERE {{
      ?item wdt:P31 wd:Q5;
        rdfs:label ?itemLabel;
        wdt:P569 ?birthdate.
      hint:Prior hint:rangeSafe "true"^^xsd:boolean.
      FILTER(("{i}-00-00"^^xsd:dateTime <= ?birthdate) && (?birthdate < "{i + 1}-00-00"^^xsd:dateTime))
      FILTER((LANG(?itemLabel)) = "en")
    }} }} as %i
    WHERE {{
      INCLUDE %i
       OPTIONAL {{ ?item schema:description ?description.   FILTER((LANG(?description)) = "en") }}
      OPTIONAL {{ ?item wdt:P734 ?lastname. }}
      OPTIONAL {{ ?item wdt:P570 ?deathdate. }}
      OPTIONAL {{ ?item wdt:P27 ?nationality . }}
      optional {{ ?item wdt:P106 ?occupation . }}
      OPTIONAL {{ ?item wdt:P21 ?sex. }}
      OPTIONAL {{
        ?item p:P18 ?stat.
        ?stat ps:P18 ?image.
        OPTIONAL {{ ?stat pq:P2096 ?legend. FILTER (langmatches(lang(?legend), "en")) }}
        OPTIONAL {{ ?stat pq:P585 ?imageDate. }}
      }}
      ?article schema:about ?item;
          schema:isPartOf <https://en.wikipedia.org/>.
    }}
                '''
            while not success:
                try:
                    r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers)
                    data = r.json()
                    with open(f"outputs/wikidata/{i}.json", "w", encoding="UTF-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                except requests.exceptions.RequestException as e:
                    numOfErrors += 1
                    success = False
                    logFile.write(str(e))
                    print("Request error number " + str(numOfErrors))
                except ValueError as ve:
                    numOfErrors += 1
                    success = False
                    logFile.write(str(ve))
                    print("Timeout error number " + str(numOfErrors))
                else:
                    success = True
                finally:
                    logFile.write("Year " + str(i) + " had " + str(numOfErrors) + " errors.\n")

            print("Year " + str(i) + " finished!")
        # print(json.dumps(data, ensure_ascii=False, indent=2))


def processResults(inDir, fromYear, toYear, outFile, indent=0):
    peopleDictionary = {}
    for i in range(fromYear, toYear):
        with open(f"{inDir}/{i}.json", 'r', encoding="UTF-8") as f:
            jsonData = json.loads(f.read())

        people = jsonData['results']['bindings']
        for person in people:
            if person['item']['value'] in peopleDictionary:
                proccessedPersonObject = peopleDictionary[person['item']['value']]
                # muze se stat, ze properta nebude v processedPersonObject - nemelo by, pokud sparql vratil spravne vysledky
                addValueToAlreadyProcessedObject('occupation', person, proccessedPersonObject)
            else:
                peopleDictionary[person['item']['value']] = {}
                proccessedPersonObject = peopleDictionary[person['item']['value']]
                for key, value in person.items():
                    proccessedPersonObject[key] = value['value']

    with open(outFile, 'w', encoding="UTF-8") as f:
        json.dump(peopleDictionary, f, ensure_ascii=False, indent=indent)


def addValueToAlreadyProcessedObject(property, personObject, processedPersonObject):
    if property in personObject:
        value = personObject[property]['value']
        if (isinstance(processedPersonObject[property], str)):
            if (value != processedPersonObject[property]):
                processedPersonObject[property] = [processedPersonObject[property], value]
        if (isinstance(processedPersonObject[property], list)):
            if (value not in processedPersonObject[property]):
                processedPersonObject[property].append(value)


def addPropertyToObject(property, value, object):
    if (property in object):
        pass
    else:
        if (isinstance(object[property], str)):
            object[property] = value
        if (isinstance(object[property], list)):
            object[property].append(value)


def saveJSONToFileCompressed(object, nameOfFile):
    with gzip.open(f"{nameOfFile}.gzip", 'w') as fout:
        fout.write(json.dumps(object).encode('utf-8'))


def readJSONfromCompressedFile(nameOfFile):
    with gzip.open(nameOfFile, 'r') as fin:
        data = json.loads(fin.read().decode('utf-8'))
    return data


# Throwing away values that contains non-existent tags (.well-known)
def getAllTags(inFile, outFile, listOfProps):
    with open(inFile, 'r', encoding="UTF-8") as f:
        people = json.loads(f.read())

    tagsDict = {}

    for person in people.values():
        for prop in listOfProps:
            if prop in person:
                if (isinstance(person[prop], str)):
                    if len(person[prop]) < 60:
                        tagsDict[person[prop]] = person[prop][31:]
                if (isinstance(person[prop], list)):
                    for item in person[prop]:
                        if len(item) < 60:
                            tagsDict[item] = item[31:]

    with open(outFile, 'w', encoding="UTF-8") as f:
        json.dump(tagsDict, f, ensure_ascii=False, indent=0)
    print(len(tagsDict))


# throwing away tags that cannot be labeled, do not have a label
def createTagsDictionary(inFile, outFile, chunkSize, indent=0):
    with open(inFile, 'r', encoding="UTF-8") as f:
        tags = json.loads(f.read())

    tagsList = list(tags.values())
    tagsDictionary = {}

    url = 'https://query.wikidata.org/sparql'
    headers = {
        "User-Agent": "wikipeople-bot/0.0 (https://github.com/dreamwaffer/wikipeople; kotrblu2@fel.cvut.cz)"
    }

    for i in range(0, len(tagsList), chunkSize):
        queryValues = "wd:" + " wd:".join(tagsList[i:i + chunkSize])
        print(queryValues)
        query = f'''
            SELECT DISTINCT ?item ?itemLabel
            WHERE {{
                VALUES ?item {{ {queryValues} }}
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }}
        '''
        r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers)
        data = r.json()['results']['bindings']

        for tag in data:
            item = tag['item']['value']
            itemLabel = tag['itemLabel']['value']
            if item[31:] != itemLabel:
                tagsDictionary[item] = itemLabel

    with open(outFile, 'w', encoding="UTF-8") as f:
        json.dump(tagsDictionary, f, ensure_ascii=False, indent=indent)


# Not working correctly, will miss quite some tags, could be fixed with sub-classes, but results in timeout
# p:P31/ps:P31/(p:P279/ps:P279)* instead of wdt:P31
def createTagsDictionaryDup(outFile, indent=0):
    url = 'https://query.wikidata.org/sparql'
    headers = {
        "User-Agent": "wikipeople-bot/0.0 (https://github.com/dreamwaffer/wikipeople; kotrblu2@fel.cvut.cz)"
    }
    query = f'''
        SELECT DISTINCT ?item ?itemLabel 
        WHERE {{
            VALUES ?o {{ wd:Q28640 wd:Q12737077 wd:Q6256 wd:Q3624078 wd:Q99541706 wd:Q48264 wd:Q4369513 }}
            ?item wdt:P31 ?o.
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
    '''
    r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers)
    data = r.json()['results']['bindings']
    tagsDictionary = {}
    for tag in data:
        tagsDictionary[tag['item']['value']] = tag['itemLabel']['value']

    with open(outFile, 'w', encoding="UTF-8") as f:
        json.dump(tagsDictionary, f, ensure_ascii=False, indent=indent)


def translateTags(person, dictionary, listOfTagProps):
    for key, value in list(person.items()):
        if key in listOfTagProps:
            if (isinstance(value, str)):
                if value in dictionary:
                    person[key] = dictionary[value]
                else:
                    del person[key]
            if (isinstance(value, list)):
                value = [item for item in value if item in dictionary]
                for index, item in enumerate(value):
                    value[index] = dictionary[item]
                person[key] = value


def translateAllTags(peopleFile, dictionaryFile, outFile, indent=0):
    with open(peopleFile, 'r', encoding="UTF-8") as f:
        people = json.loads(f.read())

    with open(dictionaryFile, 'r', encoding="UTF-8") as f:
        dictionary = json.loads(f.read())

    for person in people.values():
        translateTags(person, dictionary, ['sex', 'occupation', 'nationality'])
        # except AttributeError:
        #     print(index)
        #     print(person)

    with open(outFile, 'w', encoding="UTF-8") as f:
        json.dump(people, f, ensure_ascii=False, indent=indent)


def getListOfPeopleWithoutImage(inFile, outFile, indent=0):
    with open(inFile, 'r', encoding="UTF-8") as f:
        people = json.loads(f.read())

    peopleWithoutPictures = {
        'names': [],
        'wikidataIDs': [],
        'wikipediaIDs': []
    }

    for person in people.values():
        if 'image' not in person:
            peopleWithoutPictures['names'].append(person['itemLabel'])
            peopleWithoutPictures['wikidataIDs'].append(person['item'])
            peopleWithoutPictures['wikipediaIDs'].append(person['article'][30:])

    with open(outFile, 'w', encoding="UTF-8") as f:
        json.dump(peopleWithoutPictures, f, ensure_ascii=False, indent=indent)


def addThumbnailsFromWikipedia(inPeopleFile, noImagePeopleFile, outPeopleFile, chunkSize=50, indent=0):
    with open(inPeopleFile, 'r', encoding="UTF-8") as f:
        people = json.loads(f.read())

    with open(noImagePeopleFile, 'r', encoding="UTF-8") as f:
        noImagePeople = json.loads(f.read())
        nipNames = noImagePeople['names']
        nipTitles = noImagePeople['wikipediaIDs']

    url = 'https://en.wikipedia.org/w/api.php'
    headers = {
        "User-Agent": "wikipeople-bot/0.0 (https://github.com/dreamwaffer/wikipeople; kotrblu2@fel.cvut.cz)"
    }

    # example:
    # https://en.wikipedia.org/w/api.php?action=query&titles=Ayn%20Rand&prop=pageprops&format=json&formatversion=2

    params = {
        'action': 'query',
        'prop': 'pageprops',
        'titles': '',
        'format': 'json',
        'formatversion': 2
    }

    errors = []
    # newPeople = {}
    # start = time.time()
    for i in range(0, len(nipNames), chunkSize):
        # for i in range(0, 100, chunkSize):
        titles = "|".join(nipTitles[i:i + chunkSize])
        params['titles'] = titles
        r = requests.get(url=url, params=params, headers=headers)
        data = r.json()['query']['pages']
        # print(json.dumps(data, ensure_ascii=False, indent=2))
        # break
        try:
            for page in data:
                if 'pageprops' in page:
                    pageprops = page['pageprops']
                    wikidataID = f'http://www.wikidata.org/entity/{pageprops["wikibase_item"]}'
                    if 'page_image' in pageprops:
                        #         people[nipWikidataIDs[i]]['image'] = page['thumbnail']['source'] # tady je chyba, nemelo by to být i ale index od page in data
                        #         newPeople[wikidataID] = people[wikidataID]
                        #         newPeople[wikidataID]['image'] = pageprops['page_image']
                        people[wikidataID]['image'] = pageprops['page_image']
                    elif 'page_image_free' in pageprops:
                        # newPeople[wikidataID] = people[wikidataID]
                        # newPeople[wikidataID]['image'] = pageprops['page_image_free']
                        people[wikidataID]['image'] = pageprops['page_image_free']
        except KeyError as e:
            errors.append(wikidataID)
            logging.exception("Exception occurred")

        if i % 50000 == 0:
            print(f'currently at {i} out of {len(nipTitles)}')

    with open(outPeopleFile, 'w', encoding="UTF-8") as f:
        json.dump(people, f, ensure_ascii=False, indent=indent)


def getImagesFromDbPedia(inPeopleFile, noImagePeopleFile, outPeopleFile, chunkSize=50, indent=0):
    # with open(inPeopleFile, 'r', encoding="UTF-8") as f:
    #     people = json.loads(f.read())

    with open(noImagePeopleFile, 'r', encoding="UTF-8") as f:
        noImagePeople = json.loads(f.read())
        nipNames = noImagePeople['names']
        nipWikidataIDs = noImagePeople['wikidataIDs']


def prepareNamesForDBpediaQuery(inFile, outFile):
    with open(inFile, 'r', encoding="UTF-8") as f:
        people = json.loads(f.read())['wikipediaIDs']

    prohibitedChars = ['(', ')', '.', ',']

    with open(outFile, 'w', encoding="UTF-8") as f:
        for person in people:
            if any(c in prohibitedChars for c in person):
                f.write(f'<http://dbpedia.org/resource/{person}>\n')
            else:
                f.write(f'res:{person}\n')


def countProperty(inFile, properties=[]):
    with open(inFile, 'r', encoding="UTF-8") as f:
        people = json.loads(f.read())

    allPeopleCount = len(people)

    for property in properties:
        peopleWithPropertyCount = 0
        for person in people.values():
            if property in person:
                peopleWithPropertyCount += 1

        print(f"There are {peopleWithPropertyCount} with property: {property} out of {allPeopleCount} people in total")


def getPeopleWithoutWikidataPage(inFile, outFile):
    with open(inFile, 'r', encoding="UTF-8") as f:
        people = json.loads(f.read())

    peopleWithoutWikidataPage = []
    for person in people:
        if 'wikidata' not in person:
            peopleWithoutWikidataPage.append(person['title'])

    print(len(peopleWithoutWikidataPage))
    print(len(people))

    with open(outFile, 'w', encoding="UTF-8") as f:
        json.dump(peopleWithoutWikidataPage, f, ensure_ascii=False, indent=2)


def transformProperty(inFile, outFile, property, function):
    with open(inFile, 'r', encoding="UTF-8") as f:
        data = json.loads(f.read())

    for item in data:
        if property in item:
            item[property] = function(item[property])

    with open(outFile, 'w', encoding="UTF-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)




if __name__ == '__main__':
    # prepareNamesForDBpediaQuery('outputs/processed/all_no_image.json', 'outputs/processed/dbpedia_names.txt')
    # transformProperty('outputs/processed/all_processed_labeled.json', 'ouptuts/processed/key_transformed.json')
    # getListOfPeopleWithoutImage("outputs/processed/all_processed_labeled.json", "outputs/processed/all_no_image.json", indent=2)
    # addThumbnailsFromWikipedia("outputs/processed/all_processed_labeled.json", "outputs/processed/all_no_image.json", "outputs/processed/mwapi_img_added.json", indent=2)
    # translateAllTags("outputs/processed/all_processed.json", "outputs/allTagsDictLabeled.json", "outputs/all_processed_labeled.json", indent=2)
    # getAllTags("outputs/processed/all_processed.json", "outputs/allTagsDict.json", ['sex', 'nationality', 'occupation'])
    # getDataAboutPeople(1919, 2010)
    # processResults("outputs/wikidata", 1900, 2010, "outputs/processed/all_processed.json", 2)
    countProperty('outputs/processed/mwapi_img_added.json', ['image'])
    # getPeopleWithoutWikidataPage('outputs/wikipeople_simplified.json', 'outputs/people_without_wikidata.json')
    # with open("inputs/queryResultShort.json", 'r', encoding="UTF-8") as f:
    #     jsonData = json.loads(f.read())
    #
    # print(json.dumps(jsonData, ensure_ascii=False, indent=2))
    # createTagsDictionary('outputs/tagsDictionary.json', indent=2)
    # createTagsDictionary("outputs/allTagsDict.json", "outputs/allTagsDictLabeled.json", 500)

    # data = readJSONfromCompressedFile("outputs/processed/1990_processed.gzip")
    # print(json.dumps(data, ensure_ascii=False, indent=2))

    #
    # with open("outputs/allTagsDictLabeled.json", 'r', encoding="UTF-8") as f:
    #     dictionary = json.loads(f.read())
    #
    # person = {
    #     "legend": "Sy Bartlett and Alice White",
    #     "item": "http://www.wikidata.org/entity/Q2373467",
    #     "image": "http://commons.wikimedia.org/wiki/Special:FilePath/Sy%20Bartlett%20and%20Alice%20White%201931.png",
    #     "imageDate": "1931-01-01T00:00:00Z",
    #     "description": "American writer",
    #     "birthdate": "1900-07-10T00:00:00Z",
    #     "itemLabel": "Sy Bartlett",
    #     "article": "https://en.wikipedia.org/wiki/Sy_Bartlett",
    #     "deathdate": "1978-05-29T00:00:00Z",
    #     "nationality": "http://www.wikidata.org/entity/Q30",
    #     "occupation": [
    #     "http://www.wikidata.org/entity/Q28389",
    #     "http://www.wikidata.org/entity/Q36180",
    #     "http://www.wikidata.org/entity/Q48295580",
    #     "http://www.wikidata.org/entity/Q3282637",
    #     "http://www.wikidata.org/entity/Q6625963"
    #     ],
    #     "sex": "http://www.wikidata.org/entity/Q6581097"
    # }
    #
    # translateTags(person, dictionary, ['sex', 'occupation', 'nationality'])

# SELECT ?item ?itemLabel ?birthdate
#             WHERE {{
#                 ?item wdt:P31 wd:Q5;
#                       rdfs:label ?itemLabel;
#                       wdt:P569 ?birthdate.
#                 hint:Prior hint:rangeSafe "true"^^xsd:boolean.
#                 FILTER(("{i}-00-00"^^xsd:dateTime <= ?birthdate) && (?birthdate < "{i + 1}-00-00"^^xsd:dateTime))
#                 FILTER((LANG(?itemLabel)) = "en")
#
# person = {
#     'age': 15,
#     'name': 'Lukas'
# }
#
# people = {
#     'wikipedia': person,
#     'wikidata': person
# }
# print(people)
# people['wikipedia']['age'] = 23
# print(people)
# del people['wikidata']
# print(people)

# with open('outputs/processed/example_data.json', 'r', encoding="UTF-8") as f:
#     people = json.loads(f.read())

# print(people['http://www.wikidata.org/entity/Q75804176'])
