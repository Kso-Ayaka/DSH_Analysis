package_paths = [
    "/home/xxx/PycharmProjects/fghash/data",
    "/home/xxx/PycharmProjects/fghash"
]
import sys;
for pth in package_paths:
    sys.path.append(pth)
import torch
import numpy as np

import os
import pandas as pd
from torchvision.datasets.folder import default_loader
from torchvision.datasets.utils import download_url
from torch.utils.data import Dataset
from torch.utils.data.dataloader import DataLoader
from PIL import Image, ImageFile

from data.transform import encode_onehot
from data.transform import train_transform, query_transform
import scipy.io as scio
 
def load_data(root, batch_size, num_workers,zero_shot_classes):
    StanfordDog.init(root,zero_shot_classes)
    query_dataset = StanfordDog(root, 'query', query_transform())
    train_dataset = StanfordDog(root, 'train', train_transform())
    retrieval_dataset = StanfordDog(root, 'retrieval', query_transform())
    query4zero_shot_dataset = StanfordDog(root, 'query4zero_shot', query_transform())
    database4zero_shot_dataset = StanfordDog(root, 'database4zero_shot', query_transform())
    print(len(query_dataset))
    print(len(train_dataset))

    query_dataloader = DataLoader(
        query_dataset,
        batch_size=batch_size,
        pin_memory=True,
        num_workers=num_workers,
    )
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        pin_memory=True,
        num_workers=num_workers,
    )
    retrieval_dataloader = DataLoader(
        retrieval_dataset,
        batch_size=batch_size,
        pin_memory=True,
        num_workers=num_workers,
    )
    query4zero_shot_dataloader = DataLoader(
        query4zero_shot_dataset,
        batch_size=batch_size,
        pin_memory=True,
        num_workers=num_workers
    )

    database4zero_shot_dataloader = DataLoader(
        database4zero_shot_dataset,
        batch_size=batch_size,
        pin_memory=True,
        num_workers=num_workers
    )

    return query_dataloader, train_dataloader, retrieval_dataloader, query4zero_shot_dataloader, database4zero_shot_dataloader



class StanfordDog(Dataset):
    base_folder = 'images/'

    def __init__(self, root, mode, transform=None, loader=default_loader):
        self.root = os.path.expanduser(root)
        self.transform = transform
        self.loader = default_loader

        if mode == 'train':
            self.data = StanfordDog.TRAIN_DATA
            self.targets = StanfordDog.TRAIN_TARGETS
        elif mode == 'query':
            self.data = StanfordDog.QUERY_DATA
            self.targets = StanfordDog.QUERY_TARGETS
        elif mode == 'retrieval':
            self.data = StanfordDog.RETRIEVAL_DATA
            self.targets = StanfordDog.RETRIEVAL_TARGETS
        elif mode == 'query4zero_shot':
            self.data = StanfordDog.QUERY_DATA4ZERO_SHOT
            self.targets = StanfordDog.QUERY_TARGETS4ZERO_SHOT
        elif mode == 'database4zero_shot':
            self.data = StanfordDog.DATABASE_DATA4ZERO_SHOT
            self.targets = StanfordDog.DATABASE_TARGETS4ZERO_SHOT
        else:
            raise ValueError(r'Invalid arguments: mode, can\'t load dataset!')


    @staticmethod
    def init(root,zero_shot_classes = 6):
        class4train = 120-zero_shot_classes
        #Here should change official matlab file to txt.
        images_train = pd.read_csv(os.path.join(root,'train.txt'), sep=' ', names=['filepath', 'target'])
        images_test = pd.read_csv(os.path.join(root,'test.txt'), sep=' ', names=['filepath', 'target'])
        train_images = []
        label_list_train = []
        img_id_train = []
        for i in range(len(images_train)):
            train_images.append(images_train['filepath'][i])
            label_list_train.append(int(images_train['target'][i]))
            img_id_train.append(i+1)
        
        k = len(train_images)
        test_images = []
        label_list_test = []
        img_id_test = []
        for i in range(len(images_test)):
            test_images.append(images_test['filepath'][i])
            label_list_test.append(int(images_test['target'][i]))
            img_id_test.append(k+i+1)
   

        images_train = []
        for i in range(len(train_images)):
            images_train.append([img_id_train[i], 'images/'+train_images[i], label_list_train[i]])
        images_train = pd.DataFrame(images_train, columns=['img_id', 'filepath', 'target'])
        
        images_test = []
        for i in range(len(test_images)):
            images_test.append([img_id_test[i], 'images/'+test_images[i], label_list_test[i]])
        images_test = pd.DataFrame(images_test, columns=['img_id', 'filepath', 'target'])

        train_data_all = images_train
        test_data_all = images_test

        train_data = train_data_all[train_data_all['target'] <= class4train]
        test_data = test_data_all[test_data_all['target'] <= class4train]

        query_data4zero_shot = test_data_all[test_data_all['target'] > class4train]
        database_4zero_shot = train_data_all[train_data_all['target'] > class4train]
        # # Split dataset
        # StanfordDog.QUERY_DATA = test_data['filepath'].to_numpy()
        # StanfordDog.QUERY_TARGETS = encode_onehot((test_data['target'] - 1).tolist(), 120)

        # StanfordDog.TRAIN_DATA = train_data['filepath'].to_numpy()
        # StanfordDog.TRAIN_TARGETS = encode_onehot((train_data['target'] - 1).tolist(), 120)

        # StanfordDog.RETRIEVAL_DATA = train_data['filepath'].to_numpy()
        # StanfordDog.RETRIEVAL_TARGETS = encode_onehot((train_data['target'] - 1).tolist(), 120)
        # Split dataset
        StanfordDog.QUERY_DATA = test_data['filepath'].to_numpy()
        StanfordDog.QUERY_TARGETS = encode_onehot((test_data['target'] - 1).tolist(), 120)

        StanfordDog.TRAIN_DATA = train_data['filepath'].to_numpy()
        StanfordDog.TRAIN_TARGETS = encode_onehot((train_data['target'] - 1).tolist(), class4train)

        StanfordDog.RETRIEVAL_DATA = train_data['filepath'].to_numpy()
        StanfordDog.RETRIEVAL_TARGETS = encode_onehot((train_data['target'] - 1).tolist(), 120)

        StanfordDog.QUERY_DATA4ZERO_SHOT = query_data4zero_shot['filepath'].to_numpy()
        StanfordDog.QUERY_TARGETS4ZERO_SHOT = encode_onehot((query_data4zero_shot['target'] -1 ).tolist(), 120)

        StanfordDog.DATABASE_DATA4ZERO_SHOT = database_4zero_shot['filepath'].to_numpy()
        StanfordDog.DATABASE_TARGETS4ZERO_SHOT = encode_onehot((database_4zero_shot['target'] - 1).tolist(), 120)


    def get_onehot_targets(self):
        return torch.from_numpy(self.targets).float()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        img = Image.open(os.path.join(self.root, self.data[idx])).convert('RGB')

        if self.transform is not None:
            img = self.transform(img)

        return img, self.targets[idx], idx


# def main():
#     query_dataloader, train_dataloader, retrieval_dataloader=load_data('/dataset/StanfordDog/', 16, 4)

# main()