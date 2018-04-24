# from __future__ import division

import os
import sys
import pickle
import argparse
from math import sqrt

import numpy as np
import matplotlib.pyplot as plt
# from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split


# Prints text progress bar
def update_progress(current, total):
    amtDone = (current + 1) / total
    sys.stdout.write("\rProgress: [{0:50s}] {1:.1f}%".format('#' * int(amtDone * 50), amtDone * 100))


# Gets all the files from a given path
def get_files_paths(path):
    files_paths = []
    for dirname, dirnames, filenames in os.walk(path):
        for filename in filenames:
            files_paths.append(os.path.join(os.path.abspath(dirname), filename))
    return files_paths


# Checks if a path is an actual file
def is_file(filename):
    filename = os.path.abspath(filename)
    if not os.path.isfile(filename):
        msg = "{0} is not a file".format(filename)
        raise argparse.ArgumentTypeError(msg)
    else:
        return filename


# Checks if a path is an actual directory
def is_dir(dirname):
    dirname = os.path.abspath(dirname)
    if not os.path.isdir(dirname):
        msg = "{0} is not a directory".format(dirname)
        raise argparse.ArgumentTypeError(msg)
    else:
        return dirname


# Returns list of unique apis
def get_unique_api_list():
    ret = []
    with open('data/unique_apis.txt') as f:
        ret = f.read().strip().split('\n')
    return ret


# Returns set of unique apis
def get_unique_api_set():
    ret = {}
    with open('data/unique_apis.txt') as f:
        ret = set(f.read().strip().split('\n'))
    return ret


# Shows rgb image
#
# Example on CIFAR10 dataset
#
# with open('data_batch_1', 'rb') as f:
#     dataset = pickle.load(f, encoding='bytes')
#
# img0 = dataset[b'data'][np.random.randint(1, 10000)]
# show_rgb_image(img0, (32, 32))
#
def show_rgb_image(img_row, size_tuple):
    img = img_row.reshape(3, *size_tuple).transpose([1, 2, 0])
    plt.imshow(img)
    plt.show()


# Loads serialized dictionary,
# prepares it for learning and returns training and testing sets
def load_dataset():
    with open('data/dataset.bin', 'rb') as f:
        dataset = pickle.load(f)

    # prepare data for machine learning
    n_channels = 3  # rgb
    n_samples = dataset['data'].shape[0]
    h_w = int(sqrt(dataset['data'].shape[1] / n_channels))  # height = width
    img_size = (h_w, h_w)

    # make it array of h_w x h_w RGB images
    X = dataset['data'].reshape(n_samples, n_channels, *img_size).transpose(0, 2, 3, 1)
    y = dataset['labels']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return (X_train, y_train), (X_test, y_test)

    # n_images = dataset['data'].shape[0]
    # rand_img = dataset['data'][np.random.randint(1, n_images)]
    # show_rgb_image(rand_img, (200, 200))


if __name__ == '__main__':
    load_dataset()
