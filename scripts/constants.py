# constants.py

# OFFSETS
WIKIPEDIA_TITLE_OFFSET = 30  # base looks like this: https://en.wikipedia.org/wiki/
GENERAL_DATE_OFFSET = 10  # base looks like this: 1905-08-24T00:00:00Z
WIKIPEDIA_FILE_NAME_OFFSET = 51  # base looks like this: http://commons.wikimedia.org/wiki/Special:FilePath/
WIKIDATA_ENTITY_OFFSET = 31  # base looks like this: http://www.wikidata.org/entity/
FILE_TITLE_OFFSET = 5  # base looks like this: File:
FILE_EXT_INDEX = 1  # file extension index for os.path.splitext() 0 is for file name, 1 is for extension
YEAR_OFFSET = 4  # base looks like this: 1900-10-31

# REQUESTS
SPARQL_URL = 'https://query.wikidata.org/sparql'
MWAPI_URL = 'https://en.wikipedia.org/w/api.php'
WIKIMEDIA_COMMONS_API_URL = 'https://commons.wikimedia.org/w/api.php'
HEADERS = {
    "User-Agent": "wikipeople-bot/0.0 (https://github.com/dreamwaffer/wikipeople; kotrblu2@fel.cvut.cz)"
}

# STRUCTURES
PERSON_STRUCTURE = ['name', 'description', 'gender', 'birthDate', 'deathDate', 'nationality', 'occupation', 'images',
                    'wikipediaTitle', 'wikidataID']
IMAGE_STRUCTURE = ['year', 'caption', 'date', 'exifDate', 'url', 'fileNameLocal', 'fileNameWiki', 'extension', 'age',
                   'faces']
FACE_STRUCTURE = ['box', 'score']


BROKEN_DATA = ['.well-known/genid']
PROPERTIES_WITH_TAGS = ['gender', 'nationality', 'occupation']
PROPERTIES_TO_MERGE = ['birthDate', 'deathDate']
PERSON_PROPERTIES_FOR_TRAINING = ['gender', 'birthDate', 'deathDate', 'nationality', 'occupation']
IMAGE_PROPERTIES_FOR_TRAINING = ['age', 'faces', 'fileNameLocal']
FACES_PROPERTIES_FOR_TRAINING = ['box', 'score']

IMAGES_DIRECTORY = '../../images'
DATA_DIRECTORY = '../../data'
DATASET_DIRECTORY = '../../dataset'
STATS_DIRECTORY = '../../stats'
LOGS_DIRECTORY = '../../logs'
AGE_DB_IMAGES_DIRECTORY = '../../AgeDB/AgeDB'

ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.jpe', '.png', '.tif', '.tiff', '.webp', '.sr', '.ras', '.pbm', '.pgm', '.ppm',
                      '.jp2', '.dib']
BANNED_EXTENSIONS = ['.tif', '.tiff']

FACE_BOX_MULTIPLIER = 1.5
FACES_MIN_OCCURENCES = 100
IMAGES_SIZE = 128
START_YEAR = 1840
END_YEAR = 2015
YEAR_STEP = 1
TRAIN, VAL, TEST = 0.6, 0.2, 0.2
ONE_TEST_CONSTANT = 8000
