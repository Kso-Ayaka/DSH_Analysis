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

from data.triplet_sampler import PKSampler, PKSampler2

def load_data(root, batch_size, num_workers,zero_shot_classes = 50, sampler=None):
    #1
    Cub2011.init(root, zero_shot_classes=zero_shot_classes)
    query_dataset = Cub2011(root, 'query', query_transform())
    train_dataset = Cub2011(root, 'train', train_transform())
    retrieval_dataset = Cub2011(root, 'retrieval', query_transform())
    query4zero_shot_dataset = Cub2011(root, 'query4zero_shot', query_transform())
    database4zero_shot_dataset = Cub2011(root, 'database4zero_shot', query_transform())


    query_dataloader = DataLoader(
        query_dataset,
        batch_size=batch_size,
        pin_memory=True,
        num_workers=num_workers,
    )
    if sampler == 'PK':
        p = 16
        k = 5
        pksampler = PKSampler2(train_dataset, p, k)
        train_dataloader = DataLoader(
            train_dataset,
            batch_size=p*k,
            pin_memory=True,
            num_workers=num_workers,
            sampler=pksampler,
        )
    else:
        train_dataloader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            pin_memory=True,
            num_workers=num_workers
        )
    retrieval_dataloader = DataLoader(
        retrieval_dataset,
        batch_size=batch_size,
        pin_memory=True,
        num_workers=num_workers
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


class Cub2011(Dataset):
    base_folder = 'images/'
    url = 'http://www.vision.caltech.edu/visipedia-data/CUB-200-2011/CUB_200_2011.tgz'
    filename = 'CUB_200_2011.tgz'
    tgz_md5 = '97eceeb196236b17998738112f37df78'

    def __init__(self, root, mode, transform=None, loader=default_loader):
        self.root = os.path.expanduser(root)
        self.transform = transform
        self.loader = default_loader

        self.label_to_samples = Cub2011.label_to_samples
        if mode == 'train':
            self.data = Cub2011.TRAIN_DATA
            self.targets = Cub2011.TRAIN_TARGETS
        elif mode == 'query':
            self.data = Cub2011.QUERY_DATA
            self.targets = Cub2011.QUERY_TARGETS
        elif mode == 'retrieval':
            self.data = Cub2011.RETRIEVAL_DATA
            self.targets = Cub2011.RETRIEVAL_TARGETS
        elif mode == 'query4zero_shot':
            self.data = Cub2011.QUERY_DATA4ZERO_SHOT
            self.targets = Cub2011.QUERY_TARGETS4ZERO_SHOT
        elif mode == 'database4zero_shot':
            self.data = Cub2011.DATABASE_DATA4ZERO_SHOT
            self.targets = Cub2011.DATABASE_TARGETS4ZERO_SHOT
        else:
            raise ValueError(r'Invalid arguments: mode, can\'t load dataset!')




    @staticmethod
    def init(root, zero_shot_classes=50):
        class4train = 200-zero_shot_classes
        images = pd.read_csv(os.path.join(root, 'images.txt'), sep=' ',
                             names=['img_id', 'filepath'])
        image_class_labels = pd.read_csv(os.path.join(root, 'image_class_labels.txt'),
                                         sep=' ', names=['img_id', 'target'])
        train_test_split = pd.read_csv(os.path.join(root, 'train_test_split.txt'),
                                       sep=' ', names=['img_id', 'is_training_img'])

        data = images.merge(image_class_labels, on='img_id')
        all_data = data.merge(train_test_split, on='img_id')
        all_data['filepath'] = 'images/' + all_data['filepath']
        # train_data = all_data[all_data['is_training_img'] == 1]
        # test_data = all_data[all_data['is_training_img'] == 0]
        train_data = all_data[(all_data['is_training_img'] == 1) & (all_data['target'] <= class4train) ]
        test_data = all_data[(all_data['is_training_img'] == 0) & (all_data['target'] <= class4train)]


        query_data4zero_shot = all_data[(all_data['is_training_img'] == 0) & (all_data['target'] > class4train)]
        database_4zero_shot = all_data[(all_data['is_training_img'] == 1) & (all_data['target'] > class4train)]



        # train_data.to_csv("/disk/8T/wangp/zero_shot_hash/fghash-zero/train_data.csv")
        # query_data4zero_shot.to_csv("/disk/8T/wangp/zero_shot_hash/fghash-zero/query_data4zero_shot.csv")


################

        # Split dataset
        # Cub2011.QUERY_DATA = test_data['filepath'].to_numpy()
        # Cub2011.QUERY_TARGETS = encode_onehot((test_data['target'] - 1).tolist(), class4train)

        # Cub2011.TRAIN_DATA = train_data['filepath'].to_numpy()
        # Cub2011.TRAIN_TARGETS = encode_onehot((train_data['target'] - 1).tolist(), class4train)

        # Cub2011.RETRIEVAL_DATA = train_data['filepath'].to_numpy()
        # Cub2011.RETRIEVAL_TARGETS = encode_onehot((train_data['target'] - 1).tolist(), class4train)

        # Cub2011.QUERY_DATA4ZERO_SHOT = query_data4zero_shot['filepath'].to_numpy()
        # Cub2011.QUERY_TARGETS4ZERO_SHOT = encode_onehot((query_data4zero_shot['target'] -1 -class4train).tolist(), zero_shot_classes)

        # Cub2011.DATABASE_DATA4ZERO_SHOT = database_4zero_shot['filepath'].to_numpy()
        # Cub2011.DATABASE_TARGETS4ZERO_SHOT = encode_onehot((database_4zero_shot['target'] - 1-class4train).tolist(), zero_shot_classes)
        # Cub2011.label_to_samples = {}
        Cub2011.QUERY_DATA = test_data['filepath'].to_numpy()
        Cub2011.QUERY_TARGETS = encode_onehot((test_data['target'] - 1).tolist(), 200)

        Cub2011.TRAIN_DATA = train_data['filepath'].to_numpy()
        Cub2011.TRAIN_TARGETS = encode_onehot((train_data['target'] - 1).tolist(), class4train)

        Cub2011.RETRIEVAL_DATA = train_data['filepath'].to_numpy()
        Cub2011.RETRIEVAL_TARGETS = encode_onehot((train_data['target'] - 1).tolist(), 200)

        Cub2011.QUERY_DATA4ZERO_SHOT = query_data4zero_shot['filepath'].to_numpy()
        Cub2011.QUERY_TARGETS4ZERO_SHOT = encode_onehot((query_data4zero_shot['target'] -1 ).tolist(), 200)

        Cub2011.DATABASE_DATA4ZERO_SHOT = database_4zero_shot['filepath'].to_numpy()
        Cub2011.DATABASE_TARGETS4ZERO_SHOT = encode_onehot((database_4zero_shot['target'] - 1).tolist(), 200)
        Cub2011.label_to_samples = {}
        keys = (train_data['target'] - 1).tolist()
        for key in keys:
            Cub2011.label_to_samples[key] = list(np.where(train_data['target'] - 1 == key)[0])


    def get_onehot_targets(self):
        return torch.from_numpy(self.targets).float()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        img = Image.open(os.path.join(self.root, self.data[idx])).convert('RGB')

        if self.transform is not None:
            img = self.transform(img)

        return img, self.targets[idx], idx



# class Cub2011_UC(Dataset):
#     base_folder = 'images/'
#     url = 'http://www.vision.caltech.edu/visipedia-data/CUB-200-2011/CUB_200_2011.tgz'
#     filename = 'CUB_200_2011.tgz'
#     tgz_md5 = '97eceeb196236b17998738112f37df78'

#     def __init__(self, root, mode, transform=None, loader=default_loader):
#         self.root = os.path.expanduser(root)
#         self.transform = transform
#         self.loader = default_loader

#         if mode == 'train':
#             self.data = Cub2011.TRAIN_DATA
#             self.targets = Cub2011.TRAIN_TARGETS
#         elif mode == 'query':
#             self.data = Cub2011.QUERY_DATA
#             self.targets = Cub2011.QUERY_TARGETS
#         elif mode == 'retrieval':
#             self.data = Cub2011.RETRIEVAL_DATA
#             self.targets = Cub2011.RETRIEVAL_TARGETS
#         else:
#             raise ValueError(r'Invalid arguments: mode, can\'t load dataset!')



#     @staticmethod
#     def init(root):
#         images = pd.read_csv(os.path.join(root, 'images.txt'), sep=' ',
#                              names=['img_id', 'filepath'])
#         image_class_labels = pd.read_csv(os.path.join(root, 'image_class_labels.txt'),
#                                          sep=' ', names=['img_id', 'target'])
#         train_test_split = pd.read_csv(os.path.join(root, 'train_test_split.txt'),
#                                        sep=' ', names=['img_id', 'is_training_img'])

#         data = images.merge(image_class_labels, on='img_id')
#         all_data = data.merge(train_test_split, on='img_id')
#         all_data['filepath'] = 'images/' + all_data['filepath']
#         train_data = all_data[all_data['is_training_img'] == 1]
#         test_data = all_data[all_data['is_training_img'] == 0]


#         # Split dataset
#         Cub2011.QUERY_DATA = test_data['filepath'].to_numpy()
#         Cub2011.QUERY_TARGETS = encode_onehot((test_data['target'] - 1).tolist(), 200)

#         Cub2011.TRAIN_DATA = train_data['filepath'].to_numpy()
#         Cub2011.TRAIN_TARGETS = encode_onehot((train_data['target'] - 1).tolist(), 200)

#         Cub2011.RETRIEVAL_DATA = train_data['filepath'].to_numpy()
#         Cub2011.RETRIEVAL_TARGETS = encode_onehot((train_data['target'] - 1).tolist(), 200)


#     def get_onehot_targets(self):
#         return torch.from_numpy(self.targets).float()

#     def __len__(self):
#         return len(self.data)

#     def __getitem__(self, idx):
#         img = Image.open(os.path.join(self.root, self.data[idx])).convert('RGB')

#         if self.transform is not None:
#             img = self.transform(img)

#         return img, self.targets[idx], idx

