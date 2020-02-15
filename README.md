# mc10-parser

## Installation and Setup

### Python and dependencies (Linux)
Feel free to skip ahead to the next section if you have your own method of managing Python/virtualenvs

#### Python 3.7
```
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.7
```

#### pyenv
```
curl https://pyenv.run | bash
exec $SHELL
```

#### pyenv-virtualenvwrapper
```
git clone https://github.com/pyenv/pyenv-virtualenvwrapper.git $(pyenv root)/plugins/pyenv-virtualenvwrapper
```

### Creating a `virtualenv`

```
pyenv virtualenvwrapper
pyenv virtualenv mc10-parser
```

## Usage

### Installing dependencies

From your virtualenv, run:

```
pip install -r requirements.txt

```

### Metadata and Template files
Data must be formatted in a structure as follows:

```
study
│   template.json (optional)
└───subject 1
│   │   metadata.json (required)
│   └───heart
│   │       accel.csv
│   │       elec.csv
│   │
│   └───left-thigh
│           accel.csv
│
└───subject 2
    │   metadata.json (required)
    └───heart
    │       accel.csv
    │       elec.csv
    │
    └───right-thigh
            accel.csv
```

The metadata.json file supports the following fields:

```
required fields
---
folders (list of strings): Folder names in this directory that contain
    MC10 data.
sampling_rates (list of floats): Sampling rate for each folder in order.
types (list of bitmask ints): Int representation of bitmask describing data
    types for data in each folder. In binary, 001 is accel, 010 is elec,
    and 100 is gyro. Add these masks together for sensors recording multiple
    data types. For example, 011 = 3 corresponds to accel and elec.
timezone (string) : Timezone in which this session was recorded.
---

optional fields
---
labels (list of strings): Abbreviated names of folders for pandas dataframe
    columns.
accel_labels (list of strings): Dimension labels for pandas dataframe column.
ann_names (list of strings): Names of annotations of interest.
meta (string): If applicable, the file containing annotations for this dataset
time_comp (string, requires labels): Label of the sensor used for doing time
    comparison.
---
```
Supported timezones can be found on [this Wikipedia list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

Here is an example configuration file for three accelerometers collecting data frorm the thigh, hand, and chest locations at 31.25, 250.0, and 31.25 Hz, respectively. The thigh and hand have type 1 since they just recorded accelerometer data and the chest has type 3 since it records accelerometer and electrode data.
```
{
    "meta": "annotations.csv",
    "ann_names": [
        "Tap test"
    ],
    "folders": [
        "anterior_thigh_right",
        "dorsal_hand_right",
        "ecg_lead_ii"
    ],
    "sampling_rates": [
        31.25,
        250.0,
        31.25
    ],
    "types": [
        1,
        1,
        3
    ],
    "labels": [
        "thigh",
        "arm",
        "heart"
    ],
    "time_comp": "arm",
    "accel_labels": [
        "x",
        "y",
        "z"
    ],
    "timezone": "America/New_York"
}
```

These metadata files can be broken up into a template file and a metadata file. The template file can be placed anywhere as long as the location is referenced in the metadata file under WRITE ABOUT THE TEPMLATE_LOC!!!. The metadatafile must be placed in the directory containing the data files. This allows common metadata files to share one template.

Example data has been included in examples/data. There is a template file in `examples/data/test_experiment/template.json` and a metadata file in `examples/data/test_experiment/test_subject/metadata.json`

## Date Shifting

From your virtualenv with dependencies installed, run:

```
python examples/date_shift.py -p /path/to/repo/examples/data
```

This will create a test_subject_shifted folder with the date shifted data.
