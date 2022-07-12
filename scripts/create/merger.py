# Module name: Merger
# Purpose: This module contains auxiliary functions to merge data into various subsets as well as functions for merging
#          certain attributes.

import json
from functools import reduce
import random

from tqdm import tqdm

from constants import START_YEAR, END_YEAR, DATA_DIRECTORY, YEAR_STEP, YEAR_OFFSET, PROPERTIES_TO_MERGE
from create.utils import addDistinctValues, readData
from create import transformer


def mergeListOfValues(data):
    """This method merges list of values into only one value for all people in data that are passed as an argument.

        Keyword arguments:
        data -- processed data from sparql endpoint
    """

    for person in tqdm(data.values(), desc='mergeListOfValues', miniters=int(len(data) / 100)):
        for property in PROPERTIES_TO_MERGE:
            if property in person and isinstance(person[property], list):
                if len(person[property]) == 1:
                    person[property] = person[property][0]
                else:
                    person[property] = reduce(reduceDate, person[property])
    return data


def reduceDate(date1, date2):
    """This method reduces two dates into one. E.g. there might be multiple
       birth dates for one person. This method returns only one.
       Usually person with multiple birth dates has one marked as only the birth year
       and the other one as the real birth date. The birth year is entered as YEAR-01-01.
       The real birth dates are preffered, if there are two of them then random one is returned.

        Keyword arguments:
        date1 -- first date
        date2 -- second date
    """
    if date1[:YEAR_OFFSET] == date2[:YEAR_OFFSET]:
        # -01-01 means, that wikidata record contains just year intead the full date
        # so we can choose the other one instead which is more likely to be the full date
        if date1[YEAR_OFFSET:] == '-01-01':
            return date2
        elif date2[YEAR_OFFSET:] == '-01-01':
            return date1

    return random.choice([date1, date2])


def mergeDatasets(datasets):
    """This method merges all datasets from list that is passed as an argument.

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
                    addDistinctValues(property, value, result[person['wikidataID']])
            else:
                result[person['wikidataID']] = person

    # Merging dataset can create new lists in dataset, those lists has to be flatten
    # but this line would slow it down too much, so it is just done manually in the processCPU part.
    # result = mergeListOfValues(result)

    return result


def mergeAllData():
    """This method merges data from all years into one dictionary so calculations can be performed on
       all the data.

        Keyword arguments:
        None
    """

    data = {}
    dataList = []
    for year in range(START_YEAR, END_YEAR, YEAR_STEP):
        dataList.append(readData(f'{DATA_DIRECTORY}/{year}.json'))
        data = mergeDatasets(dataList)

    return data


def splitAllData(data):
    """This method split merged data into data bins defined in YEAR_STEP.

        Keyword arguments:
        data -- processed data from sparql endpoint
    """

    yearData = {year: {} for year in range(START_YEAR, END_YEAR, 1)}

    for key, person in data.items():
        year = int(person['birthDate'][:YEAR_OFFSET])
        yearData[year][key] = person

    if YEAR_STEP == 1:
        return yearData

    yearStepData = {f'{year}_{year + YEAR_STEP}': {} for year in
                    range(START_YEAR, END_YEAR, YEAR_STEP)}
    for lowerLimit in range(START_YEAR, END_YEAR, YEAR_STEP):
        upperLimit = lowerLimit + YEAR_STEP
        yearRangeData = [yearData[i] for i in range(lowerLimit, upperLimit)]
        yearStepData[f'{lowerLimit}_{upperLimit}'] = mergeDatasets(yearRangeData)
    return yearStepData


def mergeAllDataForTrainingAge():
    """This method merges data from all years into one dictionary and filter out those data not suitable for
       age estimation model training.

        Keyword arguments:
        None
    """

    allData = []
    for year in tqdm(range(START_YEAR, END_YEAR, YEAR_STEP),
                     desc='mergeAllDataForTrainingAge'):
        data = readData(f'{DATA_DIRECTORY}/{year}.json')
        data = transformer.toTrainingPeople(data)
        data = transformer.toImageData(data)
        data = transformer.toImagesBetween17And80(data)
        data = transformer.toImagesWithoutTif(data)
        allData.extend(data)

    return allData


def mergeAllDataForTrainingGender():
    """This method merges data from all years into one dictionary and filter out those data not suitable for
       gender estimation model training.

        Keyword arguments:
        None
    """

    allData = []
    for year in tqdm(range(START_YEAR, END_YEAR, YEAR_STEP),
                     desc='mergeAllDataForTrainingGender'):
        data = readData(f'{DATA_DIRECTORY}/{year}.json')
        data = transformer.toTrainingPeople(data)
        data = transformer.toPeopleWithGender(data)
        data = transformer.toImageData(data)
        data = transformer.toImagesWithoutTif(data)
        allData.extend(data)

    return allData


def mergeAllDataForTraining():
    """This method merges data from all years into one dictionary and filter out those data not suitable for
       model training.

        Keyword arguments:
        None
    """

    allData = []
    for year in tqdm(range(START_YEAR, END_YEAR, YEAR_STEP),
                     desc='mergeAllDataForTraining'):
        data = readData(f'{DATA_DIRECTORY}/{year}.json')
        data = transformer.toTrainingPeople(data)
        data = transformer.toImageData(data)
        data = transformer.toImagesWithoutTif(data)
        allData.extend(data)

    return allData


def mergeAllDataForEvaluation():
    """This method merges data from all years into one dictionary and filter out those data not suitable for
       evaluation.

        Keyword arguments:
        None
    """

    allData = []
    for year in tqdm(range(START_YEAR, END_YEAR, YEAR_STEP),
                     desc='mergeAllDataForEvaluation'):
        data = readData(f'{DATA_DIRECTORY}/{year}.json')
        data = transformer.toTrainingPeople(data)
        data = transformer.toPeopleWithWikipedia(data)
        data = transformer.toImageDataEvaluation(data)
        allData.extend(data)

    return allData