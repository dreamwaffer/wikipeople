import os, random
import shutil

from tqdm import tqdm

from constants import TRAIN, TEST, VAL, ONE_TEST_CONSTANT, DATASET_DIRECTORY


def moveRandomImagesToDirs(number, valPercentage):
    fileSet = set()
    maleInDir = '/datagrid/personal/kotrblu2/1/usableImages256/male'
    femaleInDir = '/datagrid/personal/kotrblu2/1/usableImages256/female'
    trainMaleDir = '/datagrid/personal/kotrblu2/1/dataset/train/male'
    trainFemaleDir = '/datagrid/personal/kotrblu2/1/dataset/train/female'
    valMaleDir = '/datagrid/personal/kotrblu2/1/dataset/val/male'
    valFemaleDir = '/datagrid/personal/kotrblu2/1/dataset/val/female'

    maleDirs = [trainMaleDir, valMaleDir]
    femaleDirs = [trainFemaleDir, valFemaleDir]

    maleFiles = os.listdir(maleInDir)
    femaleFiles = os.listdir(femaleInDir)
    for dir in maleDirs + femaleDirs:
        if not os.path.exists(dir):
            os.makedirs(dir)

    for index in tqdm(range(number), desc='moveImagesToDirs', miniters=int(number / 100)):
        # for index in range(number):
        image = None
        for dir in maleDirs:
            if dir == trainMaleDir or dir == valMaleDir and index % (1 / valPercentage) == 0:
                while image in fileSet or image is None:
                    image = random.choice(maleFiles)
                fileSet.add(image)
                os.rename(f'{maleInDir}/{image}', f'{dir}/{image}')

        image = None
        for dir in femaleDirs:
            if dir == trainFemaleDir or dir == valFemaleDir and index % (1 / valPercentage) == 0:
                while image in fileSet or image is None:
                    image = random.choice(femaleFiles)
                fileSet.add(image)
                os.rename(f'{femaleInDir}/{image}', f'{dir}/{image}')


def moveAllImagesToDirs(number, valPercentage):
    maleInDir = '/datagrid/personal/kotrblu2/1/usableImages128/male'
    femaleInDir = '/datagrid/personal/kotrblu2/1/usableImages128/female'
    trainMaleDir = '/datagrid/personal/kotrblu2/1/dataset/train/male'
    trainFemaleDir = '/datagrid/personal/kotrblu2/1/dataset/train/female'
    valMaleDir = '/datagrid/personal/kotrblu2/1/dataset/val/male'
    valFemaleDir = '/datagrid/personal/kotrblu2/1/dataset/val/female'

    allDirs = [trainMaleDir, trainFemaleDir, valMaleDir, valFemaleDir]

    maleFiles = os.listdir(maleInDir)  # shuffle?
    femaleFiles = os.listdir(femaleInDir)
    random.shuffle(maleFiles)
    random.shuffle(femaleFiles)
    for dir in allDirs:
        if not os.path.exists(dir):
            os.makedirs(dir)

    train = int(number * (1 - valPercentage))
    val = int(number * valPercentage)

    for index in range(train):
        maleImage = maleFiles[index]
        femaleImage = femaleFiles[index]
        shutil.copyfile(f'{maleInDir}/{maleImage}', f'{trainMaleDir}/{maleImage}')
        shutil.copyfile(f'{femaleInDir}/{femaleImage}', f'{trainFemaleDir}/{femaleImage}')

    for index in range(val):
        maleImage = maleFiles[train + index - 1]
        femaleImage = femaleFiles[train + index - 1]
        shutil.copyfile(f'{maleInDir}/{maleImage}', f'{valMaleDir}/{maleImage}')
        shutil.copyfile(f'{femaleInDir}/{femaleImage}', f'{valFemaleDir}/{femaleImage}')


def trainValTestSplitMin(number):
    inDataset = '../dataset2'
    outDataset = '../dataset2Split'

    # inDataset = '/datagrid/personal/kotrblu2/1/genderAge'
    # outDataset = '/datagrid/personal/kotrblu2/1/genderAgeSplit'
    classes = os.listdir(inDataset)
    directories = []
    directories.extend([f'{outDataset}/train/{item}' for item in classes])
    directories.extend([f'{outDataset}/val/{item}' for item in classes])
    directories.extend([f'{outDataset}/test/{item}' for item in classes])
    files = []
    split = {
        'train': 0,
        'val': 0,
        'test': 0
    }

    # create fileLists and shuffle them
    for item in classes:
        itemFiles = os.listdir(f'{inDataset}/{item}')
        random.shuffle(itemFiles)
        files.append(itemFiles)

    # check if all directories exists or create them
    for dir in directories:
        if not os.path.exists(dir):
            os.makedirs(dir)

    split['train'] = int(number * TRAIN)
    split['val'] = int(number * VAL)
    split['test'] = int(number * TEST)

    startIndex = 0

    for part, numFiles in split.items():
        for i in tqdm(range(numFiles), desc=f'trainValTestSplit-{part}', miniters=int(numFiles / 100)):
            # for i in range(train):
            for j, itemFiles in enumerate(files):
                image = itemFiles[startIndex + i]
                shutil.copyfile(f'{inDataset}/{classes[j]}/{image}', f'{outDataset}/{part}/{classes[j]}/{image}')
        startIndex += numFiles


def trainValTestSplitAll():
    inDataset = DATASET_DIRECTORY
    outDataset = '../controlDatasetSplit'

    # inDataset = '/datagrid/personal/kotrblu2/1/genderAge'
    # outDataset = '/datagrid/personal/kotrblu2/1/genderAgeSplit'
    classes = os.listdir(inDataset)
    directories = []
    directories.extend([f'{outDataset}/train/{item}' for item in classes])
    directories.extend([f'{outDataset}/val/{item}' for item in classes])
    directories.extend([f'{outDataset}/test/{item}' for item in classes])
    files = []
    split = {
        'train': 0,
        'val': 0,
        'test': 0
    }
    result = {
        'train': {k: 0 for k in classes},
        'val': {k: 0 for k in classes},
        'test': {k: 0 for k in classes}
    }

    # create fileLists and shuffle them
    for item in classes:
        itemFiles = os.listdir(f'{inDataset}/{item}')
        print(f'{inDataset}/{item}: {str(len(itemFiles))}')
        random.shuffle(itemFiles)
        files.append(itemFiles)

    # check if all directories exists or create them
    for dir in directories:
        if not os.path.exists(dir):
            os.makedirs(dir)

    split['train'] = TRAIN
    split['val'] = VAL
    split['test'] = TEST

    startIndices = [0] * len(classes)

    for part, multiplier in tqdm(split.items(), desc=f'controlDatasetSplitAll'):
        for i, item in enumerate(classes):
            number = int(len(files[i]) * multiplier)
            for j in range(number):
                image = files[i][startIndices[i] + j]
                shutil.copyfile(f'{inDataset}/{classes[i]}/{image}', f'{outDataset}/{part}/{classes[i]}/{image}')
                result[part][item] += 1
            startIndices[i] += number

    return result


def createDataToAdd():
    # inDataset = DATASET_DIRECTORY
    # outDataset = '../controlDatasetSplit'

    inDataset = '/datagrid/personal/kotrblu2/1/genderAge'
    outDataset = '/datagrid/personal/kotrblu2/1/finalTestDataBig'
    controlDataset = '/datagrid/personal/kotrblu2/1/controlDataset/splitAllCorrect/train'

    numTests = 10
    classes = os.listdir(inDataset)
    controlDatasetFiles = {}
    files = {}
    # create fileLists and shuffle them
    for group in classes:
        itemFiles = os.listdir(f'{inDataset}/{group}')
        random.shuffle(itemFiles)
        files[group] = itemFiles
        print(f'Files: {len(itemFiles)}')
        itemFiles = os.listdir(f'{controlDataset}/{group}')
        controlDatasetFiles[group] = itemFiles
        print(f'Control files: {len(itemFiles)}')

    ratio = {'female,adult': 2100,
             'female,old': 583,
             'female,young': 1336,
             'male,adult': 3703,
             'male,old': 1029,
             'male,young': 1140}

    total = sum(ratio.values())

    rangesInTest = {k: int(v / total * ONE_TEST_CONSTANT) for (k, v) in ratio.items()}

    for group in ratio.keys():
        os.makedirs(f'{outDataset}/0/train/{group}')
        for image in controlDatasetFiles[group]:
            shutil.copy(f'{controlDataset}/{group}/{image}', f'{outDataset}/0/train/{group}/{image}')

    for i in range(1, numTests + 1):
        for group in ratio.keys():
            # Create group
            os.makedirs(f'{outDataset}/{i}/train/{group}')
            # copy control dataset files
            for image in controlDatasetFiles[group]:
                shutil.copy(f'{controlDataset}/{group}/{image}', f'{outDataset}/{i}/train/{group}/{image}')
            # copy my files
            for j in range(i * rangesInTest[group]):
                image = files[group][j]
                shutil.copyfile(f'{inDataset}/{group}/{image}', f'{outDataset}/{i}/train/{group}/{image}')


if __name__ == '__main__':
    # directoriesConfig()
    createDataToAdd()
