# from __future__ import division

import sys
import os
import argparse


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
