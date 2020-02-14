""" MC10 data load and dump helpers """

import multiprocessing as mp
import numpy as np
import os
import pandas as pd
import pathlib
from pytz import timezone, utc
import timeit


def load_folder(ns, job):
    spec, time, (i, j, data_folder, t) = job
    # can use any of these timezones
    # https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    tz = timezone(spec['timezone'])
    if time:
        st = timeit.default_timer()
    ns.data[data_folder][t] = pd.read_csv(
        spec['loc'] + data_folder + f'/{t}.csv',
        index_col=0,
    )
    print(ns.data[data_folder][t].head())
    ns.data[data_folder][t].index = pd.to_datetime(
        ns.data[data_folder][t].index, unit='us'
    )
    print(pd.to_datetime(
        ns.data[data_folder][t].index, unit='us'
    ).head())
    print(ns.data[data_folder][t].head())
    ns.data[data_folder][t].index = ns.data[data_folder][t]. \
        index.tz_localize(utc).tz_convert(tz)
    if time:
        print(
            f"Loaded {data_folder} {t} in "
            f"{timeit.default_timer() - st} s"
        )
    return data_folder, t, ns.data[data_folder][t]


def load(spec, time=False):
    """ Loads and returns Session-formatted data from spec metadata. """
    manager = mp.Manager()
    ns = manager.Namespace()
    ns.data = {}
    masks = [1, 2, 4]
    types = ['accel', 'elec', 'gyro']

    if time:
        t0 = timeit.default_timer()

    jobs = []
    for i, data_folder in enumerate(spec['folders']):
        ns.data[data_folder] = {}
        for j, t in enumerate(types):
            if spec['types'][i] & masks[j]:

                jobs.append((spec, time, (i, j, data_folder, t)))

    processes = []
    for i in range(len(jobs)):
        p = mp.Process(target=load_folder, args=(ns, jobs[i]))
        processes.append(p)

    [x.start() for x in processes]
    for x in processes:
        x.join()

    # print(data)

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
