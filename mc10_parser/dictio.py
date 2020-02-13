""" Metadata dict load and dump helpers """

import json

"""Metadata dict manipulation functions"""
def dict_to_file(d, fp):
    """Write JSON serializable dict d to filepath fp"""

    with open(fp, 'w') as f:
        json.dump(d, f, sort_keys=False, indent=4)

def data_dict_to_file(d, filepath, template=None, template_path=""):
    """Write JSON serializable dicts d and template to filepath and template_path, respectively"""

    dict_to_file(d, filepath)

    if template:
        dict_to_file(template, template_path)

def dict_from_file(fp):
    """Load JSON serialized dict from filepath fp"""

    with open(fp, 'r') as f:
        return json.load(f)

def data_dict_from_file(filepath):
    """Read JSON serialized dict from filepath, loading values from template if applicable"""
    d = dict_from_file(filepath)

    if d.get('template_path'):
        td = dict_from_file(d['template_path'])
        d = dict(list(td.items()) + list(d.items()))

    return d
