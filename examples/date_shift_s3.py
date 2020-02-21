import argparse
import datetime

from mc10_parser import Session

# parse in and out paths
parser = argparse.ArgumentParser(
    description='Load in MC10 dataset, date shift and output to S3 bucket.'
)
parser.add_argument('-p', '--inpath', help='Input filepath')
parser.add_argument('-b', '--bucket-name', help='Output bucket name')
parser.add_argument('--access-key', help='AWS Public Access Key')
parser.add_argument('--secret-key', help='AWS Secret Access Key')
parser.add_argument('-o', '--outpath', help='Output filepath')
args = parser.parse_args()

# load session, date shift, and dump it to s3
s1 = Session.fromlocal(args.inpath, time=True)
date = datetime.date(2000, 1, 1)  # Y, M, D format
s1.date_shift(date)
s1.setup_s3(args.access_key, args.secret_key)
s1.dump_s3(args.bucket_name, args.outpath, time=True)
