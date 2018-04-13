##
#
# INVOKE Dalvik opcodes
#
# invoke-virtual 6e
# invoke-super 6f
# invoke-direct 70
# invoke-static 71
# invoke-interface 72
# invoke-virtual/range 74
# invoke-super/range 75
# invoke-direct/range 76
# invoke-static/range 77
# invoke-interface/range 78
#
##

from multiprocessing import Process, Queue
import numpy as np
import gc
# from androguard.core.bytecodes.apk import APK
# from androguard.core.bytecodes.dvm import DalvikVMFormat
# from androguard.core.analysis.analysis import Analysis
from androguard.misc import AnalyzeAPK
from common import *

test_apk = 'apks/malware/5afd15118715b8594e552a250ac82560.apk'


# Gets Android framework api calls
def get_api_calls(dx):
    methods = []
    external_classes = dx.get_external_classes()
    for i in external_classes:
        class_name = i.get_vm_class()
        methods_list = class_name.get_methods()
        for method in methods_list:
            a = '%s' % method.get_class_name()
            b = '%s' % method.get_name()
            # c = '%s' % method.get_descriptor()
            # filter android api calls
            if a.startswith('Landroid'):
                methods.append(a + '->' + b + c)

    return list(set(methods))


def get_api_sequence(d, api_list):
    api_sequence = []

    # for every .dex file
    for _d in d:
        # for every code block in .dex
        for code_block in _d.get_codes_item().code:
            # for every instruction in code block
            for ins in code_block.code.get_instuctions():
                # we look for invoke-* instructions from 0x6e to 0x78
                if 0x6e <= ins.get_op_value() <= 0x78:
                    continue
                operands = ins.get_operands()
                api = operands[-1][-1]
                if api in api_list:
                    api_sequence.append(api)

    return api_sequence


class ApiExtractorProcess(Process):
    def __init__(self, n, apks_list, args=()):
        super().__init__(target=self, args=args)
        self.process_id = n
        self.apks_list = apks_list
        self.total_apks = len(apks_list)
        self.queue = args[0]

    def run(self):
        unique_apis = []

        for apk in self.apks_list:
            try:
                # APK() -> a ; DalvikVMFormat() -> d
                # dx = Analysis(DalvikVMFormat(APK(apk)))
                _, _, dx = AnalyzeAPK(apk)
                apis = get_api_calls(dx)
                not_unique = unique_apis + apis
                unique_apis = list(np.unique(not_unique))
                print('Process %d: %.1f%%' %
                      (self.process_id, ((self.apks_list.index(apk) + 1) / self.total_apks) * 100))
                del dx
                gc.collect()
            except Exception as e:
                print(e)
                print('APK=========>', apk)

        self.queue.put(unique_apis)
        print('----------------> Process %d is done!' % self.process_id)


def main():
    path = 'apks/'
    apks_list = get_files_paths(path)
    np.random.shuffle(apks_list)
    total_apks = len(apks_list)

    # We assume that process_count | total_apks
    process_count = 4
    chunk_size = total_apks // process_count
    chunks = [
        apks_list[k:k + chunk_size]
        for k in range(0, total_apks, chunk_size)]

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


if __name__ == '__main__':
    # single_process_suffering()
    main()


#####################################


# def single_process_suffering():
#     path = 'apks/'
#     unique_apis = []

#     log_file = open('log.txt', 'w')

#     apks_list = get_files_paths(path)
#     total_apks = len(apks_list)

#     for apk in apks_list:
#         try:
#             _, _, dx = AnalyzeAPK(apk)
#             apis = get_api_calls(dx)
#             unique_apis.append(apis)
#             update_progress(apks_list.index(apk), total_apks)
#         except Exception as e:
#             log_file.write(e + '\n')
#             log_file.write(apk + '\n')

#     log_file.close()

#     with open('unique_apis.txt', 'w') as f:
#         f.write('\n'.join(list(set(unique_apis))))
