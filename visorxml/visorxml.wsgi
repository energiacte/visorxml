activate_this = '/home/pachi/.virtualenvs/visorxml/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, '/var/www/visorxml')

from visorxml import app as application
