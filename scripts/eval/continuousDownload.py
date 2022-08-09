import os
import time
from collections import Counter

import schedule

from create.ageFinder import addAgeToImages
from create.corrector import removeBrokenImages
from create.merger import mergeListOfValues, mergeDatasets
from create.utils import readData, saveData, countProperty
from create.transformer import removeBrokenData, processSparqlData, simplifySparqlData
from create.dataCollectionSetup import config
from create.sorter import orderData, changeOrderOfProperties
from create.labeler import labelTags
from create.downloader import getRawSparqlData, getThumbnails, getMetadataAndLinks, getPictures
from constants import START_YEAR, END_YEAR, YEAR_STEP, DATA_DIRECTORY, STATS_DIRECTORY


def fullDataDownload(results, resultsAllFalse):
    """This method create the database, download all the data and process it.
       Only the CPU part.

       Keyword arguments:
        None
    """

    propertiesToCount = {
        'name': False,
        'description': False,
        'gender': True,
        'birthDate': False,
        'deathDate': False,
        'nationality': True,
        'occupation': True,
        'images': True,
        'wikipediaTitle': False
    }
    propertiesToCountAllFalse = {
        'name': False,
        'description': False,
        'gender': False,
        'birthDate': False,
        'deathDate': False,
        'nationality': False,
        'occupation': False,
        'images': False,
        'wikipediaTitle': False
    }

    config()
    totalProperties = {}
    totalPropertiesAllFalse = {}
    for year in range(START_YEAR, END_YEAR, YEAR_STEP):
        print(f'Starting year: {year}!')
        if os.path.isfile(f'{DATA_DIRECTORY}/{year}.json'):
            foundData = readData(f'{DATA_DIRECTORY}/{year}.json')
        else:
            foundData = {}
        data = getRawSparqlData(year, year + YEAR_STEP)
        data = removeBrokenData(data)
        data = simplifySparqlData(data)
        data = processSparqlData(data)
        data = mergeListOfValues(data)

        data = labelTags(data)
        data = getThumbnails(data)

        data = orderData(data)
        data = changeOrderOfProperties(data)
        data = mergeDatasets([foundData, data])
        data = mergeListOfValues(data)
        saveData(data, f'{DATA_DIRECTORY}/{year}.json')
        totalProperties = Counter(totalProperties) + Counter(countProperty(data, propertiesToCount))
        totalPropertiesAllFalse = Counter(totalPropertiesAllFalse) + Counter(
            countProperty(data, propertiesToCountAllFalse))

    results.append(totalProperties)
    resultsAllFalse.append(totalPropertiesAllFalse)
    saveData(results, f'{STATS_DIRECTORY}/results.json')
    saveData(resultsAllFalse, f'{STATS_DIRECTORY}/resultsAllFalse.json')


if __name__ == '__main__':
    # results = []
    # resultsAllFalse = []
    # fullDataDownload(results, resultsAllFalse)
    results = [
        {
            "name": 4530234,
            "description": 3390576,
            "gender": 4368710,
            "birthDate": 4530234,
            "deathDate": 1782400,
            "nationality": 3268669,
            "occupation": 5579205,
            "images": 999386,
            "wikipediaTitle": 1527647,
            "total": 4530234
        },
        {
            "name": 4530829,
            "description": 3391102,
            "gender": 4369299,
            "birthDate": 4530829,
            "deathDate": 1782603,
            "nationality": 3269215,
            "occupation": 5580290,
            "images": 999591,
            "wikipediaTitle": 1527818,
            "total": 4530829
        }
    ]
    resultsAllFalse = [
        {
            "name": 4530234,
            "description": 3390576,
            "gender": 4367891,
            "birthDate": 4530234,
            "deathDate": 1782400,
            "nationality": 2969856,
            "occupation": 3677861,
            "images": 4530234,
            "wikipediaTitle": 1527647,
            "total": 4530234
        },
        {
            "name": 4530829,
            "description": 3391102,
            "gender": 4368473,
            "birthDate": 4530829,
            "deathDate": 1782603,
            "nationality": 2970303,
            "occupation": 3678372,
            "images": 4530829,
            "wikipediaTitle": 1527818,
            "total": 4530829
        }
    ]
    # fullDataDownload(results, resultsAllFalse)

    schedule.every().day.at("01:00").do(fullDataDownload, results, resultsAllFalse)

    while True:
        schedule.run_pending()
        time.sleep(300)
