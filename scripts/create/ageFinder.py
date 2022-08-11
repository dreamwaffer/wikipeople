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
    """This method adds age to image that belongs to certain person.
       For simplicity only years are used to calculate the age of a person in an image,
       therefore following description use 'image year' to refer to the date of image creation
       and 'birth year' to refer to the birth date of a person.
       Image is annotated with the age of the person found in it.
       This process is based on very simple heuristic algorithm.
       Firstly, the script finds the year which is most likely the image year.
       This is done by gathering all years (four digits in a range from 1800 to 2500)
       found in date and caption attributes as well as in the image file name.
       All found years are stored in a list. Then those that do not fit into the possible range
       are removed. Possible range is defined as a range between birth and death date of a person
       the image belongs to and between 0 and 110 exclusively.
       In the end the most common value is found and chosen as the image year.
       Finally this birth year is subtracted from image year and found value is returned.
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
       Potential years are defined as four digits in a range from 1800 to 2500.

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