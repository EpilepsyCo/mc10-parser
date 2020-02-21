import argparse

from mc10_parser import Session

# parse in and out paths
parser = argparse.ArgumentParser(
    description='Load in MC10 dataset, date shift and output to S3 bucket.'
)
parser.add_argument('-p', '--inpath', help='Input filepath')
parser.add_argument('-b', '--bucket-name', help='Output bucket name')
parser.add_argument('--access-key', help='AWS Public Access Key')
parser.add_argument('--secret-key', help='AWS Secret Access Key')
args = parser.parse_args()

s1 = Session.froms3(
    args.bucket_name, args.access_key, args.secret_key, args.inpath, time=True
)
