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
from zipfile import ZipFile, BadZipfile
import numpy as np
from androguard.core.bytecodes.dvm import DalvikVMFormat
from common import *


class ApiSequenceExtractorProcess(Process):
    def __init__(self, process_id, unique_apis, apks_list, args):
        super().__init__(target=self)
        self.process_id = process_id
        self.unique_apis = unique_apis
        self.apks_list = apks_list
        self.total_apks = len(apks_list)
        self.queue = args[0]

    # Returns api sequence of a .dex file
    def get_api_sequence(self, d):
        api_sequence = []

        # for every code block in .dex
        for code_block in d.get_codes_item().code:
            # for every instruction in code block
            for ins in code_block.code.get_instructions():
                # we look for invoke-* instructions from 0x6e to 0x78
                opcode = ins.get_op_value()
                if opcode >= 0x6e and opcode <= 0x78:
                    operands = ins.get_operands()
                    # the last operand in the list is the method reference
                    api = operands[-1][-1]
                    if api in self.unique_apis:
                        if len(api_sequence) > 1:
                            # filter to many repetitions
                            if api_sequence[-1] == api and api_sequence[-2] == api:
                                continue
                        api_sequence.append(api)

        return api_sequence

    # override
    def run(self):
        for apk in self.apks_list:
            api_sequence = []
            ret = {'apk': apk, 'apis': []}
            try:
                with ZipFile(apk) as zipfile:
                    # find .dex files inside apk
                    dexes = [dex for dex in zipfile.namelist() if dex.endswith('.dex')]
                    for dex in dexes:
                        # for every dex extract api sequence
                        with zipfile.open(dex) as dexfile:
                            d = DalvikVMFormat(dexfile.read())
                            api_sequence += self.get_api_sequence(d)
                    # send apk's api sequence to the main process
                    ret['apis'] = api_sequence
                    self.queue.put(ret)
                    print('Process %d: %.1f%%' %
                          (self.process_id, ((self.apks_list.index(apk) + 1) / self.total_apks) * 100))
            except BadZipfile as e:
                self.queue.put(ret)
                print('Bad zip file =========> %s' % apk)
            except Exception as e:
                self.queue.put(ret)
                print('\n%s\n%s\n' % (apk, e))

        self.queue.close()
        print('----------------> Process %d is done!' % self.process_id)


def main():
    path = 'apks/'
    api_seq_dir = 'api_sequences'
    apks_list = get_files_paths(path)

    # CRUTCH
    if os.path.isdir(api_seq_dir):
        apks_done = [os.path.basename(apk) for apk in get_files_paths(api_seq_dir)]
        apks_list = [apk for apk in apks_list if apk + '.txt' not in apks_done]

    np.random.shuffle(apks_list)
    total_apks = len(apks_list)
    unique_apis = get_unique_api_set()

    print('%d apks found in total.' % total_apks)

    if not os.path.isdir(api_seq_dir):
        os.makedirs(os.path.join(api_seq_dir, 'benign'))
        os.mkdir(os.path.join(api_seq_dir, 'malware'))
    else:
        benign_path = os.path.join(api_seq_dir, 'benign')
        malware_path = os.path.join(api_seq_dir, 'malware')
        if not os.path.isdir(benign_path):
            os.mkdir(benign_path)
        if not os.path.isdir(malware_path):
            os.mkdir(malware_path)

    # We assume that process_count | total_apks
    process_count = 10
    chunk_size = total_apks // process_count
    chunks = [
        apks_list[k:k + chunk_size]
        for k in range(0, total_apks, chunk_size)]

    queue = Queue()
    processes = [
        ApiSequenceExtractorProcess(i, unique_apis, chunks[i], (queue,)) for i in range(process_count)]

    for process in processes:
        process.start()

    for _ in range(total_apks):
        ret = queue.get()
        if len(ret['apis']) == 0:
            continue
        if 'malware' in ret['apk']:
            dest_dir = os.path.join(api_seq_dir, 'malware')
        else:
            dest_dir = os.path.join(api_seq_dir, 'benign')
        with open(os.path.join(dest_dir, os.path.basename(ret['apk']) + '.txt'), 'w') as f:
            for api in ret['apis']:
                f.write(api + '\n')

    for process in processes:
        process.join()

    print('Done.')


if __name__ == '__main__':
    main()
