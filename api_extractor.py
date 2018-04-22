from multiprocessing import Process, Queue
from zipfile import ZipFile, BadZipfile
import numpy as np
from androguard.core.bytecodes.dvm import DalvikVMFormat
from androguard.core.analysis.analysis import Analysis
from common import *


class ApiExtractorProcess(Process):
    def __init__(self, process_id, apks_list, args=()):
        super().__init__(target=self, args=args)
        self.process_id = process_id
        self.apks_list = apks_list
        self.total_apks = len(apks_list)
        self.queue = args[0]

    # Gets Android framework api calls
    def get_api_calls(self, dx):
        methods = []
        external_classes = dx.get_external_classes()
        for i in external_classes:
            class_name = i.get_vm_class()
            methods_list = class_name.get_methods()
            for method in methods_list:
                a = '%s' % method.get_class_name()
                b = '%s' % method.get_name()
                c = '%s' % method.get_descriptor()
                # filter android and java api calls
                if a.startswith('Landroid') or a.startswith('Ljava'):
                    methods.append(a + '->' + b + c)

        return list(set(methods))

    def run(self):
        unique_apis = []

        for apk in self.apks_list:
            try:
                with ZipFile(apk) as zipfile:
                    # find .dex files inside apk
                    dexes = [dex for dex in zipfile.namelist() if dex.endswith('.dex')]
                    dx = Analysis()
                    # analyze every .dex
                    for dex in dexes:
                        with zipfile.open(dex) as dexfile:
                            d = DalvikVMFormat(dexfile.read())
                            dx.add(d)
                    # creates cross references between classes, methods, etc. for all the .dex
                    dx.create_xref()

                    # extracting android apis
                    apis = self.get_api_calls(dx)
                    not_unique = unique_apis + apis
                    unique_apis = list(np.unique(not_unique))
                    print('Process %d: %.1f%%' %
                          (self.process_id, ((self.apks_list.index(apk) + 1) / self.total_apks) * 100))
            except BadZipfile as e:
                print('Bad zip file =========> %s' % apk)
            except Exception as e:
                print('\n%s\n%s\n' % (apk, e))

        self.queue.put(unique_apis)
        print('----------------> Process %d is done!' % self.process_id)


def main():
    path = 'apks/'
    apks_list = get_files_paths(path)
    np.random.shuffle(apks_list)
    total_apks = len(apks_list)

    # Give apks chunk for every process
    process_count = 10
    chunk_size = total_apks // process_count
    chunks = [
        apks_list[k:k + chunk_size]
        for k in range(0, total_apks, chunk_size)]

    # If not process_count | total_apks -> last one gets more!
    if len(chunks) > process_count:
        chunks[-2] += chunks[-1]
        del chunks[-1]

    queue = Queue()
    processes = [
        ApiExtractorProcess(i, chunks[i], (queue,)) for i in range(process_count)]

    for process in processes:
        process.start()

    api_list = []
    for i in range(process_count):
        api_list += queue.get()

    for process in processes:
        process.join()

    # # flatten list of lists and remove duplicates
    api_list = np.array(api_list).flatten()
    api_list = list(np.unique(api_list))

    with open('unique_apis.txt', 'w') as f:
        f.write('\n'.join(api_list))

    print('Done.')


if __name__ == '__main__':
    main()
