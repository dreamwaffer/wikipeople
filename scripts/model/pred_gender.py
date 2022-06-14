from __future__ import print_function
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.models as models
from torchvision import transforms
from torch.utils.data import Dataset, DataLoader
import os
import pandas as pd
from glob import glob
from tqdm import tqdm

from PIL import Image

USE_CUDA = True
NUM_EPO = 40
BATCH_SIZE = 64
BATCHES_PER_EPO = 100

device = torch.device("cuda") if USE_CUDA else torch.device("cpu")

model = models.resnet50(pretrained=True)
model.fc = nn.Sequential(nn.Linear(in_features=model.fc.in_features, out_features=2), torch.nn.Softmax())
model = model.to(device)

transform = transforms.Compose([
    transforms.ToTensor(),
    lambda x: x.float(),
    transforms.Normalize((0.1307,), (0.3081,))
])


class ImageDataset(Dataset):
    def __init__(self, annotations_file, img_dir, device, validation=False, validation_split_coef=0.9, transform=None):
        super().__init__()
        self.device = device
        self.img_labels = pd.read_csv(annotations_file, header=None)
        self.img_dir = img_dir
        self.img_files = glob(os.path.join(img_dir, '*'))
        split_thr = int(len(self.img_files) * validation_split_coef)
        self.transform = transform
        if validation:
            self.img_files = self.img_files[split_thr:]
            self.img_labels = self.img_labels[split_thr:]
        else:
            self.img_files = self.img_files[:split_thr]
            self.img_labels = self.img_labels[:split_thr]

    def __len__(self):
        return len(self.img_files)

    def __getitem__(self, idx):
        img_path = self.img_files[idx]
        image = Image.open(img_path)
        label = self.img_labels.iloc[idx, [0, 1]]
        vector = [label[0], label[1], 0 if label[1] == 1 else 1]
        label = torch.tensor(vector).float()
        if self.transform:
            image = self.transform(image)
        image = image[:3]  # remove alpha level
        if image.shape[0] == 2:
            image = image[:1]  # remove alpha level
        if image.shape[0] < 3:  # handle grayscale
            image = torch.cat([image, image, image], dim=0)
        if image.max() <= 1:
            image = image * 255
        image = image.to(self.device).float()
        label = label.to(self.device)
        return image, label


train_data = ImageDataset("./people.csv", "dataset_256", device, validation=False, validation_split_coef=0.9,
                          transform=transform)
valid_data = ImageDataset("./people.csv", "dataset_256", device, validation=True, validation_split_coef=0.9,
                          transform=transform)

train_dataloader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=False)
valid_dataloader = DataLoader(valid_data, batch_size=BATCH_SIZE, shuffle=False)

loss_fn = nn.BCELoss()
avg_loss = 0
n = 0

tq = tqdm(range(NUM_EPO))
optimizer = optim.Adam(model.parameters(), lr=0.0000001)

for e in tq:
    for item in tqdm(train_dataloader, total=BATCHES_PER_EPO):
        optimizer.zero_grad()
        data, label = item
        pred = model(data)
        # print(pred, label[:, 1:])
        # exit(0)
        loss = loss_fn(pred, label[:, 1:])
        loss.backward()
        optimizer.step()
        n += 1
        avg_loss += loss.item()
        if n > BATCHES_PER_EPO:
            break
    print("loss=" + str(avg_loss / n))
    n = 0
