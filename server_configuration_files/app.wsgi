import os, sys

PROJECT_DIR = '/var/www/html/baoe-app'

activate_this = os.path.join(PROJECT_DIR, 'env', 'bin', 'activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

sys.path.append(os.path.join(PROJECT_DIR, 'app'))

from app import app as application