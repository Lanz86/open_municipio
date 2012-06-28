from django.conf import settings

import os

MUNICIPALITY_NAME = 'Senigallia'
# starting year (as a 'YYYY' string) of the municipality's current legislature
MUNICIPALITY_CURRENT_LEGISLATURE = '2010'
# where MDB files are located on the filesystem
MDB_ROOT_DIR = os.path.join(settings.PROJECT_ROOT, 'data_import/municipalities/senigallia/test_data/mdb')
# where SQLite files are located on the filesystem
SQLITE_ROOT_DIR = os.path.join(settings.PROJECT_ROOT, 'data_import/municipalities/senigallia/test_data/sqlite')
# a regexp describing valid filenames for MDB files containing votation-related data
MDB_SITTING_FNAME_PATTERN = r'SeniS(?P<sitting_id>\d{4})\.Mdb'
# name of the MDB file containing data about people taking part to City Council's sittings 
MDB_COMPONENT_FNAME = 'SeniC%(current_legislature)s.Mdb' % {'current_legislature': MUNICIPALITY_CURRENT_LEGISLATURE}
# where XML files are located on the filesystem
XML_ROOT_DIR = os.path.join(settings.PROJECT_ROOT, 'data_import/municipalities/senigallia/test_data/xml')