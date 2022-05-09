import collections

import matplotlib.pyplot as plt
from modules.process import *


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


def plotPieChart(stats, file, graphDescription):
    plt.clf()
    plt.close()
    plt.pie(list(stats.values()), startangle=90, radius=1.2, autopct='%.2f%%')
    plt.legend(labels=list(stats.keys()), bbox_to_anchor=(1, 0), loc="lower right",
               bbox_transform=plt.gcf().transFigure)
    plt.title(graphDescription['title'])
    plt.savefig(file, dpi=300)


def createStatsFaces(data, file):
    """This method creates histogram for detected faces

        Keyword arguments:
        data -- processed data from sparql endpoint
        file -- location where to save the histogram
    """
    stats = {}
    for person in tqdm(data.values(), desc='createStatsFaces', miniters=int(len(data) / 100)):
        for image in person['images'].values():
            # print(image['fileNameLocal'])
            # Images with bad extensions are skipped during the face detection phase
            # We are only interested in those images, that were through successful face detection and got an age assigned to them
            if 'faces' in image and 'age' in image and image['age'] is not None:
                numberOfFaces = str(len(image['faces']))
                if numberOfFaces in stats:
                    stats[numberOfFaces] += 1
                else:
                    stats[numberOfFaces] = 1

    stats = {k: v for (k, v) in stats.items() if v > 100}
    sortedStats = collections.OrderedDict(sorted(stats.items(), key=lambda x: int(x[0])))

    graphDescription = {
        'x': '# of faces detected',
        'y': '# of occurences in dataset',
        'title': 'Distribution of detected faces'
    }
    plotBarChart(sortedStats, file, graphDescription)

    return graphDescription, stats


def createStatsAge(data, file):
    """This method creates histogram for detected faces

        Keyword arguments:
        data -- processed data from sparql endpoint
        file -- location where to save the histogram
    """
    stats = {}
    for person in tqdm(data.values(), desc='createStatsAge', miniters=int(len(data) / 100)):
        for image in person['images'].values():
            # print(image['fileNameLocal'])
            # Images with bad extensions are skipped during the face detection phase
            # We are only interested in those images, that were through successful face detection and got an age assigned to them
            if 'age' in image and image['age'] is not None:
                if image['age'] in stats:
                    stats[image['age']] += 1
                else:
                    stats[image['age']] = 1

    graphDescription = {
        'x': 'age',
        'y': '# of occurences in dataset',
        'title': 'Distribution of age in dataset'
    }
    plotBarChart(stats, file, graphDescription)

    return graphDescription, stats


def createStatsGender(data, file):
    """This method creates histogram for detected faces

        Keyword arguments:
        data -- processed data from sparql endpoint
        file -- location where to save the histogram
    """
    stats = {
        'male': 0,
        'female': 0,
        'other': 0
    }
    key = 'gender'
    for person in tqdm(data.values(), desc='createStatsGender', miniters=int(len(data) / 100)):
        if key in person:
            for gender in person[key]:
                if gender in ['male', 'female']:
                    stats[gender] += 1
                else:
                    stats['other'] += 1

    graphDescription = {
        'title': 'Distribution of gender in dataset'
    }
    plotPieChart(stats, file, graphDescription)

    return graphDescription, stats


def createStatsUsableImages(data, file):
    """This method creates histogram for detected faces

        Keyword arguments:
        data -- processed data from sparql endpoint
        file -- location where to save the histogram
    """
    stats = {
        'faces': 0,
        'age': 0,
        'faces and age': 0
    }

    for person in tqdm(data.values(), desc='createStatsUsableImages', miniters=int(len(data) / 100)):
        for image in person['images'].values():
            age = 'age' in image and image['age'] is not None
            faces = 'faces' in image and len(image['faces']) == 1
            if age and not faces:
                stats['age'] += 1
            if faces and not age:
                stats['faces'] += 1
            if age and faces:
                stats['faces and age'] += 1

    graphDescription = {
        'x': 'Images quality options',
        'y': '# of occurences in dataset',
        'title': 'Distribution of quality in images in dataset'
    }
    plotBarChart(stats, file, graphDescription)

    return graphDescription, stats


def createStatsImagesExtensions(data, file):
    """This method creates histogram for detected faces

        Keyword arguments:
        data -- processed data from sparql endpoint
        file -- location where to save the histogram
    """
    stats = {}

    for person in tqdm(data.values(), desc='createStatsImagesExtensions', miniters=int(len(data) / 100)):
        for image in person['images'].keys():
            extension = os.path.splitext(image)[1].lower()
            if extension in stats:
                stats[extension] += 1
            else:
                stats[extension] = 1

    graphDescription = {
        'x': 'Images extensions',
        'y': '# of occurences in dataset',
        'title': 'Distribution of images extensions in dataset'
    }
    plotBarChart(stats, file, graphDescription)

    return graphDescription, stats


def createStatsBirthYear(data, file):
    """This method creates histogram for detected faces

        Keyword arguments:
        data -- processed data from sparql endpoint
        file -- location where to save the histogram
    """
    stats = {}

    for person in tqdm(data.values(), desc='createStatsBirthYear', miniters=int(len(data) / 100)):
        year = int(person['birthDate'][:constants.YEAR_OFFSET])
        if year == '1':
            print(person['wikidataID'])
        if year in stats:
            stats[year] += 1
        else:
            stats[year] = 1

    graphDescription = {
        'x': 'Birth years',
        'y': '# of occurences in dataset',
        'title': 'Distribution of birth years in dataset'
    }
    plt.clf()
    plt.close()
    plt.figure(figsize=(10, 7))
    plt.bar(list(stats.keys()), stats.values(), color='green')
    plt.ylabel(graphDescription['y'])
    plt.xlabel(graphDescription['x'])
    plt.title(graphDescription['title'])
    # plt.xticks(rotation=90)
    plt.savefig(file, dpi=300)

    return graphDescription, stats


def plotAll():
    config()
    step = 5
    allStats = {
        'age': {},
        'faces': {},
        'birthYear': {},
        'gender': {},
        'extensions': {},
        'usableImages': {},
    }
    graphsDescriptions = {
        'age': {},
        'faces': {},
        'birthYear': {},
        'gender': {},
        'extensions': {},
        'usableImages': {},
    }

    allDir = 'all'
    if not os.path.exists(f'{constants.STATS_DIRECTORY}/{allDir}'):
        os.makedirs(f'{constants.STATS_DIRECTORY}/{allDir}')
    for year in range(constants.START_YEAR, constants.END_YEAR, step):
        print(f'Starting years: {year}, {year + step}!')
        data = readData(f'{constants.DATA_DIRECTORY}/{year}_{year + step}.json')
        if not os.path.exists(f'{constants.STATS_DIRECTORY}/{year}_{year + step}'):
            os.makedirs(f'{constants.STATS_DIRECTORY}/{year}_{year + step}')
        for key in allStats.keys():
            if key == 'age':
                graphsDescriptions[key], stats = createStatsAge(data,
                                                                f'{constants.STATS_DIRECTORY}/{year}_{year + step}/{key}.svg')
                allStats[key] = allStats[key] | stats
            elif key == 'faces':
                graphsDescriptions[key], stats = createStatsFaces(data,
                                                                  f'{constants.STATS_DIRECTORY}/{year}_{year + step}/{key}.svg')
                allStats[key] = allStats[key] | stats
            elif key == 'birthYear':
                graphsDescriptions[key], stats = createStatsBirthYear(data,
                                                                      f'{constants.STATS_DIRECTORY}/{year}_{year + step}/{key}.svg')
                allStats[key] = allStats[key] | stats
            elif key == 'gender':
                graphsDescriptions[key], stats = createStatsGender(data,
                                                                   f'{constants.STATS_DIRECTORY}/{year}_{year + step}/{key}.svg')
                allStats[key] = allStats[key] | stats
            elif key == 'extensions':
                graphsDescriptions[key], stats = createStatsImagesExtensions(data,
                                                                             f'{constants.STATS_DIRECTORY}/{year}_{year + step}/{key}.svg')
                allStats[key] = allStats[key] | stats
            elif key == 'usableImages':
                graphsDescriptions[key], stats = createStatsUsableImages(data,
                                                                         f'{constants.STATS_DIRECTORY}/{year}_{year + step}/{key}.svg')
                allStats[key] = allStats[key] | stats

    for key, graphData in allStats.items():
        if key == 'faces':
            graphData = collections.OrderedDict(sorted(graphData.items(), key=lambda x: int(x[0])))
            plotBarChart(graphData, f'{constants.STATS_DIRECTORY}/{allDir}/{key}.svg', graphsDescriptions[key])
        elif key == 'gender':
            plotPieChart(graphData, f'{constants.STATS_DIRECTORY}/{allDir}/{key}.svg', graphsDescriptions[key])
        else:
            plotBarChart(graphData, f'{constants.STATS_DIRECTORY}/{allDir}/{key}.svg', graphsDescriptions[key])


def test():
    # creating data on which bar chart will be plot
    x = ["Engineering", "Hotel Managment",
         "MBA", "Mass Communication", "BBA",
         "BSc", "MSc"]
    y = [9330, 4050, 3030, 5500,
         8040, 4560, 6650]

    # setting figure size by using figure() function
    plt.figure(figsize=(10, 5))

    # making the bar chart on the data
    plt.bar(x, y)

    # calling the function to add value labels
    addlabels(x, y)

    # giving title to the plot
    plt.title("College Admission")

    # giving X and Y labels
    plt.xlabel("Courses")
    plt.ylabel("Number of Admissions")

    # visualizing the plot
    plt.show()


if __name__ == '__main__':
    # test()
    plotAll()
