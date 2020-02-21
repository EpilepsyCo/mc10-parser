""" MC10 data load and dump helpers """

from io import StringIO
import numpy as np
import pandas as pd
import pathlib
from pytz import timezone, utc
from s3fs.core import S3FileSystem
import timeit


def load(spec, s3=None, time=False):
    """ Loads and returns Session-formatted data from spec metadata. """
    data = {}
    types = ['accel', 'elec', 'gyro']
    masks = [1, 2, 4]
    # can use any of these timezones
    # https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    tz = timezone(spec['timezone'])

    if time:
        t0 = timeit.default_timer()

    anns = None
    if spec.get('meta'):
        if s3:
            fs = S3FileSystem(
                anon=False,
                key=s3['creds']['access_key'],
                secret=s3['creds']['secret_key']
            )
            s3_prefix = f"s3://{s3['bucket_name']}/"
            anns = pd.read_csv(
                s3_prefix + spec['loc'] + spec['meta'],
                index_col=0,
            )
        else:
            anns = pd.read_csv(
                spec['loc'] + spec['meta'],
                index_col=0,
            )

    for i, data_folder in enumerate(spec['folders']):
        data[data_folder] = {}
        for j, t in enumerate(types):
            if spec['types'][i] & masks[j]:
                if time:
                    st = timeit.default_timer()
                file_path = f"{spec['loc']}{data_folder}/{t}.csv"
                if s3:
                    data[data_folder][t] = pd.read_csv(
                        s3_prefix + file_path,
                        index_col=0
                    )
                else:
                    data[data_folder][t] = pd.read_csv(
                        file_path,
                        index_col=0,
                    )
                data[data_folder][t].index = pd.to_datetime(
                    data[data_folder][t].index, unit='us'
                )
                data[data_folder][t].index = data[data_folder][t]. \
                    index.tz_localize(utc).tz_convert(tz)

                if time:
                    print(
                        f"Loaded {data_folder} {t} in "
                        f"{timeit.default_timer() - st} s"
                    )
    if time:
        print(f"Data loaded in {timeit.default_timer() - t0} s")

    return data, anns


def load_local(spec, time=False):
    """ Load Session from local filesystem. """
    return load(spec, time=time)


def load_s3(s3_creds, s3_bucket_name, spec, time=False):
    """ Load Session from S3. """
    return load(spec, time=time, s3={
        'creds': s3_creds,
        'bucket_name': s3_bucket_name
    })


def dump(spec, data, anns, s3=None, time=False):
    """ Dumps data to filesystem or S3 as specified by spec metadata. """
    if time:
        t0 = timeit.default_timer()

    for i, k1 in enumerate(data.keys()):
        for k2 in data[k1].keys():
            if time:
                st = timeit.default_timer()

            df = data[k1][k2]
            file_loc = f"{spec['loc']}{k1}/"
            file_name = f'{k2}.csv'
            old_index = df.index
            df.set_index(df.index.astype(np.int64)//1000, inplace=True)

            if s3:
                csv_buffer = StringIO()
                df.to_csv(csv_buffer)
                s3['resource'].Object(
                    s3['bucket_name'],
                    file_loc + file_name
                ).put(Body=csv_buffer.getvalue())
            else:
                pathlib.Path(file_loc).mkdir(parents=True, exist_ok=True)
                df.to_csv(file_loc + file_name)

            df.set_index(old_index, inplace=True)

            if time:
                print(
                    f"Saved {k1} {k2} in "
                    f"{timeit.default_timer() - st} s"
                )

    if anns is not None:
        if s3:
            csv_buffer = StringIO()
            anns.to_csv(csv_buffer)
            s3['resource'].Object(
                s3['bucket_name'],
                spec['loc'] + spec['meta']
            ).put(Body=csv_buffer.getvalue())
        else:
            anns.to_csv(spec['loc'] + spec['meta'])

    if time:
        print(f"Data saved in {timeit.default_timer() - t0} s")


def dump_local(spec, data, anns, time=False):
    """ Dump Session to local filesystem. """
    dump(spec, data, anns, time=time)


def dump_s3(s3_resource, s3_bucket_name, spec, data, anns, time=False):
    """ Dump Session to S3. """
    dump(spec, data, anns, time=time, s3={
        'resource': s3_resource,
        'bucket_name': s3_bucket_name
    })
