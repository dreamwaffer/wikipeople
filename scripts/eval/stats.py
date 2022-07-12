import copy
from collections import Counter, OrderedDict
import os

import matplotlib.pyplot as plt
from tqdm import tqdm

import constants
from create.utils import readData, saveData, countProperty, addToDictionary
from create.transformer import toTrainingPeople, toEvaluationSample


def addlabels(x, y):
    for i in range(len(x)):
        plt.text(i, y[i] + 100, y[i], ha='center')


def plotBarChart(stats, file, graphDescription):
    plt.clf()
    plt.close()
    plt.figure(figsize=(10, 7))
    plt.bar(list(stats.keys()), stats.values(), color='green')
    plt.ylabel(graphDescription['y'])
    plt.xlabel(graphDescription['x'])
    plt.title(graphDescription['title'])
    plt.savefig(file, dpi=300)


def plotLineChart(stats, file, graphDescription):
    plt.clf()
    plt.close()
    plt.plot(list(stats['all'].keys()), stats['all'].values(), color='green', label='all')
    plt.plot(list(stats['male'].keys()), stats['male'].values(), color='blue', label='male')
    plt.plot(list(stats['female'].keys()), stats['female'].values(), color='red', label='female')
    plt.ylabel(graphDescription['y'])
    plt.xlabel(graphDescription['x'])
    plt.legend()
    plt.title(graphDescription['title'])
    plt.savefig(file, dpi=300)


def plotPieChart(stats, file, graphDescription):
    plt.clf()
    plt.close()
    plt.pie(list(stats.values()), startangle=90, radius=1.2, autopct='%.2f%%')
    plt.legend(labels=list(stats.keys()), bbox_to_anchor=(1, 0), loc="lower right",
               bbox_transform=plt.gcf().transFigure)
    plt.title(graphDescription['title'])
    plt.savefig(file, dpi=300)


def getAllInfo(datasetOnly=False):
    allStats = {
        'age': {
            'male': {key: 0 for key in range(0, 111)},
            'female': {key: 0 for key in range(0, 111)},
            'all': {key: 0 for key in range(0, 111)}
        },
        'faces': {},
        'birthYear': {},
        'gender': {
            'male': 0,
            'female': 0,
            'other': 0
        },
        'extensions': {},
        'usableImages': {
            'only faces': 0,
            'only age': 0,
            'faces and age': 0
        },
        'resolution': {}
    }

    graphsDescriptions = {
        'age': {
            'x': 'age',
            'y': '# of occurences in dataset',
            'title': 'Distribution of age in dataset'
        },
        'faces': {
            'x': '# of faces detected',
            'y': '# of occurences in dataset',
            'title': 'Distribution of detected faces'
        },
        'birthYear': {
            'x': 'Birth years',
            'y': '# of occurences in dataset',
            'title': 'Distribution of birth years in dataset'
        },
        'gender': {
            'title': 'Distribution of gender in dataset'
        },
        'extensions': {
            'x': 'Images extensions',
            'y': '# of occurences in dataset',
            'title': 'Distribution of images extensions in dataset'
        },
        'usableImages': {
            'x': 'Detected values in images',
            'y': '# of occurences in dataset',
            'title': 'Distribution of detected values in images in dataset'
        },
        'resolution': {
            'x': 'Images resolution [px]',
            'y': '# of occurences in dataset',
            'title': 'Resolution of face images in dataset'
        },
    }
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

    uniqueValuesAll = {
        'nationality': {
            'male': {},
            'female': {},
            'all': {}
        },
        'occupation': {
            'male': {},
            'female': {},
            'all': {}
        },
        'gender': {}
    }

    totalProperties = {}
    totalPropertiesAllFalse = {}
    step = 1
    for year in tqdm(range(constants.START_YEAR, constants.END_YEAR, step), desc='getAllInfo'):
        data = readData(f'{constants.DATA_DIRECTORY}/{year}.json')
        if datasetOnly:
            data = toTrainingPeople(data)
        totalProperties = Counter(totalProperties) + Counter(countProperty(data, propertiesToCount))
        totalPropertiesAllFalse = Counter(totalPropertiesAllFalse) + Counter(
            countProperty(data, propertiesToCountAllFalse))

        for person in data.values():
            countAllForPerson(person, uniqueValuesAll)
            countGender(person, allStats['gender'])
            countBirthYear(person, allStats['birthYear'])

            for image in person['images'].values():
                countFaces(image, allStats['faces'])
                countAge(person, image, allStats['age'])
                countUsableImages(image, allStats['usableImages'])
                countExtensions(image, allStats['extensions'])
                if datasetOnly:
                    countResolution(image, allStats['resolution'])

    for key, graphData in list(allStats.items()):
        if key == 'faces':
            graphData = {k: v for (k, v) in graphData.items() if v > 1000}
            graphData = OrderedDict(sorted(graphData.items(), key=lambda x: int(x[0])))
            plotBarChart(graphData, f'{constants.STATS_DIRECTORY}/{key}.svg', graphsDescriptions[key])
        elif key == 'gender':
            plotPieChart(graphData, f'{constants.STATS_DIRECTORY}/{key}.svg', graphsDescriptions[key])
        elif key == 'age':
            # graphData['all'] = OrderedDict(sorted(graphData['all'].items(), key=lambda x: int(x[0])))
            plotLineChart(graphData, f'{constants.STATS_DIRECTORY}/{key}.svg', graphsDescriptions[key])
        elif key == 'resolution':
            if datasetOnly:
                plotBarChart({k: v for (k, v) in graphData.items() if v > 100},
                             f'{constants.STATS_DIRECTORY}/{key}_noBins.svg', graphsDescriptions[key])
                graphData = OrderedDict(sorted(graphData.items(), key=lambda x: int(x[1])))
                bins = {}
                step = 10
                start = 0
                for resolution in range(0, max(graphData.keys())):
                    if resolution % step == 0:
                        if start != 0:
                            bins[start + 5] = value
                        value = 0
                        start = resolution
                    if resolution in graphData:
                        value += graphData[resolution]
                bins = OrderedDict(sorted(bins.items(), key=lambda x: int(x[1]), reverse=True))
                allStats['resolutionBins'] = bins
                bins = {k: v for (k, v) in bins.items() if v > 100}
                plotBarChart(bins, f'{constants.STATS_DIRECTORY}/{key}_bins.svg', graphsDescriptions[key])
        else:
            plotBarChart(graphData, f'{constants.STATS_DIRECTORY}/{key}.svg', graphsDescriptions[key])

    saveData(allStats, f'{constants.STATS_DIRECTORY}/allStats.json')
    saveData(totalProperties, f'{constants.STATS_DIRECTORY}/countProperty.json')
    saveData(totalPropertiesAllFalse, f'{constants.STATS_DIRECTORY}/countPropertyAllFalse.json')

    for key in uniqueValuesAll.keys():
        if key == 'gender':
            uniqueValuesAll[key] = {k: v for k, v in
                                    sorted(uniqueValuesAll[key].items(), key=lambda x: x[1], reverse=True)}
        else:
            for gender in uniqueValuesAll[key]:
                uniqueValuesAll[key][gender] = {k: v for k, v in
                                                sorted(uniqueValuesAll[key][gender].items(), key=lambda x: x[1],
                                                       reverse=True)}
    # uniqueValuesShort = {prop: {gender: val for gender, val in } for prop in uniqueValuesAll.keys()}
    uniqueValuesShort = copy.deepcopy(uniqueValuesAll)
    for part in uniqueValuesShort.keys():
        if part == 'gender':
            uniqueValuesShort[part] = {key: value for key, value in
                                       list(uniqueValuesShort[part].items())[:10]}
        else:
            for gender in uniqueValuesShort[part]:
                uniqueValuesShort[part][gender] = {key: value for key, value in
                                                   list(uniqueValuesShort[part][gender].items())[:10]}
    uniqueValuesCount = {
        'nationality': 0,
        'occupation': 0,
        'gender': 0
    }

    uniqueValuesCount['nationality'] = len(uniqueValuesAll['nationality']['all'])
    uniqueValuesCount['occupation'] = len(uniqueValuesAll['occupation']['all'])
    uniqueValuesCount['gender'] = len(uniqueValuesAll['gender'])
    uniqueValues = {
        'uniqueValuesCount': uniqueValuesCount,
        'uniqueValuesShort': uniqueValuesShort,
        'uniqueValuesAll': uniqueValuesAll,
    }

    saveData(uniqueValues, f'{constants.STATS_DIRECTORY}/uniqueValues.json')


def countResolution(image, stats):
    x1, y1, x2, y2 = [int(value) for value in image['faces'][0]['box']]
    width = x2 - x1
    height = y2 - y1
    longerSide = max(width, height)
    if longerSide in stats:
        stats[longerSide] += 1
    else:
        stats[longerSide] = 1


def countAllForPerson(person, stats):
    for key in ['nationality', 'occupation']:
        if key in person:
            for item in person[key]:
                addToDictionary(item, stats[key]['all'])
                if 'gender' in person:
                    gender = person['gender']
                    if 'male' in gender and 'female' not in gender:
                        gender = 'male'
                    elif 'female' in gender and 'male' not in gender:
                        gender = 'female'
                    if gender in ['male', 'female']:
                        addToDictionary(item, stats[key][gender])

    if 'gender' in person:
        for item in person['gender']:
            addToDictionary(item, stats['gender'])


def countGender(person, stats):
    if 'gender' in person:
        for gender in person['gender']:
            if gender in ['male', 'female']:
                stats[gender] += 1
            else:
                stats['other'] += 1


def countBirthYear(person, stats):
    year = int(person['birthDate'][:constants.YEAR_OFFSET])
    if year in stats:
        stats[year] += 1
    else:
        stats[year] = 1


def countFaces(image, stats):
    # Images with bad extensions are skipped during the face detection phase
    if 'faces' in image:
        numberOfFaces = str(len(image['faces']))
        if numberOfFaces in stats:
            stats[numberOfFaces] += 1
        else:
            stats[numberOfFaces] = 1


def countAge(person, image, stats):
    if 'age' in image and image['age'] is not None:
        # stats[image['age']] += 1
        stats['all'][image['age']] += 1
        if 'gender' in person:
            for gender in person['gender']:
                if gender in ['male', 'female']:
                    stats[gender][image['age']] += 1


def countUsableImages(image, stats):
    age = 'age' in image and image['age'] is not None
    faces = 'faces' in image and len(image['faces']) == 1
    if age and not faces:
        stats['only age'] += 1
    if faces and not age:
        stats['only faces'] += 1
    if age and faces:
        stats['faces and age'] += 1


def countExtensions(image, stats):
    # extension = os.path.splitext(image['fileNameLocal'])[1].lower()
    extension = image['extension']
    if extension in stats:
        stats[extension] += 1
    else:
        stats[extension] = 1


if __name__ == '__main__':
    getAllInfo()
    # data = toEvaluationSample()