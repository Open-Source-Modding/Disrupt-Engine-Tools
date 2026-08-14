from setuptools import setup, find_packages

# we vantage some helper scripts the twine team wrote to avoid tons of copy/pasta
import fnmatch
import os

# .. note:: the following 2 functions were out-and-out stolen from
# twine.setuptools to avoid a dependency VirtualEnv couldn't solve


def get_version():
    if os.path.exists('version.txt'):
        with open('version.txt', 'r') as v_file:
            return v_file.readline().strip()
    else:
        return "0.0.0"


def find_package_data(path, data_paths, exclusions=None):

    def all_allowed(items):
        return items

    def _allowed(items):
        excluded = []
        for e in exclusions:
            excluded.extend(fnmatch.filter(items, e))
        return set(items) - set(excluded)

    allowed = all_allowed if exclusions is None else _allowed

    package_data = []
    for data_path in data_paths:
        data_path = os.path.join(path, data_path)
        for root, dirs, files in os.walk(data_path):
            if files:
                # Remove the leading sep otherwise it will not work
                # subsequent os.path.join, with leading sep does not work
                # os.path.join('src/barn', '\ui') == '\ui' -> True
                relative_root = root.replace(path, '')[1:]
                package_data.extend(os.path.join(relative_root, f) for f in allowed(files))
            if dirs:
                dirs[:] = allowed(dirs)

    return package_data

setup(
    author="Orwell",
    author_email="ORWELL-Support-Tor@ubisoft.com>",
    name="layer2prefab",
    description="layer2prefab package for a standalone tool",
    version=get_version(),
    dependency_links=[''],
    # Need to use these two lines for pip -e <path> to work properly
    package_dir={'': 'src'},
    packages=find_packages('src'),

    license="Ubisoft internal use",
    long_description=open('README.txt').read(),

    zip_safe=False,

    package_data={'layer2prefab': find_package_data('src/layer2prefab',
                                        [
                                            '.'
                                        ]
                                        )},
    install_requires=[
        "pyside==1.2.2"
    ],
    entry_points = {
        'console_scripts' : [
            # .. todo::  --cfg W:/sourcedata_nexus/animations/_SourceAssets/watchdogs3.json
            "layer2prefab_standalone=layer2prefab.gui:main"
        ]
    }
)
