import re
from datetime import datetime
from tqdm import tqdm

import constants

def addAgeToImages(data):
    """This method adds age to all people in data.

        Keyword arguments:
        data -- processed data from sparql endpoint
    """
    for person in tqdm(data.values(), desc='addAgeToImages', miniters=int(len(data) / 100)):
        if 'images' in person:
            for image in person['images'].values():
                # # TODO smazat nasledujici radek
                # image['age'] = None
                addAgeToImage(image, person)

    return data


def addAgeToImage(image, person):
    """This method adds age to image that belongs to certain person,
       the strategy is to get all years from date, caption and filename then remove those that does not fit
       into the range and then calculate median.
       This median is then returned, None is returned if there is no value, which can be used.

        Keyword arguments:
        image -- specific image to add age to
        person -- specific person the image belongs to
    """
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

    sortedStats = {k: v for k, v in sorted(stats.items(), key=lambda item: item[1], reverse=True)}

    for year in sortedStats.keys():
        age = year - int(person['birthDate'][:constants.YEAR_OFFSET])
        if 0 < age < 110:
            image['age'] = age
            break

    # counter = 0
    # # how to make this more pythonic, bruh? This sh*t ugly AF
    # while True:
    #     if counter < len(sortedStats):
    #         year = list(sortedStats.keys())[counter]
    #         counter += 1
    #     else:
    #         image['age'] = None
    #         break
    #     if year is None:
    #         image['age'] = None
    #         break
    #     else:
    #         age = year - int(person['birthDate'][:constants.YEAR_OFFSET])
    #         if 0 < age < 100:
    #             image['age'] = age
    #             break


def findPotentialYears(text):
    """This method finds all potential years in string.

        Keyword arguments:
        text -- string to search years in
    """
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