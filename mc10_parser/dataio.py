""" MC10 data load and dump helpers """

from io import StringIO
import numpy as np
import pandas as pd
import pathlib
from pytz import timezone, utc
import timeit


def load(spec, time=False):
    """ Loads and returns Session-formatted data from spec metadata. """
    data = {}
    types = ['accel', 'elec', 'gyro']
    masks = [1, 2, 4]
    # can use any of these timezones
    # https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    tz = timezone(spec['timezone'])

    if time:
        t0 = timeit.default_timer()
    for i, data_folder in enumerate(spec['folders']):
        data[data_folder] = {}
        for j, t in enumerate(types):
            if spec['types'][i] & masks[j]:
                if time:
                    st = timeit.default_timer()
                data[data_folder][t] = pd.read_csv(
                    f"{spec['loc']}{data_folder}/{t}.csv",
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

    return data


def dump(spec, data, time=False):
    """ Dumps Session data to file as specified by spec metadata. """
    if time:
        t0 = timeit.default_timer()
    for i, k1 in enumerate(data.keys()):
        for k2 in data[k1].keys():
            if time:
                st = timeit.default_timer()

            df = data[k1][k2]
            file_loc = spec['loc'] + k1
            old_index = df.index
            df.set_index(df.index.astype(np.int64)//1000, inplace=True)
            pathlib.Path(file_loc).mkdir(parents=True, exist_ok=True)
            df.to_csv(file_loc + f'/{k2}.csv')
            df.set_index(old_index, inplace=True)

            if time:
                print(
                    f"Saved {k1} {k2} in "
                    f"{timeit.default_timer() - st} s"
                )
    if time:
        print(f"Data saved in {timeit.default_timer() - t0} s")


def dump_s3(s3_resource, bucket_name, spec, data, time=False):
    if time:
        t0 = timeit.default_timer()
    for i, k1 in enumerate(data.keys()):
        for k2 in data[k1].keys():
            if time:
                st = timeit.default_timer()

            df = data[k1][k2]
            old_index = df.index
            df.set_index(df.index.astype(np.int64)//1000, inplace=True)
            csv_buffer = StringIO()
            df.to_csv(csv_buffer)
            file_loc = spec['loc'] + k1
            df.set_index(old_index, inplace=True)
            s3_resource.Object(
                bucket_name,
                file_loc
            ).put(Body=csv_buffer.getvalue())

            if time:
                print(
                    f"Saved {k1} {k2} in "
                    f"{timeit.default_timer() - st} s"
                )

    if time:
        print(f"Data saved in {timeit.default_timer() - t0} s")
