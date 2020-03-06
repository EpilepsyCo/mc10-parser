from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='mc10_parser',
    version='0.0.5',
    license='MIT,',
    description='Data IO and parsing for MC10 BioStamp Sensors',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Sabar Dasgupta',
    author_email='sdasgupta@epilepsyco.com',
    install_requires=[
        'boto3',
        'numpy',
        'pandas',
        'pytz',
        'requests',
        's3fs',
    ],
    packages=['mc10_parser'],
    python_requires='>=3.7.3'
)
