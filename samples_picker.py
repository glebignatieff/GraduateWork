import os
import random
import argparse
from shutil import copyfile
from common import *


def main():
    parser = argparse.ArgumentParser(description='Let\'s pick some samples for you.')
    parser.add_argument('<src path>', type=is_dir, help='Directory to pick samples from')
    parser.add_argument('<dst path>', type=is_dir, help='Directory to put samples to')
    parser.add_argument('<nsamples>', type=int, help='Number of samples to pick')
    args = vars(parser.parse_args())

    src_path = args['<src path>']
    dst_path = args['<dst path>']
    samples_num = args['<nsamples>']

    print(src_path, dst_path)

    files = get_files_paths(src_path)
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
