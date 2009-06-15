#!/usr/bin/python

#Copyright 2008 Ray E. Barker
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in
#agpl-3.0.txt in the docs folder of the package.

import os
import sys
from optparse import OptionParser

def fpdb_options():

    """Process command line options for fpdb and HUD_main."""
    parser = OptionParser()
    parser.add_option("-x", "--errorsToConsole", 
                      action="store_true", 
                      help="If passed error output will go to the console rather than .")
    parser.add_option("-d", "--databaseName", 
                      dest="dbname", default="fpdb",
                      help="Overrides the default database name")
    parser.add_option("-c", "--configFile", 
                      dest="config", default=None,
                      help="Specifies a configuration file.")
    (options, sys.argv) = parser.parse_args()
    return (options, sys.argv)

if __name__== "__main__":
    (options, sys.argv) = fpdb_options()
    print "errorsToConsole =", options.errorsToConsole
    print "database name   =", options.dbname
    print "config file     =", options.config

    print "press enter to end"
    sys.stdin.readline()