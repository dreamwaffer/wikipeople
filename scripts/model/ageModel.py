from __future__ import print_function, division

import json
import time
import os
import copy

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
from torch import Tensor
from torch.optim import lr_scheduler
import torch.backends.cudnn as cudnn
import numpy as np
from torchvision import datasets, models, transforms
import matplotlib.pyplot as plt

import constants
from create.utils import saveData


def run(data_dir, eval_dir, resultDirectory, runIndex):
    def train_model(model, criterion, optimizer, scheduler, num_epochs=25):
        since = time.time()

        best_model_wts = copy.deepcopy(model.state_dict())
        best_mean = 10000
        progress = {
            'train': [],
            'val': []
        }

        for epoch in range(num_epochs):
            print(f'Epoch {epoch}/{num_epochs - 1}')
            print('-' * 10)

            # Each epoch has a training and validation phase
            for phase in ['train', 'val']:
                if phase == 'train':
                    model.train()  # Set model to training mode
                else:
                    model.eval()  # Set model to evaluate mode

                running_loss = 0.0
                running_corrects = 0
                std_deviation, std_mean = 0.0, 0.0

                # Iterate over data.
                for inputs, labels in dataloaders[phase]:
                    inputs = inputs.to(device)
                    labels = labels.to(device)

                    # zero the parameter gradients
                    optimizer.zero_grad()

                    # forward
                    # track history if only in train
                    with torch.set_grad_enabled(phase == 'train'):
                        outputs = model(inputs)

                        # create loss matrix
                        loss_matrix = torch.zeros(len(class_names), len(class_names), dtype=torch.float64).cuda()
                        # loss_matrix = torch.zeros(len(class_names), len(class_names), dtype=torch.float64).cpu()
                        for y in range(len(class_names)):
                            for yy in range(len(class_names)):
                                loss_matrix[y, yy] = torch.abs(torch.tensor(y - yy))

                        # Prediction optimal for given loss_matrix
                        posterior = torch.softmax(outputs.detach().clone(), 1).cuda()
                        # posterior = torch.softmax(outputs.detach().clone(), 1).cpu()
                        _, preds = torch.min(torch.matmul(posterior.to(torch.float), loss_matrix.to(torch.float)), 1)

                        # _, preds = torch.max(outputs, 1)
                        loss = criterion(outputs, labels)

                        # backward + optimize only if in training phase
                        if phase == 'train':
                            loss.backward()
                            optimizer.step()

                    # statistics
                    running_loss += loss.item() * inputs.size(0)
                    running_corrects += torch.sum(preds == labels.data)
                    absTensor = torch.abs(torch.sub(preds, labels.data))
                    aux = torch.std_mean(absTensor.to(torch.float))
                    std_deviation += aux[0]
                    std_mean += aux[1]

                if phase == 'train':
                    scheduler.step()

                epoch_loss = running_loss / dataset_sizes[phase]
                epoch_acc = running_corrects.double() / dataset_sizes[phase]
                std_deviation = std_deviation / len(dataloaders[phase])
                std_mean = std_mean / len(dataloaders[phase])

                progress[phase].append(Tensor.cpu(std_mean))

                print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')
                print(f'{phase} Standart Deviation: {std_deviation:.4f}')
                print(f'{phase} Standart Mean: {std_mean:.4f}')

                # deep copy the model
                if phase == 'val' and std_mean < best_mean:
                    best_mean = std_mean
                    best_model_wts = copy.deepcopy(model.state_dict())

            print()

        time_elapsed = time.time() - since
        print(f'Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s')
        print(f'Best val Mean: {best_mean:.10f}')

        # create graphs with progress
        plt.clf()
        plt.close()
        x = [item for item in range(1, num_epochs + 1)]
        plt.figure(figsize=(10, 7))
        plt.ylabel('Error of model [years]')
        plt.xlabel('Phase of training')
        plt.title(
            f'Mean Absolute Error of model throughout the training')
        for index, (phase, values) in enumerate(progress.items()):
            label = 'training phase' if phase == 'train' else 'validation phase'
            plt.plot(x, values, label=label)
        plt.legend()
        plt.savefig(f'{resultDirectory}/{runIndex}/error', dpi=300)

        # load best model weights
        model.load_state_dict(best_model_wts)
        return model

    def test_model(model, criterion):
        was_training = model.training
        model.eval()
        running_loss = 0.0
        running_corrects = 0
        std_deviation, std_mean = 0.0, 0.0
        errorByYears = {f'{number}': 0 for number in range(17, 81)}
        totalByYears = {f'{number}': 0 for number in range(17, 81)}

        with torch.no_grad():
            for i, (inputs, labels) in enumerate(dataloaders['test']):
                inputs = inputs.to(device)
                labels = labels.to(device)

                outputs = model(inputs)
                # create loss matrix
                loss_matrix = torch.zeros(len(class_names), len(class_names), dtype=torch.float64).cuda()
                # loss_matrix = torch.zeros(len(class_names), len(class_names), dtype=torch.float64).cpu()
                for y in range(len(class_names)):
                    for yy in range(len(class_names)):
                        loss_matrix[y, yy] = torch.abs(torch.tensor(y - yy))

                # Prediction optimal for given loss_matrix
                posterior = torch.softmax(outputs.detach().clone(), 1).cuda()
                # posterior = torch.softmax(outputs.detach().clone(), 1).cpu()
                _, preds = torch.min(torch.matmul(posterior.to(torch.float), loss_matrix.to(torch.float)), 1)

                # _, preds = torch.max(outputs, 1)
                loss = criterion(outputs, labels)

                if i < 10:
                    plt.clf()
                    plt.close()
                    plt.figure(figsize=(8, 3))
                    out = torchvision.utils.make_grid(inputs.cpu().data,
                                                      out=torchvision.utils.make_grid(inputs.cpu().data))
                    imsave(out, f'{resultDirectory}/{runIndex}/test{i}.png',
                           real=[class_names[x] for x in labels],
                           predicted=[class_names[x] for x in preds])

                # statistics
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
                absTensor = torch.abs(torch.sub(preds, labels.data))
                aux = torch.std_mean(absTensor.to(torch.float))
                std_deviation += aux[0]
                std_mean += aux[1]

                real = [class_names[x] for x in labels]
                for index, item in enumerate(real):
                    errorByYears[item] += absTensor[index]
                    totalByYears[item] += 1

            test_loss = running_loss / dataset_sizes['test']
            test_acc = running_corrects.double() / dataset_sizes['test']
            std_deviation = std_deviation / len(dataloaders['test'])
            std_mean = std_mean / len(dataloaders['test'])

            meanByYears = {}
            totalByYearsVals = list(totalByYears.values())
            for index, (year, error) in enumerate(errorByYears.items()):
                meanByYears[year] = error / totalByYearsVals[index]
            meanByYears = {int(k): v.item() for k, v in meanByYears.items()}
            stdMeanAll = sum(meanByYears.values()) / len(meanByYears)

            print(f'Test Loss: {test_loss:.4f} Acc: {test_acc:.10f}')
            print(f'Test Standart Deviation: {std_deviation:.4f}')
            print(f'Test Standart Mean: {std_mean:.4f}')
            print(f'Test Standart Mean Through all years: {stdMeanAll:.4f}')

            print(json.dumps(meanByYears, indent=2))
            model.train(mode=was_training)

        return Tensor.cpu(std_mean).item(), meanByYears

    def imsave(inp, location, real, predicted):
        """Imshow for Tensor."""
        inp = inp.numpy().transpose((1, 2, 0))
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        inp = std * inp + mean
        inp = np.clip(inp, 0, 1)
        plt.imshow(inp)
        plt.figtext(0.5, 0.2, f'Real: {real}', wrap=True, horizontalalignment='center', fontsize=8)
        plt.figtext(0.5, 0.1, f'Pred: {predicted}', wrap=True, horizontalalignment='center', fontsize=8)
        plt.xticks([])
        plt.yticks([])
        plt.pause(0.001)  # pause a bit so that plots are updated
        plt.savefig(location)

    cudnn.benchmark = True
    BATCH_SIZE = 100
    NUM_EPOCHS = 100
    LR = 0.001

    # Data augmentation and normalization for training
    # Just normalization for validation
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'val': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'test': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir, x),
                                              data_transforms[x])
                      for x in ['train']}
    image_datasets = image_datasets | {x: datasets.ImageFolder(os.path.join(eval_dir, x),
                                                               data_transforms[x])
                                       for x in ['val', 'test']}

    torchDataloader = torch.utils.data.DataLoader
    dataloaders = {x: torchDataloader(image_datasets[x],
                                      batch_size=BATCH_SIZE,
                                      shuffle=True,
                                      num_workers=4)
                   for x in ['train', 'val']}
    dataloaders['test'] = torchDataloader(image_datasets['test'],
                                          batch_size=8,
                                          shuffle=True,
                                          num_workers=4)
    dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val', 'test']}
    class_names = image_datasets['train'].classes
    device = torch.device(f"cuda:0" if torch.cuda.is_available() else "cpu")
    model_ft = models.resnet50(pretrained=True)
    # model_ft = models.resnet50(weights=ResNet50_Weights.DEFAULT)
    num_ftrs = model_ft.fc.in_features
    # Setting the number of classification classes
    model_ft.fc = nn.Linear(num_ftrs, len(class_names))
    model_ft = model_ft.to(device)
    criterion = nn.CrossEntropyLoss()
    # Observe that all parameters are being optimized
    optimizer_ft = optim.SGD(model_ft.parameters(), lr=LR, momentum=0.9)
    # Decay LR by a factor of 0.1 every 7 epochs
    exp_lr_scheduler = lr_scheduler.StepLR(optimizer_ft, step_size=7, gamma=0.1)
    model_ft = train_model(model_ft, criterion, optimizer_ft, exp_lr_scheduler,
                           num_epochs=NUM_EPOCHS)
    if runIndex == 4:
        torch.save(model_ft.state_dict(), f'{resultDirectory}/{runIndex}/model.pt')
    acc, accByYears = test_model(model_ft, criterion)
    return dataset_sizes['train'], acc, accByYears


if __name__ == '__main__':
    if not os.path.exists(constants.RESULTS_DIRECTORY):
        os.makedirs(constants.RESULTS_DIRECTORY)

    if not os.path.exists(f"{constants.RESULTS_DIRECTORY}/age"):
        os.makedirs(f"{constants.RESULTS_DIRECTORY}/age")

    results = []
    accByYearAll = {
        0: {'name': 'Pure AgeDB - 9455 images'},
        1: {'name': 'AgeDB + approx. 1k images - 10455 images'},
        2: {'name': 'AgeDB + approx. 10k images - 19455 images'},
        3: {'name': 'AgeDB + approx. 100k images - 109449 images'},
        4: {'name': 'AgeDB + approx. 600k images - 598901 images'}
    }
    iterationsNum = 5

    for i in range(iterationsNum):
        print(f'Starting model {i}')
        if not os.path.exists(f'{constants.RESULTS_DIRECTORY}/age/{i}'):
            os.makedirs(f'{constants.RESULTS_DIRECTORY}/age/{i}')
        length, acc, accByYear = run(f'{constants.DATASET_DIRECTORY}/age/{i}',
                                     f'{constants.DATASET_DIRECTORY}/age/eval',
                                     f'{constants.RESULTS_DIRECTORY}/age', i)
        results.append((length, acc))
        accByYearAll[i]['data'] = accByYear

        # results.append(run(f'/datagrid/personal/kotrblu2/final/dataset/{i}',
        #                    f'/datagrid/personal/kotrblu2/final/dataset/eval',
        #                    resultDirectory, i))

    saveData(accByYearAll, f'{constants.RESULTS_DIRECTORY}/age/accByYearAll.json')

    # MAE of all models in relation to specific ages
    plt.clf()
    plt.close()
    plt.ylabel('Error of model [years]')
    plt.xlabel('Real age [years]')
    plt.title('Mean absolute error of models in relation to specific ages')
    for item in accByYearAll.values():
        if 'data' in item:
            plt.plot(list(item['data'].keys()), list(item['data'].values()), label=item['name'])
    plt.legend()
    plt.savefig(f'{constants.RESULTS_DIRECTORY}/age/accByYear.png', dpi=300)

    # MAE of first and last model in relation to specific ages
    plt.clf()
    plt.close()
    plt.ylabel('Error of model [years]')
    plt.xlabel('Real age [years]')
    plt.title('Mean absolute error of models in relation to specific ages')
    item = list(accByYearAll.values())[0]
    if 'data' in item:
        plt.plot(list(item['data'].keys()), list(item['data'].values()), label=item['name'])
    item = list(accByYearAll.values())[4]
    if 'data' in item:
        plt.plot(list(item['data'].keys()), list(item['data'].values()), label=item['name'])
    plt.legend()
    plt.savefig(f'{constants.RESULTS_DIRECTORY}/age/accByYear2.png', dpi=300)

    # MAE of all models in relation to amount of data in dataset
    plt.clf()
    plt.close()
    plt.figure(figsize=(10, 7))
    plt.xscale('log')
    plt.plot(*zip(*results), color='green')
    plt.scatter(*zip(*results), color='green')
    for i, (dataLength, error) in enumerate(results):
        if i == len(results) - 1:
            plt.annotate(f'{dataLength} images', (dataLength * 0.45, error))
        else:
            plt.annotate(f'{dataLength} images', (dataLength * 1.02, error))
    plt.ylabel('Error of model [years]')
    plt.xlabel('Amount of data used for training')
    plt.title(
        f'Mean Absolute Error of model in relation to amount of data in dataset')
    plt.savefig(f'{constants.RESULTS_DIRECTORY}/age/error.png', dpi=300)

    with open(f'{constants.RESULTS_DIRECTORY}/age/results.json', 'w', encoding="UTF-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)