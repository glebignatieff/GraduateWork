##
#   Dataset builder with multiprocessing
##

import os
import sqlite3
import pickle
from collections import OrderedDict
from math import ceil
from multiprocessing import Process, Queue

import mmh3
import numpy as np

from common import get_files_paths, split_list, update_progress


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


class DatasetBuilderProcess(Process):
    def __init__(self, process_id, file_list, mapping_dict, perm_level_dict, image_size, args):
        super().__init__(target=self)
        self.process_id = process_id
        self.mapping_dict = mapping_dict
        self.perm_level_dict = perm_level_dict
        self.image_size = image_size
        self.file_list = file_list
        self.total_files = len(file_list)
        self.queue = args[0]

    def is_valid_api_level(self, api_level):
        if api_level in AXPLORER_APIS or api_level in PSCOUT_APIS:
            return True
        else:
            return False

    def get_permission_level_by_api(self, api, api_level):
        if api.startswith('Landroid'):
            max_perm_level = PERM_PROTECTION_LEVEL['NO_LEVEL']
        else:
            max_perm_level = PERM_PROTECTION_LEVEL['UNKNOWN']

        if not self.is_valid_api_level(api_level):
            return max_perm_level

        if api in self.mapping_dict['API_' + str(api_level)]:
            perms = self.mapping_dict['API_' + str(api_level)][api]
            for perm in perms:
                if perm in self.perm_level_dict:
                    level = self.perm_level_dict[perm]
                    max_perm_level = max(max_perm_level, level)

        return max_perm_level

    def rgba2rgb(self, rgba_color):
        alpha = rgba_color[-1]
        rgb_bg = [0, 0, 0]  # rgb background
        rgb_color = [
            ceil((1 - alpha) * rgb_bg[0] + alpha * rgba_color[0]),    # 0 - r
            ceil((1 - alpha) * rgb_bg[1] + alpha * rgba_color[1]),    # 1 - g
            ceil((1 - alpha) * rgb_bg[2] + alpha * rgba_color[2])     # 2 - b
        ]

        return rgb_color

    def protection_level_to_alpha(self, level):
        return level / PERM_PROTECTION_LEVEL['DANGEROUS']

    def to_3dim_24bit(self, x):
        x &= 0xffffff
        ret = []
        for i in range(3):
            _8bit = (x >> 8 * (2 - i)) & 0xff
            ret.append(_8bit)
        return ret

    def unique(self, input_list, keep_order=False):
        if keep_order:
            return list(OrderedDict.fromkeys(input_list))
        else:
            return np.unique(input_list)

    def encode_api(self, api):
        return mmh3.hash(api) & 0xffffff

    def run(self):
        dataset = {}
        dataset['labels'] = []
        dataset['filenames'] = []

        for file in self.file_list:
            try:
                # TMP!!
                if os.path.getsize(file) > (7 << 20):   # to Mbs
                    continue
                #

                # Processing single file
                with open(file) as f:
                    apis = f.read().strip().split('\n')

                    # (image_size * rgb channels)
                    data_row = np.zeros(self.image_size * 3, dtype=np.uint8)

                    cnt = 0
                    # For every api
                    for api in apis:
                        v3_api = self.to_3dim_24bit(self.encode_api(api))               # encode api -> 3 dim vector
                        protection_level = self.get_permission_level_by_api(api, 16)    # get protection level of permission needed by api
                        alpha_level = self.protection_level_to_alpha(protection_level)  # map protection level to interval (0, 1)
                        rgb_api = self.rgba2rgb(v3_api + [alpha_level])                 # rgba (with api as rgb and protection level as apha) -> rgb

                        # data_row: (r channel, g channel, b channel)
                        data_row[cnt] = rgb_api[0]
                        data_row[cnt + self.image_size] = rgb_api[1]
                        data_row[cnt + self.image_size * 2] = rgb_api[2]

                        cnt += 1

                # stack new row with dataset
                if 'data' not in dataset:
                    dataset['data'] = np.array([data_row])
                else:
                    dataset['data'] = np.vstack((dataset['data'], data_row))

                # set label for current file
                if 'malware' in file:
                    dataset['labels'].append(1)
                else:
                    dataset['labels'].append(0)

                # save filename
                dataset['filenames'].append(os.path.basename(file).rstrip('.txt'))

                self.queue.put('done')
            except Exception as e:
                self.queue.put('done')
                print('\n%s\n%s\n' % (file, e))

        self.queue.put(dataset)
        print('----------------> Process %d is done!' % self.process_id)


def main():
    mapping_dict = load_mapping_data()
    perm_level_dict = get_perm_level_dict()
    api_seq_files = get_files_paths('api_sequences/')
    total_files = len(api_seq_files)
    image_size = 384 * 384  # Let it be :D

    # Give apks chunk for every process
    process_count = 15
    chunks = split_list(api_seq_files, process_count)

    # Multiprocessing stuff
    queue = Queue()
    processes = [
        DatasetBuilderProcess(i, chunks[i], mapping_dict, perm_level_dict,
                              image_size, (queue,)) for i in range(process_count)]

    for process in processes:
        process.start()

    # Progress bar
    done = 0
    for _ in range(total_files):
        queue.get()
        update_progress(done, total_files)
        done += 1

    dataset = {}
    dataset['labels'] = []
    dataset['filenames'] = []

    # Collect dataset chunks from every process
    for _ in range(process_count):
        dataset_chunk = queue.get()
        if dataset_chunk == 'done':
            print('c=========================================3 FUCK!')
        if 'data' not in dataset:
            dataset['data'] = dataset_chunk['data']
        else:
            dataset['data'] = np.vstack((dataset['data'], dataset_chunk['data']))
        dataset['labels'] += dataset_chunk['filenames']
        dataset['filenames'] += dataset_chunk['filenames']

    for process in processes:
        process.join()

    dataset['labels'] = np.array(dataset['labels'])
    dataset['filenames'] = np.array(dataset['filenames'])

    # Serialize dataset dictionary object
    with open('dataset.bin', 'wb') as pickle_file:
        pickle.dump(dataset, pickle_file)

    print('Dataset dictionary object is dumped to dataset.bin.')


if __name__ == '__main__':
    main()
