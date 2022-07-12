# Module name: AgeFinder
# Purpose: This module contains functions to determine the year the image was created.

import re

from datetime import datetime
from tqdm import tqdm

from constants import START_YEAR, YEAR_OFFSET


def addAgeToImages(data):
    """This method adds age to all people in passed dataset.

        Keyword arguments:
        data -- processed data from sparql endpoint
    """

    for person in tqdm(data.values(), desc='addAgeToImages', miniters=int(len(data) / 100)):
        if 'images' in person:
            for image in person['images'].values():
                addAgeToImage(image, person)

    return data


def addAgeToImage(image, person):
    """This method adds age to image that belongs to certain person,
       the strategy is to get all years from date, caption and file name then remove those that does not fit
       into the possible range. Possible range is the range between birth and death date and between 0 and 110
       exclusively. In the end median is calculated from all the possible data and returned.
       None is returned if there is no value, which can be used.

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
        if isYearInRange(year, person) and START_YEAR <= year <= datetime.now().year:
            if year in stats:
                stats[year] += 1
            else:
                stats[year] = 1

    sortedStats = {k: v for k, v in sorted(stats.items(), key=lambda item: item[1], reverse=True)}

    for year in sortedStats.keys():
        age = year - int(person['birthDate'][:YEAR_OFFSET])
        if 0 < age < 110:
            image['age'] = age
            break


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
        person -- specific person to check year against
    """

    if 'birthDate' in person:
        birthYear = int(person['birthDate'][:YEAR_OFFSET])
    else:
        birthYear = 0
    if 'deathDate' in person:
        deathYear = int(person['deathDate'][:YEAR_OFFSET])
    else:
        deathYear = 3000
    if year > birthYear and year < deathYear:
        return True
    return False