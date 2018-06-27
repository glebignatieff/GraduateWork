import gc
import pickle
from math import sqrt

import numpy as np
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE

with open('dataset/dataset_chunk_0.pkl', 'rb') as f:
    dataset = pickle.load(f)

with open('dataset/dataset_chunk_1.pkl', 'rb') as f:
    chunk = pickle.load(f)
    dataset['data'] = np.vstack((dataset['data'], chunk['data']))
    dataset['labels'] = np.concatenate((dataset['labels'], chunk['labels']))

with open('dataset/dataset_chunk_2.pkl', 'rb') as f:
    chunk = pickle.load(f)
    dataset['data'] = np.vstack((dataset['data'], chunk['data']))
    dataset['labels'] = np.concatenate((dataset['labels'], chunk['labels']))

with open('dataset/dataset_chunk_3.pkl', 'rb') as f:
    chunk = pickle.load(f)
    dataset['data'] = np.vstack((dataset['data'], chunk['data']))
    dataset['labels'] = np.concatenate((dataset['labels'], chunk['labels']))

with open('dataset/dataset_chunk_4.pkl', 'rb') as f:
    chunk = pickle.load(f)
    dataset['data'] = np.vstack((dataset['data'], chunk['data']))
    dataset['labels'] = np.concatenate((dataset['labels'], chunk['labels']))

with open('dataset/dataset_chunk_5.pkl', 'rb') as f:
    chunk = pickle.load(f)
    dataset['data'] = np.vstack((dataset['data'], chunk['data']))
    dataset['labels'] = np.concatenate((dataset['labels'], chunk['labels']))

del chunk
gc.collect()

n_channels = 3  # rgb
n_samples = dataset['data'].shape[0]
h_w = int(sqrt(dataset['data'].shape[1] / n_channels))  # height = width
img_size = (h_w, h_w)

# make it array of h_w x h_w RGB images
X = dataset['data'].reshape(n_samples, n_channels, *img_size).transpose(0, 2, 3, 1)
y = dataset['labels']

x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

n_total = x_train.shape[0]
chunk_size = n_total // 3

x_train_chunks  = [
        x_train[k:k + chunk_size]
        for k in range(0, n_total, chunk_size)]

x_train_chunks[2] = np.vstack((x_train_chunks[2], x_train_chunks[3]))

for i in range(len(x_train_chunks)):
    with open('split/x_train_%d.pkl' % i, 'wb') as f:
        pickle.dump(x_train_chunks[i], f)

with open('split/x_test.pkl', 'wb') as f:
    pickle.dump(x_test, f)

with open('split/y_train.pkl', 'wb') as f:
    pickle.dump(y_train, f)

with open('split/y_test.pkl', 'wb') as f:
    pickle.dump(y_test, f)
