from multiprocessing import Process, Queue
from zipfile import ZipFile, BadZipfile
import numpy as np
from androguard.core.bytecodes.dvm import DalvikVMFormat
from androguard.core.analysis.analysis import Analysis
from common import *


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


class ApiSequenceExtractor(Process):
    def __init__(self, process_id, apks_list, args):
        super().__init__(target=self)
        self.process_id = process_id
        self.apks_list = apks_list
        self.total_apks = len(apks_list)
        self.queue = args[0]

    def run(self):
        # TODO
        pass



def main():
    test_api = 'tmp/apktool/com.android.calculator2_8.1.0-27_minAPI27(nodpi)_apkmirror.com.apk'
    # TODO


if __name__ == '__main__':
    main()