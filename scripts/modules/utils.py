from functools import reduce
import random

from tqdm import tqdm
from modules import constants


# import tensorflow as tf
# from retinaface import RetinaFace


def addDistinctValues(property, value, node):
    """This method checks for duplicate values and only adds it once,
       in case there are multiple unique values create a list for them

        Keyword arguments:
        property -- name of the property to be added
        value -- value of the property to be added
        node -- any object that contains data, object to check the duplicity against
    """

    # This check is necessary, because some records might be missing some values, which could have been
    # deleted (they were marked as unknown values - removeBrokenData).
    # If the property is missing we can just add the property-value pair.
    if property in node:
        if isinstance(node[property], str):
            if value != node[property]:
                node[property] = [node[property], value]
        elif isinstance(value, list) and isinstance(node[property], list):
            node[property] = value + list(set(node[property]) - set(value))
        elif isinstance(value, str) and isinstance(node[property], list):
            if value not in node[property]:
                node[property].append(value)
        elif isinstance(node[property], dict):
            for k, v in value.items():
                if k in node[property]:
                    addDistinctValues(k, v, node[property])
                else:
                    node[property][k] = v
    else:
        node[property] = value


def mergeListOfValues(data):
    for person in tqdm(data.values(), desc='mergeListOfValues', miniters=int(len(data) / 100)):
        if 'birthDate' in person and isinstance(person['birthDate'], list):
            person['birthDate'] = reduce(reduceDate, person['birthDate'])[0]
        if 'deathDate' in person and isinstance(person['deathDate'], list):
            person['deathDate'] = reduce(reduceDate, person['deathDate'])[0]

    return data

def reduceDate(date1, date2):
    if date1[:constants.YEAR_OFFSET] == date2[:constants.YEAR_OFFSET]:
        # -01-01 means, that wikidata record contains just year intead the full date
        # so we can choose the other one instead which is more likely to be the full date
        if date1[constants.YEAR_OFFSET:] == '-01-01':
            return date2
        elif date2[constants.YEAR_OFFSET:] == '-01-01':
            return date1
        else:
            return random.choice([date1, date2])
