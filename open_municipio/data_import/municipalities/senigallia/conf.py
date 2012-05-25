from django.conf import settings

import os

# where MDB files are located on the filesystem
MDB_ROOT_DIR = os.path.join(settings.PROJECT_ROOT, 'data_import/municipalities/senigallia/test_data/mdb')
# where SQLite files are located on the filesystem
SQLITE_ROOT_DIR = os.path.join(settings.PROJECT_ROOT, 'data_import/municipalities/senigallia/test_data/sqlite')
# a regexp describing valid filenames for MDB files containing votation-related data
MDB_FILENAME_PATTERN = r'SeniS(?P<sitting_id>\d{4})\.Mdb'