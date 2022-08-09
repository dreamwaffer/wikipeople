import webbrowser

from tqdm import tqdm

from create.utils import readData, saveData
import constants


def evalAges(data):
    for image in tqdm(data, desc='evaluation progress'):
        if image['imageYear'] == 0:
            webbrowser.open(image['wikipediaLink'])
            webbrowser.open(image['wikidataLink'])
            webbrowser.open(image['imageLink'])
            print()
            inputText = input('Enter image year found or "end" for saving current progress: ')
            if inputText == 'end':
                break
            image['imageYear'] = int(inputText)
            image['foundAge'] = image['imageYear'] - int(image['birthDate'][:constants.YEAR_OFFSET])

    return data


def evaluateData(data):
    totalDiff = 0
    totalNumber = 0
    error = {}
    for image in data:
        if 'foundAge' in image:
            diff = abs(image['age'] - image['foundAge'])
            if diff not in error:
                error[diff] = 1
            else:
                error[diff] += 1
            totalDiff += diff
            totalNumber += 1

    result = totalDiff / totalNumber
    correctAge = error[0] / totalNumber
    print(f'Mean Absolute Error: {result:.6f} years')
    print(f'Correct estimations: {correctAge}')
    print(f'Data length: {totalNumber}')


if __name__ == '__main__':
    # data = transformer.toEvaluationSample()
    # data = readData(f'{constants.DATA_DIRECTORY}/eval.json')
    # data = evalAges(data)
    # saveData(data, f'{constants.DATA_DIRECTORY}/eval.json')

    data = readData(f'{constants.DATA_DIRECTORY}/eval.json')
    evaluateData(data)