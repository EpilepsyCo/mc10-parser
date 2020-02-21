""" MC10 data file loading, manipulation, and saving """

import boto3
import os
import pathlib
import re

from .dictio import (
    data_dict_from_file,
    data_dict_to_file,
    data_dict_to_s3,
    data_dict_from_s3
)
from .dataio import (
    load_local as io_load_local,
    load_s3 as io_load_s3,
    dump_local as io_dump_local,
    dump_s3 as io_dump_s3
)


class Session:
    """ Represents MC10 recordings for one patient session  """

    def __init__(self, filepath, s3_dict=None, time=False):
        """ Initialize Session by loading data from filepath. """
        if s3_dict:
            self.setup_s3(s3_dict['access_key'], s3_dict['secret_key'])
            self.metadata, self.data, self.annotations = self.load_s3(
                s3_dict['bucket_name'], filepath, time=time
            )
        else:
            self.s3_session = None
            self.s3_resource = None
            self.metadata, self.data, self.annotations = self.load(
                filepath, time=time
            )

    @classmethod
    def fromlocal(cls, filepath, time=False):
        """ Initialize and load Session from filepath. """
        return cls(filepath, time=time)

    @classmethod
    def froms3(cls, bucket_name, access_key, secret_key, filepath, time=False):
        """ Initialize and load Session from S3 data and path """
        return cls(filepath, time=time, s3_dict={
            'bucket_name': bucket_name,
            'access_key': access_key,
            'secret_key': secret_key
        })

    def setup_s3(self, access_key, secret_key):
        """ Create S3 resource given credentials. """
        self.s3_creds = {
            'access_key': access_key,
            'secret_key': secret_key
        }
        self.s3_session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self.s3_resource = self.s3_session.resource('s3')

    def load(self, filepath, time=False):
        """ Load Session from metadata specified at filepath.

        Parameters:
            filepath (string): Full path to metadata file.

        Keyword Arguments:
            time (bool): set True to print elapsed time.

        Returns:
            dict: Metadata dictionary for the loaded session.
            dict: Session data, with folders as top-level keys and data
                  types as secondary keys.
        """
        assert(isinstance(filepath, str))
        metadata = data_dict_from_file(filepath)
        metadata['loc'] = os.path.dirname(filepath) + '/'
        return (metadata, *io_load_local(metadata, time=time))

    def load_s3(self, bucket_name, filepath, time=False):
        """ Load Session from metadata specified at S3 location.

        Parameters:
            filepath (string): Full path to metadata file.

        Keyword Arguments:
            bucket_name (string): S3 bucket to write to.
            time (bool): set True to print elapsed time.

        Returns:
            dict: Metadata dictionary for the loaded session.
            dict: Session data, with folders as top-level keys and data
                  types as secondary keys.
        """
        assert(isinstance(filepath, str))
        assert(self.s3_session and self.s3_resource)

        metadata = data_dict_from_s3(self.s3_resource, bucket_name, filepath)
        return (metadata, *io_load_s3(
            self.s3_creds, bucket_name, metadata, time=time
        ))

    def dump(self, filepath, time=False):
        """ Dump Session as specified by metadata at filepath.

        Parameters:
            filepath (string): Full path to metadata file.

        Keyword Arguments:
            time (bool): set True to print elapsed time
        """
        assert(isinstance(filepath, str))

        self.metadata['loc'] = filepath.replace(
            re.sub('.*/', '', filepath), ''
        )
        self.metadata.pop('template_path', None)
        pathlib.Path(self.metadata['loc']).mkdir(
            parents=True, exist_ok=True
        )
        data_dict_to_file(self.metadata, filepath)
        self.metadata['loc'] = os.path.dirname(filepath) + '/'
        io_dump_local(self.metadata, self.data, self.annotations, time=time)

    def dump_s3(self, bucket_name, filepath, time=False):
        """ Dump Session as specified by metadata at filepath.

        Parameters:
            bucket_name (string): S3 bucket to write to.
            filepath (string): Full path to metadata file.

        Keyword Arguments:
            time (bool): set True to print elapsed time
        """
        assert(isinstance(filepath, str))
        assert(self.s3_session and self.s3_resource)

        metadata_filename = re.sub('.*/', '', filepath)
        self.metadata['loc'] = filepath.replace(metadata_filename, '')
        self.metadata.pop('template_path', None)
        data_dict_to_s3(
            self.s3_resource,
            bucket_name,
            self.metadata,
            metadata_filename
        )
        io_dump_s3(
            self.s3_resource,
            bucket_name,
            self.metadata,
            self.data,
            self.annotations,
            time=time
        )

    def date_shift(self, target_date):
        """ Shift all dataframe indexes to start at target_date

        Parameters:
            target_date (datetime.date): Date to shift data start to.
        """

        # assert this Session is populated
        if not self.data:
            raise Exception("Session must have data.")

        # loop through all dataframes (accel, elec, and gyro)
        for k1 in self.data.keys():
            for k2 in self.data[k1].keys():
                df = self.data[k1][k2]

                # compute time difference in days and shift each df
                start_date = df.index[0].date()
                dt_days = (target_date - start_date).days
                df.index = df.index.shift(dt_days, freq='D')
