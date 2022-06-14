import constants
from create import ageFinder, corrector, merger, utils, transformer, setupCPU, sorter, labeler, downloader


def fullDataDownload():
    """This method create the database, download all the data and process it.
       Only the CPU part.

       Keyword arguments:
        None
    """
    setupCPU.config()
    for year in range(constants.START_YEAR, constants.END_YEAR, constants.YEAR_STEP):
        print(f'Starting year: {year}!')
        data = downloader.getRawSparqlData(year, year + constants.YEAR_STEP)
        data = transformer.removeBrokenData(data)
        data = transformer.simplifySparqlData(data)
        data = transformer.processSparqlData(data)
        data = merger.mergeListOfValues(data)

        data = labeler.labelTags(data)
        data = downloader.getThumbnails(data)
        data = downloader.getMetadataAndLinks(data)

        data = ageFinder.addAgeToImages(data)

        data = sorter.orderData(data)
        data = sorter.changeOrderOfProperties(data)
        utils.saveData(data, f'{constants.DATA_DIRECTORY}/{year}.json')

        data = downloader.getPictures(data)
        data = corrector.removeBrokenImages(data)

        # probably useless, needs to be ordered after faces are added too
        # careful about that as it can sort the box values too
        data = sorter.orderData(data)
        data = sorter.changeOrderOfProperties(data)
        utils.saveData(data, f'{constants.DATA_DIRECTORY}/{year}.json')


if __name__ == '__main__':
    fullDataDownload()