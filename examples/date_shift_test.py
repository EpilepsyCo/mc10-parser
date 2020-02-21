import argparse
import datetime
import numpy as np

from mc10_parser import Session

# parse in and out paths
parser = argparse.ArgumentParser(
    description='Load in MC10 dataset, date shift and output to file.'
)
parser.add_argument('-p', '--inpath', help='Input filepath.')
parser.add_argument('-o', '--outpath', help='Output filepath.')
parser.add_argument(
    '--verify',
    help='Verify output dataset integrity.',
    action='store_true'
)
args = parser.parse_args()

# Load in input dataset, date shift, and write to output path
s1 = Session(args.inpath, time=True)
date = datetime.date(2000, 1, 1)  # Y, M, D format
s1.date_shift(date)
s1.dump(args.outpath, time=True)

# load in dumped session and verify equality
if args.verify:
    # Load in output dataset
    s2 = Session(args.outpath)

    # check equality of data loaded in after time shift
    for k1 in s1.data.keys():
        for k2 in s1.data[k1].keys():
            df1 = s1.data[k1][k2]
            df2 = s2.data[k1][k2]
            assert((df1.ge(df2) | np.isclose(df1, df2)).all().all())
