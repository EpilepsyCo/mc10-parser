# mc10-parser

## Installation and Setup

### python and dependencies (Linux)
Feel free to skip ahead if you have your own method of managing Python/virtualenvs

#### python
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

## Formatting Data

### Metadata and Tempalte files
An example template file has been included in `examples/data/test_experiment/template.json`
An example metadata file has been included in `examples/data/test_experiment/test_subject/metadata.json`
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

## mc10_parser package


## Date Shifting
