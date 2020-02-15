import argparse
import datetime
import numpy as np

from mc10_parser import Session

# parse basepath
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--basepath')
args = parser.parse_args()

# add '/' to end of basepath if necessary
basepath = args.basepath
if basepath[-1] != '/':
    basepath += '/'

# data location
metadata_locs = {
    # unshifted test subject
    'test_subject':
        basepath + 'test_study/test_subject/metadata.json',

    # shifted test subject
    'test_subject_shifted':
        basepath + 'test_study/test_subject_shfited/metadata.json',
}

s1 = Session(metadata_locs['test_subject'], time=True)
date = datetime.date(2000, 1, 1)  # Y, M, D format
s1.date_shift(date)
s1.dump(metadata_locs['test_subject_shifted'], time=True)

s2 = Session(metadata_locs['test_subject_shifted'])

# check equality of data loaded in after time shift
for k1 in s1.data.keys():
    for k2 in s1.data[k1].keys():
        df1 = s1.data[k1][k2]
        df2 = s2.data[k1][k2]
        assert((df1.ge(df2) | np.isclose(df1, df2)).all().all())
