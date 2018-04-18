import os
import sqlite3
from collections import OrderedDict

import mmh3
import numpy as np
# from sklearn.preprocessing import LabelEncoder

from common import get_unique_api_list
from common import get_files_paths


def to_3dim_24bit(x):
    x &= 0xffffff
    ret = []
    for i in range(3):
        _8bit = (x >> 8 * (2 - i)) & 0xff
        ret.append(_8bit)
    return ret


def unique(_list, keep_order=False):
    if keep_order:
        return list(OrderedDict.fromkeys(_list))
    else:
        return np.unique(_list)


def encode_api(api):
    return mmh3.hash(api) & 0xffffff


def encoding_apis_without_perm_level():
    unique_apis = get_unique_api_list()
    encoded_unique_apis = unique([encode_api(api) for api in unique_apis], True)
    # no_api = len(unique_apis)   # for padding

    # label_encoder = LabelEncoder()
    # integer_encoded = label_encoder.fit(unique_apis)

    api_seq_files = get_files_paths('api_sequences/')

    apis_vector = []
    labels = []
    for file in api_seq_files:
        with open(file) as f:
            apis = f.read().strip().split('\n')
            apis_vector.append([encode_api(api) for api in apis])
            # apis_vector.append(label_encoder.transform(apis))
            if 'malware' in file:
                labels.append(1)
            else:
                labels.append(0)

    # API inverse transform example
    print(apis_vector[0][0], unique_apis[encoded_unique_apis.index(apis_vector[0][0])])


##########################################################################################

# Permissions
normal_perms = 'data/permissions/normal.txt'
signature_perms = 'data/permissions/signature.txt'
dangerous_perms = 'data/permissions/dangerous.txt'


# Permission levels (tmp values)
PERM_PROTECTION_LEVEL = {
    'UNKNOWN':      0,
    'NORMAL':       1,
    'SIGNATURE':    2,
    'DANGEROUS':    3
}


AXPLORER_APIS = {'min': 16, 'max': 25}
PSCOUT_APIS = {'min': 9, 'max': 22}


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


def get_permission_level_by_api(cursor, api, api_level, perm_level_dict):
    query = "SELECT permission FROM {}_API_{} WHERE api='{}'"
    max_perm_level = PERM_PROTECTION_LEVEL['UNKNOWN']

    # axplorer query
    if api_level >= AXPLORER_APIS['min'] and api_level <= AXPLORER_APIS['max']:
        cursor.execute(query.format('AXPLORER', api_level, api))
        for perm in cursor.fetchall():
            if perm[0] in perm_level_dict:
                level = perm_level_dict[perm[0]]
                if level > max_perm_level:
                    max_perm_level = level

    # PScout query
    if api_level >= PSCOUT_APIS['min'] and api_level <= PSCOUT_APIS['max']:
        cursor.execute(query.format('PSCOUT', api_level, api))
        for perm in cursor.fetchall():
            if perm[0] in perm_level_dict:
                level = perm_level_dict[perm[0]]
                if level > max_perm_level:
                    max_perm_level = level

    return max_perm_level


perm_level_dict = get_perm_level_dict()


with sqlite3.connect('mappings/mapping.db') as conn:
    cursor = conn.cursor()
    perm_level = get_permission_level_by_api(cursor, 'Landroid/inputmethodservice/InputMethodService;->clearWallpaper()V', 16, perm_level_dict)
    print(perm_level)
