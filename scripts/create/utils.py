import os
from urllib.parse import urlparse, unquote
import json
from tqdm import tqdm

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
            node[property].extend(item for item in value if item not in node[property])
            # node[property] = value + list(set(node[property]) - set(value))
        elif isinstance(value, str) and isinstance(node[property], list):
            if value not in node[property]:
                node[property].append(value)
        elif isinstance(value, list) and isinstance(node[property], str):
            if node[property] not in value:
                value.append(node[property])
        elif isinstance(node[property], dict):
            for k, v in value.items():
                if k in node[property]:  # tento check je mozna zbytecny protoze uz je zahrnut v tom na radku 19, if property in node
                    addDistinctValues(k, v, node[property])
                else:
                    node[property][k] = v
    else:
        node[property] = value


def getLastPartOfURL(url):
    """This method returns last part of passed URL, it can be either file, ID, basically anything behind the last slash,
       be aware of this methods limitation, if there is a special character like ? or ; in the last part of URL,
       the method would not work properly and it is better to use custom string strip

        Keyword arguments:
        url -- desired url
    """
    return unquote(os.path.basename(urlparse(url).path))


def saveData(data, file, indent=2):
    """This method saves data to a file with a specific indent

        Keyword arguments:
        data -- processed data from sparql endpoint
        file -- file and location to save data to
        indent -- number of spaces for nicer formatting of JSON (default: 2)
    """

    with open(file, 'w', encoding="UTF-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def readData(file):
    """This method reads data from a file

        Keyword arguments:
        file -- file and location to read data from
    """

    with open(file, 'r', encoding="UTF-8") as f:
        data = json.loads(f.read())
    return data


def countProperty(data, properties={}, verbose=False):
    """This method does a basic statistics on data and counts desired properties

        Keyword arguments:
        data -- processed data from sparql endpoint
        properties -- dictionary of desired properties to count with assigned boolean value,
                      True -- add all values from lists
                      False -- only count a number of occurences of property
                      eg: {'images': True} will count number of all images in data, adding the length of the list
                      in comparison to: {'deathDate': False} will only count number of deathDate is present in data.

                      NOTE: all properties with non-list values are percieved as False
    """

    stats = {property: 0 for property in properties}

    if isinstance(data, dict):
        data = data.values()

    for person in tqdm(data, desc='countProperty', miniters=int(len(data) / 100)):
        for property in properties:
            if property in person:
                # properties[property] is a boolean value passed to the method in dictionary
                if isinstance(person[property], list) and \
                        properties[property] or \
                        isinstance(person[property], dict) and \
                        properties[property]:
                    stats[property] += len(person[property])
                    if len(person[property]) > 1:
                        print(person['fileNameLocal'])
                else:
                    stats[property] += 1

    if verbose:
        print(f'Total number of people: {len(data)}')
        for property in properties:
            print(f'{property}: {properties[property]} = {stats[property]}')

    return stats