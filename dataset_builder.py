##
## Building dataset
##

import os
import sqlite3
import pickle
from collections import OrderedDict
from math import ceil

import mmh3
import numpy as np

from common import get_files_paths, get_unique_api_list, update_progress

# Permissions paths
normal_perms = 'data/permissions/normal.txt'
signature_perms = 'data/permissions/signature.txt'
dangerous_perms = 'data/permissions/dangerous.txt'

# Permission levels (tmp values)
PERM_PROTECTION_LEVEL = {
    'NO_LEVEL':     1,
    'UNKNOWN':      2,
    'NORMAL':       3,
    'SIGNATURE':    4,
    'DANGEROUS':    5
}

# Available api mapping levels
AXPLORER_APIS = [16, 17, 18, 19, 21, 22, 23, 25, 25]
PSCOUT_APIS = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22]


def to_3dim_24bit(x):
    x &= 0xffffff
    ret = []
    for i in range(3):
        _8bit = (x >> 8 * (2 - i)) & 0xff
        ret.append(_8bit)
    return ret


def unique(input_list, keep_order=False):
    if keep_order:
        return list(OrderedDict.fromkeys(input_list))
    else:
        return np.unique(input_list)


def encode_api(api):
    return mmh3.hash(api) & 0xffffff


def get_perm_level_dict():
    ret = {}

    with open(normal_perms) as f:
        for perm in f.read().strip().split('\n'):
            ret[perm] = PERM_PROTECTION_LEVEL['NORMAL']

    with open(signature_perms) as f:
        for perm in f.read().strip().split('\n'):
            ret[perm] = PERM_PROTECTION_LEVEL['SIGNATURE']

    with open(dangerous_perms) as f:
        for perm in f.read().strip().split('\n'):
            ret[perm] = PERM_PROTECTION_LEVEL['DANGEROUS']

    return ret


def is_valid_api_level(api_level):
    if api_level in AXPLORER_APIS or api_level in PSCOUT_APIS:
        return True
    else:
        return False


def get_permission_level_by_api(api, api_level, mapping_dict, perm_level_dict):
    if api.startswith('Landroid'):
        max_perm_level = PERM_PROTECTION_LEVEL['NO_LEVEL']
    else:
        max_perm_level = PERM_PROTECTION_LEVEL['UNKNOWN']

    if not is_valid_api_level(api_level):
        return max_perm_level

    if api in mapping_dict['API_' + str(api_level)]:
        perms = mapping_dict['API_' + str(api_level)][api]
        for perm in perms:
            if perm in perm_level_dict:
                level = perm_level_dict[perm]
                max_perm_level = max(max_perm_level, level)

    return max_perm_level


def rgba2rgb(rgba_color):
    alpha = rgba_color[-1]
    rgb_bg = [0xff, 0xff, 0xff]  # rgb background
    rgb_color = [
        ceil((1 - alpha) * rgb_bg[0] + alpha * rgba_color[0]),    # 0 - r
        ceil((1 - alpha) * rgb_bg[1] + alpha * rgba_color[1]),    # 1 - g
        ceil((1 - alpha) * rgb_bg[2] + alpha * rgba_color[2])     # 2 - b
    ]

    return rgb_color


def protection_level_to_alpha(level):
    return level / PERM_PROTECTION_LEVEL['DANGEROUS']


def load_mapping_data():
    ret = {}

    with sqlite3.connect('mappings/mapping.db') as conn:
        cursor = conn.cursor()

        table_names = []
        cursor.execute('SELECT sql FROM sqlite_master WHERE sql IS NOT NULL')
        table_names = [sql[0].split()[2] for sql in cursor.fetchall()]

        for table_name in table_names:
            key = '_'.join(table_name.split('_')[1:])
            if key not in ret:
                ret[key] = {}
            cursor.execute('SELECT * FROM ' + table_name)
            for row in cursor.fetchall():
                if row[0] in ret[key]:
                    if not row[1] in ret[key][row[0]]:
                        ret[key][row[0]].append(row[1])
                else:
                    ret[key][row[0]] = [row[1]]

    return ret


def main():
    mapping_dict = load_mapping_data()
    perm_level_dict = get_perm_level_dict()
    # unique_apis = get_unique_api_list()
    # encoded_unique_apis = unique([encode_api(api) for api in unique_apis], True)
    api_seq_files = get_files_paths('api_sequences/')
    # benign_files = [file for file in api_seq_files if 'benign' in file]
    # malware_files = [file for file in api_seq_files if 'malware' in file]
    image_size = 200 * 200  # Let it be :D

    dataset = {}
    dataset['labels'] = [int(i >= 1000) for i in range(len(api_seq_files))]
    dataset['filenames'] = []

    print('Building dataset...')

    for file in api_seq_files:
        with open(file) as f:
            apis = f.read().strip().split('\n')

            # (image_size * rgb)
            data_row = np.zeros(image_size * 3, dtype=np.uint8)

            cnt = 0
            for api in apis:
                v3_api = to_3dim_24bit(encode_api(api))
                protection_level = get_permission_level_by_api(api, 16, mapping_dict, perm_level_dict)
                alpha_level = protection_level_to_alpha(protection_level)
                rgb_api = rgba2rgb(v3_api + [alpha_level])

                data_row[cnt] = rgb_api[0]
                data_row[cnt + image_size] = rgb_api[1]
                data_row[cnt + image_size * 2] = rgb_api[2]

                cnt += 1
                # apis_vector.append(rgba2rgb(v3_api + [alpha_level]))   # rgba -> rgb
                # apis_vector.append(v3_api + [alpha_level])   # full rgba

        if 'data' not in dataset:
            dataset['data'] = data_row
        else:
            dataset['data'] = np.vstack((dataset['data'], data_row))

        dataset['filenames'].append(file)

        update_progress(api_seq_files.index(file), len(api_seq_files))
    print()

    with open('mydataset.bin', 'wb') as pickle_file:
        pickle.dump(dataset, pickle_file)

    print('Dataset dictionary object is dumped to mydataset.bin.')


if __name__ == '__main__':
    main()
