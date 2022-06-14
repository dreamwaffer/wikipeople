from __future__ import print_function, division

import json
from textwrap import wrap

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
import time
import os
import copy


def run(data_dir, eval_dir, resultDirectory, runIndex):
    def train_model(model, criterion, optimizer, scheduler, num_epochs=25):
        since = time.time()

        best_model_wts = copy.deepcopy(model.state_dict())
        best_acc = 0.0
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
                        _, preds = torch.max(outputs, 1)
                        loss = criterion(outputs, labels)

                        # backward + optimize only if in training phase
                        if phase == 'train':
                            loss.backward()
                            optimizer.step()

                    # statistics
                    running_loss += loss.item() * inputs.size(0)
                    running_corrects += torch.sum(preds == labels.data)
                if phase == 'train':
                    scheduler.step()

                epoch_loss = running_loss / dataset_sizes[phase]
                epoch_acc = running_corrects.double() / dataset_sizes[phase]

                progress[phase].append(Tensor.cpu(epoch_acc))

                print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

                # deep copy the model
                if phase == 'val' and epoch_acc > best_acc:
                    best_acc = epoch_acc
                    best_model_wts = copy.deepcopy(model.state_dict())

            print()

        time_elapsed = time.time() - since
        print(f'Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s')
        print(f'Best val Acc: {best_acc:.10f}')

        # create graphs with progress
        plt.clf()
        plt.close()
        x = [item for item in range(1, num_epochs + 1)]
        for index, (phase, values) in enumerate(progress.items()):
            plt.figure(figsize=(10, 7))
            plt.plot(x, values, color='green')
            plt.ylabel('Accuracy of model')
            plt.xlabel('Phase of training')
            plt.title(
                f'Accuracy of model on {"training" if phase == "train" else "validation"} data throughout the training')
            plt.savefig(f'{resultDirectory}/{runIndex}/acc{index}', dpi=300)

        # load best model weights
        model.load_state_dict(best_model_wts)
        return model

    def test_model(model, criterion):
        was_training = model.training
        model.eval()
        running_loss = 0.0
        running_corrects = 0

        with torch.no_grad():
            for i, (inputs, labels) in enumerate(dataloaders['test']):
                inputs = inputs.to(device)
                labels = labels.to(device)

                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                loss = criterion(outputs, labels)

                if i < 10:
                    plt.clf()
                    plt.close()
                    plt.figure(figsize=(8, 3))
                    out = torchvision.utils.make_grid(inputs.cpu().data,
                                                      out=torchvision.utils.make_grid(inputs.cpu().data))
                    imsave(out, f'{resultDirectory}/{runIndex}/test{i}.png', real=[class_names[x] for x in labels],
                           predicted=[class_names[x] for x in preds])

                # statistics
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            test_loss = running_loss / dataset_sizes['test']
            test_acc = running_corrects.double() / dataset_sizes['test']

            print(f'Test Loss: {test_loss:.4f} Acc: {test_acc:.10f}')
            model.train(mode=was_training)

        return Tensor.cpu(test_acc).item()

    def imsave(inp, location, real, predicted):
        """Imshow for Tensor."""
        inp = inp.numpy().transpose((1, 2, 0))
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        inp = std * inp + mean
        inp = np.clip(inp, 0, 1)
        plt.imshow(inp)
        # text = f'Real: {real}\nPredicted: {predicted}'
        plt.figtext(0.5, 0.2, f'Real: {real}', wrap=True, horizontalalignment='center', fontsize=8)
        plt.figtext(0.5, 0.1, f'Pred: {predicted}', wrap=True, horizontalalignment='center', fontsize=8)
        # for realItem, predItem in zip(real, predicted):
        #     plt.figtext(0.01, 0.1, realItem)
        # plt.title(title, fontdict={'fontsize': 8})
        plt.xticks([])
        plt.yticks([])
        plt.pause(0.001)  # pause a bit so that plots are updated
        plt.savefig(location)

    cudnn.benchmark = True
    BATCH_SIZE = 100
    NUM_EPOCHS = 30
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
                                      num_workers=10)
                   for x in ['train', 'val']}
    dataloaders['test'] = torchDataloader(image_datasets['test'],
                                          batch_size=8,
                                          shuffle=True,
                                          num_workers=4)
    dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val', 'test']}
    class_names = image_datasets['train'].classes
    device = torch.device(f"cuda:1" if torch.cuda.is_available() else "cpu")
    model_ft = models.resnet50(pretrained=True)
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
    torch.save(model_ft.state_dict(), f'{resultDirectory}/{runIndex}/model.pt')
    acc = test_model(model_ft, criterion)
    return acc


if __name__ == '__main__':
    resultDirectory = 'results'

    if not os.path.exists(resultDirectory):
        os.makedirs(resultDirectory)

    results = []
    iterationsNum = 11

    for i in range(iterationsNum):
        print(f'Starting model {i}')
        if not os.path.exists(f'{resultDirectory}/{i}'):
            os.makedirs(f'{resultDirectory}/{i}')
        results.append(run(f'/datagrid/personal/kotrblu2/1/finalTestDataBig/{i}',
                           f'/datagrid/personal/kotrblu2/1/finalTestDataBig/eval',
                           resultDirectory, i))

    x = [item for item in range(1, iterationsNum + 1)]
    plt.figure(figsize=(10, 7))
    plt.plot(x, results, color='green')
    plt.ylabel('Accuracy')
    plt.xlabel('Number of model')
    plt.title(
            f'Accuracy of model in relation to amount of general data in dataset')
    plt.savefig(f'{resultDirectory}/acc.png', dpi=300)

    with open(f'{resultDirectory}/results.json', 'w', encoding="UTF-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
