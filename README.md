# mc10-parser

## Installation and Setup

### Python and dependencies (Linux)
Feel free to skip ahead to the next section if you have your own method of managing Python/virtualenvs

#### Fedora (Red Hat, etc.)

##### git-lfs
```
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.rpm.sh | sudo bash
sudo yum install -y git-lfs
git lfs install
```

##### pyenv and python 3.7
```
curl https://pyenv.run | bash
```

Then, add the following to your `~/.bashrc`

```
export PATH="/home/ec2-user/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

and run:

```
exec $SHELL
pyenv install 3.7.3 -v
pyenv global 3.7.3
```

##### pyenv-virtualenvwrapper
```
git clone https://github.com/pyenv/pyenv-virtualenvwrapper.git $(pyenv root)/plugins/pyenv-virtualenvwrapper
```

##### Creating a `virtualenv`

```
pyenv virtualenvwrapper
pyenv virtualenv mc10-parser
```

#### Debian (Ubuntu, etc.)

##### pyenv and Python 3.7
```
curl https://pyenv.run | bash
exec $SHELL
pyenv install 3.7.3 -v
pyenv global 3.7.3
```

##### pyenv-virtualenvwrapper
```
git clone https://github.com/pyenv/pyenv-virtualenvwrapper.git $(pyenv root)/plugins/pyenv-virtualenvwrapper
```

##### Creating and activating a `virtualenv`

```
pyenv virtualenvwrapper
pyenv virtualenv mc10-parser
```

### Package and dependencies

First, clone the repository:

```
git clone https://github.com/EpilepsyCo/mc10_parser
cd mc10_parser
git lfs pull
```

Activate your virtualenv and install Python packages:

```
pyenv activate mc10-parser
python -m pip install -r requirements.txt
python -m pip install .
```


## Usage


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
sampling_rates (list of list of floats): Sampling rates for each folder in
    order. Nested list should be ordered with accelerometer first, then
    electrode, then gyroscope sampling rate, omitting any as necessary.
types (list of bitmask ints): Int representation of bitmask describing data
    types for data in each folder. In binary, 001 is accel, 010 is elec,
    and 100 is gyro. Add these masks together for sensors recording multiple
    data types. For example, 011 = 3 corresponds to accel and elec.
timezone (string) : Timezone in which this session was recorded.
---

optional fields
---
meta (string): If applicable, the file containing annotations for this dataset.
ann_names (list of strings): Names of annotations of interest.
labels (list of strings): Abbreviated names of folders for pandas dataframe
    columns.
accel_labels (list of strings): Dimension labels for pandas dataframe column.
time_comp (string, requires labels): Label of the sensor used for doing time
    comparison.
loc (string): Relative (preferred for s3) or absolute path to metadata file.
template_path (string): Relative (preferred) or absolute path to template file.
segments (int): Number of recording segments. Exepects data folders names to be
    suffixed with _0, _1, ... up to segments - 1.
metrics_folder (string): Relative (preferred) or absolute path to metrics
    folder.
---
```
Supported timezones can be found on [this Wikipedia list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) under **TZ database name**.

Here is an example configuration file for three accelerometers collecting data from the thigh, hand, and chest locations with acceleromters at 31.25, 250, and 31.25 Hz, respectively and electrodes at 250 Hz. The thigh and hand have type 1 since they just recorded accelerometer data and the chest has type 3 since it records accelerometer and electrode data.
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
        [31.25],
        [250.0],
        [31.25, 250.0]
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

These metadata files can be broken up into a template file and a metadata file. The template file can be placed anywhere as long as the location is referenced in the metadata file under `template_path`. The metadata file must be placed in the directory containing the data files with filename `metadata.json`. This allows common metadata files to share one template.

Example data has been included in examples/data. There is a template file in `examples/data/test_experiment/template.json` and a metadata file in `examples/data/test_experiment/test_subject/metadata.json`


## Date Shifting

From your virtualenv with dependencies installed, run:

```
python examples/date_shift_test.py \
    -p /path/to/repo/examples/data/test_study/test_subject/metadata.json \
    -o /path/to/repo/examples/data/test_study_test_subject_shifted/metadata.json
```

This will create a test_subject_shifted folder with the date shifted data.

To date shift data stored at `/path/to/data/` and upload it to our S3 bucket, run:

```
python examples/date_shift_s3.py \
    -p /path/to/data/metadata.json \
    --access-key <AWS_ACCESS_KEY> \
    --secret-key <AWS_SECRET_KEY> \
    -b epico-acceldata-upenn
    -o test_study/test_subject_shifted/metadata.json
```

## Direct Transfer

From your virtualenv with dependencies installed, run the following to transfer over an entire study of data, skipping already uploaded subjects:

```
python examples/transfer.py \
    -u $MC10_USERNAME \
    -p $MC10_PASSWORD \
    -s $MC10_STUDY_NAME \
    -b epico-acceldata-upenn \
    --access-key $AWS_ACCESS \
    --secret-key $AWS_SECRET \
    -o $S3_OUTPUT_FOLDER
```
