import argparse
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

# Create filenames, types, and sampling rates for this study
rec_types = []
rec_sampling_rates = []
rec_file_bases = []
for device in study_response['deviceConfigs']:
    # create filename
    filename = device['physicalConfig']['location']
    filename = filename.lower()
    rec_file_bases.append(filename)

    # create type and sampling rate
    rec_type = 0
    rec_sampling_rate = []
    if 'ACCEL' in device['sensorConfig']['gyro']['mode']:
        rec_type += 1
        rate = 1000. / device['sensorConfig']['gyro']['periodMs']
        rec_sampling_rate.append(rate)
    if device['sensorConfig'].get('afe'):
        rec_type += 2
        rec_sampling_rate.append(device['sensorConfig']['afe']['rate'])
    if 'GYRO' in device['sensorConfig']['gyro']['mode']:
        rec_type += 4
        rate = 1000. / device['sensorConfig']['gyro']['periodMs']
        rec_sampling_rate.append(rate)
    rec_types.append(rec_type)
    rec_sampling_rates.append(rec_sampling_rate)
study_rec_template = OrderedDict(zip(rec_file_bases, list(map(lambda i: {
    'type': rec_types[i],
    'sampling_rate': rec_sampling_rates[i],
    'num': 0
}, range(len(rec_types))))))

# Get activity annotation names
ann_names = [a['displayName'] for a in study_response['activities']]

# Get all subjects for specified study
subjects_response = make_request(
    f"https://mc10cloud.com/api/v1/studies/{study['id']}/subjects",
    headers, auth=auth
)
num_subjects = subjects_response['size']
subjects = subjects_response['items']

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

    # Loop through recordings creating folder names
    rec_filenames = []
    rec_timestamps = []
    rec_types = []
    rec_sampling_rates = []
    for k in study_rec_template.keys():
        study_rec_template[k]['num'] = 0
    for i, rec in enumerate(recs):
        # create filename
        filename_base = rec['physicalConfig']['location'].lower()
        filename = filename_base
        if rec['physicalConfig']['side'] != 'NONE':
            filename = f"{filename_base}_" \
                       f"{rec['physicalConfig']['side']}".lower()
        filename = f"{filename}_" \
                   f"{study_rec_template[filename_base]['num']}"
        study_rec_template[filename_base]['num'] += 1

        rec_filenames.append(filename)
        rec_timestamps.append(rec['recordingStartTs'])
        rec_types.append(study_rec_template[filename_base]['type'])
        rec_sampling_rates.append(
            study_rec_template[filename_base]['sampling_rate']
        )

    # We assume recordings come in ascending, sorted order from MC10
    assert(rec_timestamps == sorted(rec_timestamps))

    # Set metadata segments
    rec_segments = 0
    if len(set(list(map(
        lambda x: study_rec_template[x]['num'],
        study_rec_template.keys()
    )))) == 1:
        rec_segments = \
            study_rec_template[list(study_rec_template)[0]]['num']

    rec_folders = rec_filenames
    if rec_segments != 0:
        # format folders with correct side
        new_rec_folders = []
        for folder in list(study_rec_template):
            filename_idx = 0
            while folder not in rec_filenames[filename_idx]:
                filename_idx += 1
            side = rec_filenames[filename_idx].split('_')[-2]
            if side == 'left' or side == 'right':
                new_rec_folders.append(f"{folder}_{side}")
            else:
                new_rec_folders.append(folder)
        rec_folders = new_rec_folders
        rec_types = [
            study_rec_template[key]['type']
            for key in list(study_rec_template)
        ]
        rec_sampling_rates = [
            study_rec_template[key]['sampling_rate']
            for key in list(study_rec_template)
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

        # TODO make sure error files are copied
        for name in zip_file.namelist():
            if '.csv' in name:
                rec_file[name[:-4]] = BytesIO(
                    zip_file.read(zip_file.namelist()[0])
                )

        rec_files[rec_filenames[i]] = rec_file

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
        'sampling_rates': rec_sampling_rates
    })
    if (rec_segments != 0):
        subject_meta['segments'] = rec_segments

    # pprint.pprint(subject_meta)

    # Load session
    data[subject_identifier] = Session.frommem(subject_meta, subject_data)
    data[subject_identifier].date_shift(shift_date)
    data[subject_identifier].setup_s3(args.access_key, args.secret_key)
    data[subject_identifier].dump_s3(
        args.bucket_name,
        f"{args.outpath}/{study['displayName']}/"
        f"{subject_identifier}/metadata.json",
        time=True
    )

# for ssubject in data
