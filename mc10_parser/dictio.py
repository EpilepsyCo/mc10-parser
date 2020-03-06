""" Metadata dict load and dump helpers """

import json
import os

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


def data_dict_to_s3(s3_resource, bucket_name, d, filename):
    """Write JSON serializable dict d to filepath on s3_resource """

    s3_resource.Object(
        bucket_name, d['loc'] + filename
    ).put(ACL='bucket-owner-full-control', Body=json.dumps(d))


def dict_from_file(fp):
    """Load JSON serialized dict from filepath fp"""

    with open(fp, 'r') as f:
        return json.load(f)


def data_dict_from_file(filepath):
    """Read JSON serialized dict from filepath, loading values from template if applicable"""
    d = dict_from_file(filepath)

    if d.get('template_path'):
        if d['template_path'][0]== '/':
            tfp = d['template_path']
        else:
            tfp = os.path.normpath(
                os.path.join(os.path.dirname(filepath), d['template_path'])
            )
        td = dict_from_file(tfp)
        d = dict(list(td.items()) + list(d.items()))

    return d


def data_dict_from_s3(s3_resource, bucket_name, filename):
    """Read JSON serializable dict d from filepath on s3_resource """

    response = s3_resource.Object(
        bucket_name, filename
    ).get()
    return json.loads(response['Body'].read())
