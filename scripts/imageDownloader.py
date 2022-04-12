import requests
import os.path
import json
import time
import logging

logging.basicConfig(filename=f'errors/{time.strftime("%Y%m%d-%H%M%S")}.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.ERROR)


def getPictures(inFile, outFile, directory, startIndex=-1, endIndex=-1):
    with open(inFile, 'r', encoding="UTF-8") as f:
        # people = list(json.loads(f.read()).values())
        people = json.loads(f.read())
        peopleList = list(people.values())

    if startIndex == -1:
        startIndex = 0
    if endIndex == -1:
        endIndex = len(peopleList)

    headers = {
        "User-Agent": "wikipeople-bot/0.0 (https://github.com/dreamwaffer/wikipeople; kotrblu2@fel.cvut.cz)"
    }
    session = requests.Session()

    errors = []
    exceptionCounter = 0
    start = time.time()
    for i in range(startIndex, endIndex):
        try:
            person = peopleList[i]
            if 'image' in person:
                if 'url' in person['image']:
                    response = session.get(person['image']['url'], headers=headers)
                    # 1 refers to the extension and 0 would refer to the file name
                    with open(f'{directory}/{person["wikidataID"]}{os.path.splitext(person["image"]["fileName"])[1]}', "wb+") as f:
                        if response.ok:
                            f.write(response.content)
                        else:
                            errors.append(person)
                else:
                    wikidataID = person['wikidataID']
                    del people[wikidataID]['image']
        except:
            exceptionCounter += 1
            print(exceptionCounter)
            logging.exception('exception')
            logging.exception(json.dumps(person, ensure_ascii=False, indent=2))
            errors.append(person)

        if i % 1000 == 0:
            print(f'currently at {i/endIndex*100}%')

    end = time.time()
    print(end - start)
    logging.error(json.dumps(errors, ensure_ascii=False, indent=2))

    with open(outFile, 'w', encoding="UTF-8") as f:
        json.dump(people, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    # getPictures('errors/error_jsons/image_name_broken.json', 'errors/error_jsons/pics')
    # getPictures('outputs/dated/2022_03_27_1.json', 'outputs/test/pics')
    getPictures('indata.json', 'outdata.json', 'pics')

    # print(requests.utils.unquote(getFileName('Sir_Peter_Courtney_Quennell;_James_Stephens.jpg')))

    # with open('outputs/dated/2022_03_27_1.json', 'r', encoding="UTF-8") as f:
    #     people = list(json.loads(f.read()).values())
    #     print(people[227])