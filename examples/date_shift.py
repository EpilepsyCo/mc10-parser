import datetime
import numpy as np

from mc10_parser import Session

basepath = '/Users/sabard/dev/cloud/'
metadata_locs = {
    # carolyn tap test 1
    'time_test_1_CW':
        basepath + 'mc10/data/penn_time_align/test_1/CW/metadata.json',

    # van tap test 1
    'time_test_1_VT':
        basepath + 'mc10/data/penn_time_align/test_1/VT/metadata.json',

    'save_path':
        basepath + 'mc10_parser/examples/data/e1/CW/metadata.json'
}

if __name__ == '__main__':
    s1 = Session(metadata_locs['time_test_1_CW'], time=True)
    print(s1.data)
    date = datetime.date(2000, 1, 1)  # Y, M, D format
    s1.date_shift(date)
    s1.dump(metadata_locs['save_path'], time=True)

    s2 = Session(metadata_locs['save_path'])

    # check equality of data loaded in after time shift
    for k1 in s1.data.keys():
        for k2 in s1.data[k1].keys():
            df1 = s1.data[k1][k2]
            df2 = s2.data[k1][k2]
            assert((df1.ge(df2) | np.isclose(df1, df2)).all().all())
