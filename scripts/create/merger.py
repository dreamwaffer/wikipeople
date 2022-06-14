import json
from functools import reduce
import random

from tqdm import tqdm

import constants
from create import utils


def mergeListOfValues(data):
    """This method merges list of values into only one value for all people in data.

        Keyword arguments:
        data -- processed data from sparql endpoint
    """
    for person in tqdm(data.values(), desc='mergeListOfValues', miniters=int(len(data) / 100)):
        for property in constants.PROPERTIES_TO_MERGE:
            if property in person and isinstance(person[property], list):
                if len(person[property]) == 1:
                    person[property] = person[property][0]
                else:
                    person[property] = reduce(reduceDate, person[property])
    return data


def reduceDate(date1, date2):
    """This method reduces two dates into one. E.g. there might be multiple
       birth dates for one person. This method returns only one.

        Keyword arguments:
        date1 -- first date
        date2 -- second date
    """
    if date1[:constants.YEAR_OFFSET] == date2[:constants.YEAR_OFFSET]:
        # -01-01 means, that wikidata record contains just year intead the full date
        # so we can choose the other one instead which is more likely to be the full date
        if date1[constants.YEAR_OFFSET:] == '-01-01':
            return date2
        elif date2[constants.YEAR_OFFSET:] == '-01-01':
            return date1

    return random.choice([date1, date2])


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
                    utils.addDistinctValues(property, value, result[person['wikidataID']])
            else:
                result[person['wikidataID']] = person

    return result