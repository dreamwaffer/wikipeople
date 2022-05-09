# constants.py

# OFFSETS
WIKIPEDIA_TITLE_OFFSET = 30  # base looks like this: https://en.wikipedia.org/wiki/
GENERAL_DATE_OFFSET = 10  # base looks like this: 1905-08-24T00:00:00Z
WIKIPEDIA_FILE_NAME_OFFSET = 51  # base looks like this: http://commons.wikimedia.org/wiki/Special:FilePath/
WIKIDATA_ENTITY_OFFSET = 31  # base looks like this: http://www.wikidata.org/entity/
FILE_TITLE_OFFSET = 5  # base looks like this: File:
FILE_EXT_INDEX = 1  # file extension index for os.path.splitext 0 is for file name, 1 is for extension in os.path.splitext()
YEAR_OFFSET = 4 # base looks like this: 1900-10-31

SPARQL_URL = 'https://query.wikidata.org/sparql'
MWAPI_URL = 'https://en.wikipedia.org/w/api.php'
WIKIMEDIA_COMMONS_API_URL = 'https://commons.wikimedia.org/w/api.php'
HEADERS = {
    "User-Agent": "wikipeople-bot/0.0 (https://github.com/dreamwaffer/wikipeople; kotrblu2@fel.cvut.cz)"
}

PERSON_STRUCTURE = ['name', 'description', 'gender', 'birthDate', 'deathDate', 'nationality', 'occupation', 'images',
                    'wikipediaTitle', 'wikidataID']
IMAGE_STRUCTURE = ['year', 'caption', 'date', 'exifDate', 'url', 'fileNameLocal', 'fileNameWiki', 'age', 'faces']
FACE_STRUCTURE = ['box', 'score']

BROKEN_DATA = ['.well-known/genid']
PROPERTIES_WITH_TAGS = ['gender', 'nationality', 'occupation']
PROPERTIES_TO_MERGE = ['birthDate', 'deathDate']
IMAGES_DIRECTORY = '../images'
DATA_DIRECTORY = '../data'
REMOVED_DATA_DIRECTORY = 'removed'
DATASET_DIRECTORY = 'dataset'
FIX_DATA_DIRECTORY = '../fixData'
STATS_DIRECTORY = '../stats'
PATH_TO_DATA = 'data.json'
IMAGE_DOWNLOAD_REPEATS = 10
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.jpe', '.png', '.tif', '.tiff', '.webp', '.sr', '.ras', '.pbm', '.pgm', '.ppm',
                      '.jp2', '.dib']
FACE_BOX_MULTIPLIER = 1.5
START_YEAR = 1840
END_YEAR = 2015
