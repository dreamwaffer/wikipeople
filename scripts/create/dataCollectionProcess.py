# Module name: DataCollectionProcess
# Purpose: This module contains main function for creating the dataset.

import os

from create.ageFinder import addAgeToImages
from create.corrector import removeBrokenImages
from create.merger import mergeListOfValues, mergeDatasets
from create.utils import readData, saveData
from create.transformer import removeBrokenData, processSparqlData, simplifySparqlData
from create.dataCollectionSetup import config
from create.sorter import orderData, changeOrderOfProperties
from create.labeler import labelTags
from create.downloader import getRawSparqlData, getThumbnails, getMetadataAndLinks, getPictures
from constants import START_YEAR, END_YEAR, YEAR_STEP, DATA_DIRECTORY


def fullDataDownload():
    """This method create the database, download all the data and process it.
       This method contains only the CPU part.

       Keyword arguments:
        None
    """

    config()
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
        data = getMetadataAndLinks(data)

        data = addAgeToImages(data)

        data = orderData(data)
        data = changeOrderOfProperties(data)
        data = mergeDatasets([foundData, data])
        data = mergeListOfValues(data)
        saveData(data, f'{DATA_DIRECTORY}/{year}.json')

        data = getPictures(data)
        data = removeBrokenImages(data)

        data = orderData(data)
        data = changeOrderOfProperties(data)
        saveData(data, f'{DATA_DIRECTORY}/{year}.json')


if __name__ == '__main__':
    fullDataDownload()