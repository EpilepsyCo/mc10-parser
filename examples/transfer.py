import argparse
import boto3
from collections import OrderedDict
import datetime
from io import BytesIO
import json
import requests
import zipfile

import pprint # debugging

from mc10_parser import Session

# parse in and out paths
parser = argparse.ArgumentParser(
    description='Download MC10 dataset from MC10 cloud portal.'
)
parser.add_argument('-u', '--username', help='Username')
parser.add_argument('-p', '--password', help='Password')
parser.add_argument('-s', '--study', help='Study to transfer')
parser.add_argument('-b', '--bucket-name', help='Output bucket name')
parser.add_argument('--access-key', help='AWS Public Access Key')
parser.add_argument('--secret-key', help='AWS Secret Access Key')
parser.add_argument('-o', '--outpath', help='Output filepath')

args = parser.parse_args()

# TODO RATE LIMIT TO 10 requests per second
# GET or POST request to specified URL with specified parameters
def make_request(
    url, headers, auth={}, data={}, req_type='get', load_method='json'
):
    req_methods = {
        'get': requests.get,
        'post': requests.post
    }
    load_methods = {
        'json': json.loads,
        'csv': lambda x: x
    }
    return load_methods[load_method](req_methods[req_type](
        url,
        headers=headers,
        auth=auth,
        data=data
    ).text)

# common headers and auth
headers = {'Content-Type': 'text/json'}
auth_data = (
    f'{{"email":"{args.username}",'
    f'"password":"{args.password}",'
    f'"accountType":"BRC2"}}'
)
# get auth token
auth_response = make_request(
    'https://mc10cloud.com/api/v1/users/login/email',
    headers, data=auth_data, req_type='post'
)
auth = (auth_response['user']['id'], auth_response['accessToken'])
account_id = auth_response['user']['accountId']

# Load all studies and find specified study
study_response = make_request(
    f'https://mc10cloud.com/api/v1/accounts/{account_id}/studies',
    headers, auth=auth
)
study = [
    study for study in study_response if study['displayName'] == args.study
][0]
# Load additional data for specified study
study_response = make_request(
    f"https://mc10cloud.com/api/v1/studies/{study['id']}",
    headers, auth=auth
)

# TODO
# device returns sensor types which may have a side of ANY, LEFT, RIGHT, or (MAYBE NONE????)
# recording returns sensor types in which ANY gets assigned to LEFT or RIGHT
# need to fix this shit

# Create filenames, types, and sampling rates for this study
device_configs = []
device_types = []
device_sampling_rates = []
device_folder_bases = []
for device in study_response['deviceConfigs']:
    device_configs.append(device['id'])

    # create filename
    device_filename_base = f"{device['physicalConfig']['location'].lower()}" \
                           f"_{device['physicalConfig']['side']}".lower()

    # create type and sampling rate
    device_type = 0
    device_sampling_rate = []
    if 'ACCEL' in device['sensorConfig']['gyro']['mode']:
        device_type += 1
        rate = 1000. / device['sensorConfig']['gyro']['periodMs']
        device_sampling_rate.append(rate)
    if device['sensorConfig'].get('afe'):
        device_type += 2
        device_sampling_rate.append(device['sensorConfig']['afe']['rate'])
    if 'GYRO' in device['sensorConfig']['gyro']['mode']:
        device_type += 4
        rate = 1000. / device['sensorConfig']['gyro']['periodMs']
        device_sampling_rate.append(rate)
    device_types.append(device_type)
    device_sampling_rates.append(device_sampling_rate)
    device_folder_bases.append(device_filename_base)

device_template = OrderedDict(zip(device_configs, list(map(lambda i: {
    'type': device_types[i],
    'sampling_rate': device_sampling_rates[i],
    'filename_base': device_folder_bases[i],
    'num': 0
}, range(len(device_types))))))

# Get activity annotation names
ann_names = [a['displayName'] for a in study_response['activities']]

# Get all subjects for specified study
subjects_response = make_request(
    f"https://mc10cloud.com/api/v1/studies/{study['id']}/subjects",
    headers, auth=auth
)
num_subjects_total = subjects_response['size']
subjects_total = subjects_response['items']

# copy only uncopied subjects
s3_session = boto3.Session(
    aws_access_key_id=args.access_key,
    aws_secret_access_key=args.secret_key,
)
s3_resource = s3_session.client('s3')
s3_keys = s3_resource.list_objects_v2(Bucket=args.bucket_name)['Contents']
study_path = f"{args.outpath}/{study['displayName']}/"
subjects_seen = list(set([
    k['Key'].split(study_path, 1)[1].split('/')[0]
    for k in s3_keys if study_path in k['Key']
]))
subjects = [s for s in subjects_total if s['displayName'] not in subjects_seen]
num_subjects = len(subjects)

if num_subjects == 0:
    print("All subjects alreday transferred.")
else:
    print(f"There are {num_subjects_total} subjects in total. "
          f"Transferring {num_subjects}.")

# Loop through all subjects, loading an MC10 Session for each
data = {}
shift_date = datetime.date(2000, 1, 1)  # Y, M, D format
for subject in subjects:
    subject_identifier = subject['displayName']

    # Load all recordings for this subject
    recordings_response = make_request(
        f"https://mc10cloud.com/api/v1/studies/{study['id']}/"
        f"subjects/{subject['id']}/recordings",
        headers, auth=auth
    )
    num_recordings = recordings_response['size']
    recs = recordings_response['items']
    if len(recs) == 0:
        continue

    # Loop through recordings creating folder names
    rec_timestamps = []
    rec_types = []
    rec_sampling_rates = []
    rec_filenames = []
    for k in device_template.keys():
        device_template[k]['num'] = 0
    for i, rec in enumerate(recs):
        deviceId = rec['deviceConfigId']

        rec_timestamps.append(rec['recordingStartTs'])
        rec_types.append(device_template[deviceId]['type'])
        rec_sampling_rates.append(
            device_template[deviceId]['sampling_rate']
        )
        rec_filename = device_template[deviceId]['filename_base']
        side = rec['physicalConfig']['side']
        if side in ['LEFT', 'RIGHT']:
            rec_filename = f"{rec_filename}_{side.lower()}"
        rec_filename = f"{rec_filename}_{device_template[deviceId]['num']}"
        rec_filenames.append(rec_filename)
        device_template[deviceId]['num'] += 1

    # We assume recordings come in ascending, sorted order from MC10
    assert(rec_timestamps == sorted(rec_timestamps))

    # Set metadata segments
    rec_segments = 0
    rec_folders = rec_filenames
    # TODO support segments here
    if False and len(set(list(map(
        lambda x: device_template[x]['num'],
        device_template.keys()
    )))) == 1:
        rec_segments = device_template[list(device_template)[0]]['num']

        # format folders with correct side
        rec_folders = [
            device_template[key]['filename_base']
            for key in list(device_template)
        ]
        rec_types = [
            device_template[key]['type']
            for key in list(device_template)
        ]
        rec_sampling_rates = [
            device_template[key]['sampling_rate']
            for key in list(device_template)
        ]

    # Loop through one last time, downloading the data for each recording
    rec_files = OrderedDict()
    for i, rec in enumerate(recs):
        # Get download link
        rec_download_link = make_request(
            f"https://mc10cloud.com/api{rec['export']['href']}",
            headers,
            auth=auth
        )['href']
        # Download and unzip
        zip_file = requests.get(rec_download_link, stream=True)
        zip_file = zipfile.ZipFile(BytesIO(zip_file.content))
        rec_file = {}

        # TODO copy error files as well
        for name in zip_file.namelist():
            if '.csv' in name:
                rec_file[name[:-4]] = BytesIO(
                    zip_file.read(zip_file.namelist()[0])
                )

        rec_files[rec_filenames[i]] = rec_file
        print(f"Loaded {rec_filenames[i]}")

    # Create subject data and metadata
    subject_data = {}
    # Get subject annotations
    subject_data['meta'] = make_request(
        f"https://mc10cloud.com/api/v1/archives/{study['id']}"
        f"/subjects/{subject['id']}/annotations",
        {'Content-Type': 'text/csv'}, auth=auth, load_method='csv'
    )

    # Get subject metrics
    subject_data['metrics'] = make_request(
        f"https://mc10cloud.com/api/v1/studies/{study['id']}/subjects/"
        f"{subject['id']}/pipelines/metrics",
        {'Content-Type':'text/csv'}, auth=auth
    )

    # Get subject channels
    pipeline_id = 'fdd051b8-d753-11e6-ab51-34363bc84032'
    master_id = '4e8a80fd-4778-11e6-a313-34363bc3dbe2'
    start_ts = recs[0]['recordingStartTs']
    end_ts = recs[-1]['recordingStopTs']
    interval = 1000
    subject_data['channels'] = make_request(
        f"https://mc10cloud.com/api/v1/studies/{study['id']}/subjects/"
        f"{subject['id']}/pipelines/{pipeline_id}/channels?masterId="
        f"{master_id}&from={start_ts}&to={end_ts}&interval={interval}",
        {'Content-Type':'text/csv'}, auth=auth
    )
    subject_data['data'] = rec_files

    subject_meta = {}
    subject_meta.update({
        'meta': 'annotations.csv',
        'timezone': subject['timezone'],
        'ann_names': ann_names,
        'folders': rec_folders,
        'types': rec_types,
        'sampling_rates': rec_sampling_rates,
    })
    print(subject_meta)
    if (rec_segments != 0):
        subject_meta['segments'] = rec_segments

    # pprint.pprint(subject_meta)

    # Load session
    data[subject_identifier] = Session.frommem(
        subject_meta, subject_data, time=True
    )
    data[subject_identifier].date_shift(shift_date)
    data[subject_identifier].setup_s3(args.access_key, args.secret_key)
    data[subject_identifier].dump_s3(
        args.bucket_name,
        f"{args.outpath}/{study['displayName']}/"
        f"{subject_identifier}/metadata.json",
        time=True
    )
