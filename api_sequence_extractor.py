from multiprocessing import Process, Queue
from zipfile import ZipFile, BadZipfile
import numpy as np
from androguard.core.bytecodes.dvm import DalvikVMFormat
from common import *


def get_unique_api_list():
    ret = []
    with open('unique_apis.txt') as f:
        ret = list(map(str.strip, f.readlines()))
    return ret


class ApiSequenceExtractorProcess(Process):
    def __init__(self, process_id, unique_apis, apks_list, args):
        super().__init__(target=self)
        self.process_id = process_id
        self.unique_apis = unique_apis
        self.apks_list = apks_list
        self.total_apks = len(apks_list)
        self.queue = args[0]

    def get_api_sequence(self, d, api_list):
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
                    if api in api_list:
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
            try:
                with ZipFile(apk) as zipfile:
                    # find .dex files inside apk
                    dexes = [dex for dex in zipfile.namelist() if dex.endswith('.dex')]
                    for dex in dexes:
                        # for every dex extract api sequence
                        with zipfile.open(dex) as dexfile:
                            d = DalvikVMFormat(dexfile.read())
                            api_sequence += self.get_api_sequence(d, self.unique_apis)
                    # send apk's api sequence to the main process
                    ret = {'apk': os.path.basename(apk), 'apis': api_sequence}
                    self.queue.put(ret)
                    print('Process %d: %.1f%%' %
                          (self.process_id, ((self.apks_list.index(apk) + 1) / self.total_apks) * 100))
            except BadZipfile as e:
                print('Bad zip file =========> %s' % apk)
            except Exception as e:
                print('\n%s\n%s\n' % (apk, e))

        print('----------------> Process %d is done!' % self.process_id)


def main():
    path = 'apks/'
    api_seq_dir = 'api_sequences'
    apks_list = get_files_paths(path)
    np.random.shuffle(apks_list)
    total_apks = len(apks_list)
    unique_apis = get_unique_api_list()

    if not os.path.isdir(api_seq_dir):
        os.mkdir(api_seq_dir)

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
        with open(os.path.join(api_seq_dir, ret['apk'] + '.txt'), 'w') as f:
            for api in ret['apis']:
                f.write(api + '\n')

    for process in processes:
        process.join()

    print('Done.')


if __name__ == '__main__':
    main()