from collections import Counter, OrderedDict
import os

import matplotlib.pyplot as plt
from tqdm import tqdm

import constants
from create import utils, transformer


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
            'faces': 0,
            'age': 0,
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
            'x': 'Images quality options',
            'y': '# of occurences in dataset',
            'title': 'Distribution of quality in images in dataset'
        },
        'resolution': {
            'x': 'Images resolution',
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

    uniqueValues = {
        'nationality': {},
        'occupation': {},
        'gender': {}
    }

    totalProperties = {}
    totalPropertiesAllFalse = {}
    step = 1
    for year in tqdm(range(constants.START_YEAR, constants.END_YEAR, step), desc='getAllInfo'):
        # data = utils.readData(f'{constants.DATA_DIRECTORY}/{year}_{year + step}.json')
        data = utils.readData(f'{constants.DATA_DIRECTORY}/{year}.json')
        if datasetOnly:
            data = transformer.toTrainingPeople(data)
        totalProperties = Counter(totalProperties) + Counter(utils.countProperty(data, propertiesToCount))
        totalPropertiesAllFalse = Counter(totalPropertiesAllFalse) + Counter(
            utils.countProperty(data, propertiesToCountAllFalse))

        for person in data.values():
            countAllForPerson(person, uniqueValues)
            countGender(person, allStats['gender'])
            countBirthYear(person, allStats['birthYear'])

            for image in person['images'].values():
                countFaces(image, allStats['faces'])
                countAge(person, image, allStats['age'])
                countUsableImages(image, allStats['usableImages'])
                countExtensions(image, allStats['extensions'])
                countResolution(image, allStats['resolution'])

    for key, graphData in allStats.items():
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
            graphData = {k: v for (k, v) in graphData.items() if v > 10}
            graphData = OrderedDict(sorted(graphData.items(), key=lambda x: int(x[0])))
            plotBarChart(graphData, f'{constants.STATS_DIRECTORY}/{key}.svg', graphsDescriptions[key])
        else:
            plotBarChart(graphData, f'{constants.STATS_DIRECTORY}/{key}.svg', graphsDescriptions[key])

    utils.saveData(allStats, f'{constants.STATS_DIRECTORY}/allStats.json')
    utils.saveData(totalProperties, f'{constants.STATS_DIRECTORY}/countProperty.json')
    utils.saveData(totalPropertiesAllFalse, f'{constants.STATS_DIRECTORY}/countPropertyAllFalse.json')
    uniqueValues = {key: {k: v for k, v in sorted(value.items(), key=lambda item: item[1], reverse=True)} for key, value
                    in uniqueValues.items()}
    utils.saveData(uniqueValues, f'{constants.STATS_DIRECTORY}/uniqueValues.json')


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
    for key in stats.keys():
        if key in person:
            for item in person[key]:
                if item in stats[key]:
                    stats[key][item] += 1
                else:
                    stats[key][item] = 1


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
    # We are only interested in those images, that were through successful face detection and got an age assigned to them
    if 'faces' in image and 'age' in image and image['age'] is not None:
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

        # if image['age'] in stats:
        #     stats[image['age']] += 1
        # else:
        #     stats[image['age']] = 1


def countUsableImages(image, stats):
    age = 'age' in image and image['age'] is not None
    faces = 'faces' in image and len(image['faces']) == 1
    if age and not faces:
        stats['age'] += 1
    if faces and not age:
        stats['faces'] += 1
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
    # getAllInfo(True)
    # step = 5
    # for year in tqdm(range(constants.START_YEAR, constants.END_YEAR, step), desc='getAllInfo'):
    #     data = utils.readData(f'{constants.DATA_DIRECTORY}/{year}_{year + step}.json')
    #     data = transformer.toTrainingPeople(data)
    #     data = transformer.toPeopleWithAllProps(data)
    #     data = transformer.toEvaluationSample(data)
    #     utils.saveData(data, f'{constants.DATA_DIRECTORY}/{year}_{year + step}_eval.json')

    step = 1
    allStats = {year: {} for year in range(constants.START_YEAR, constants.END_YEAR, step)}
    total = {year: 0 for year in range(constants.START_YEAR, constants.END_YEAR, step)}
    result = {}
    for year in tqdm(range(constants.START_YEAR, constants.END_YEAR, step), desc='getAllInfo'):
        # data = utils.readData(f'{constants.DATA_DIRECTORY}/{year}_{year + step}.json')
        data = utils.readData(f'{constants.DATA_DIRECTORY}/{year}.json')
        for person in data.values():
            for image in person['images'].values():
                countFaces(image, allStats[year])
        total[year] = utils.countProperty(data, {'images': True})['images']
        result[year] = (sum(allStats[year].values()), total[year])

    utils.saveData(result, f'{constants.STATS_DIRECTORY}/result.json')
