import pickle
from math import sqrt

import numpy as np
from sklearn.model_selection import train_test_split


with open('dataset/dataset_chunk_0.pkl', 'rb') as f:
    dataset_benign = pickle.load(f)

with open('dataset/dataset_chunk_5.pkl', 'rb') as f:
    dataset_malware = pickle.load(f)

dataset = {}
dataset['data'] = np.vstack((dataset_benign['data'], dataset_malware['data']))
dataset['labels'] = np.concatenate((dataset_benign['labels'], dataset_malware['labels']))
dataset['filenames'] = np.concatenate((dataset_benign['filenames'], dataset_malware['filenames']))

n_channels = 3  # rgb
n_samples = dataset['data'].shape[0]
h_w = int(sqrt(dataset['data'].shape[1] / n_channels))  # height = width
img_size = (h_w, h_w)

X = dataset['data'].reshape(n_samples, n_channels, *img_size).transpose(0, 2, 3, 1)
y = dataset['labels']

x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

with open('train/x_train.pkl', 'wb') as f:
    pickle.dump(x_train, f)

with open('train/x_test.pkl', 'wb') as f:
    pickle.dump(x_test, f)

with open('train/y_train.pkl', 'wb') as f:
    pickle.dump(y_train, f)

with open('train/y_test.pkl', 'wb') as f:
    pickle.dump(y_test, f)

#########################################################################################################

with open('train/x_train.pkl', 'rb') as f:
    x_train = pickle.load(f)

with open('train/x_test.pkl', 'rb') as f:
    x_test = pickle.load(f)

with open('train/y_train.pkl', 'rb') as f:
    y_train = pickle.load(f)

with open('train/y_test.pkl', 'rb') as f:
    y_test = pickle.load(f)
