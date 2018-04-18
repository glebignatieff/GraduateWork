import os
import random
import argparse
from shutil import copyfile
from common import *


def main():
    parser = argparse.ArgumentParser(description='Let\'s pick some samples for you.')
    parser.add_argument('src_path', type=is_dir, help='Directory to pick samples from')
    parser.add_argument('dst_path', type=is_dir, help='Directory to put samples to')
    parser.add_argument('n_samples', type=int, help='Number of samples to pick')
    parser.add_argument('--min-size', type=int, help='Minimum size of a file in kilobytes')
    parser.add_argument('--max-size', type=int, help='Maximum size of a file in kilobytes')
    args = vars(parser.parse_args())

    src_path = args['src_path']
    dst_path = args['dst_path']
    samples_num = args['n_samples']
    min_size = args['min_size']
    max_size = args['max_size']

    files = get_files_paths(src_path)
    if min_size is not None:
        files = [file for file in files if os.path.getsize(file) >= min_size]
    if max_size is not None:
        files = [file for file in files if os.path.getsize(file) <= max_size]

    if len(files) < samples_num:
        print("Too many samples you want to pick! In total there are {} samples.".format(len(files)))
        return
    elif len(files) == samples_num:
        samples = files
    else:
        samples = random.sample(files, samples_num)

    print('Picking samples...')

    for sample in samples:
        src_sample_path = sample
        dst_sample_path = os.path.join(dst_path, sample.split('\\')[-1])
        copyfile(src_sample_path, dst_sample_path)
        update_progress(samples.index(sample), len(samples))

    print('\nDone!')


if __name__ == '__main__':
    main()
