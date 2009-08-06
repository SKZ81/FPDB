#!/usr/bin/python

#Copyright 2008 Steffen Jobbagy-Felso
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
import re
import sys
import logging
from time import time, strftime

import fpdb_simple
import FpdbSQLQueries

class fpdb_db:
    MYSQL_INNODB = 2
    PGSQL = 3
    SQLITE = 4
    def __init__(self):
        """Simple constructor, doesnt really do anything"""
        self.db             = None
        self.cursor         = None
        self.sql            = {}
    #end def __init__

    def do_connect(self, config=None):
        """Connects a database using information in config"""
        if config is None:
            raise FpdbError('Configuration not defined')

        self.settings = {}
        self.settings['os'] = "linuxmac" if os.name != "nt" else "windows"

        db = config.get_db_parameters()
        self.connect(backend=db['db-backend'],
                     host=db['db-host'],
                     database=db['db-databaseName'],
                     user=db['db-user'], 
                     password=db['db-password'])
    #end def do_connect
    
    def connect(self, backend=None, host=None, database=None,
                user=None, password=None):
        """Connects a database with the given parameters"""
        if backend is None:
            raise FpdbError('Database backend not defined')
        self.backend=backend
        self.host=host
        self.user=user
        self.password=password
        self.database=database
        if backend==fpdb_db.MYSQL_INNODB:
            import MySQLdb
            try:
                self.db = MySQLdb.connect(host = host, user = user, passwd = password, db = database, use_unicode=True)
            except:
                raise fpdb_simple.FpdbError("MySQL connection failed")
        elif backend==fpdb_db.PGSQL:
            import psycopg2
            import psycopg2.extensions 
            psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
            # If DB connection is made over TCP, then the variables
            # host, user and password are required
            # For local domain-socket connections, only DB name is
            # needed, and everything else is in fact undefined and/or
            # flat out wrong
            # sqlcoder: This database only connect failed in my windows setup??
            # Modifed it to try the 4 parameter style if the first connect fails - does this work everywhere?
            connected = False
            if self.host == "localhost" or self.host == "127.0.0.1":
                try:
                    self.db = psycopg2.connect(database = database)
                    connected = True
                except:
                    pass
                    #msg = "PostgreSQL direct connection to database (%s) failed, trying with user ..." % (database,)
                    #print msg
                    #raise fpdb_simple.FpdbError(msg)
            if not connected:
                try:
                    self.db = psycopg2.connect(host = host,
                                               user = user, 
                                               password = password, 
                                               database = database)
                except:
                    msg = "PostgreSQL connection to database (%s) user (%s) failed." % (database, user)
                    print msg
                    raise fpdb_simple.FpdbError(msg)
        elif backend==fpdb_db.SQLITE:
            logging.info("Connecting to SQLite:%(database)s" % {'database':database})
            import sqlite3
            self.db = sqlite3.connect(database,detect_types=sqlite3.PARSE_DECLTYPES)
            sqlite3.register_converter("bool", lambda x: bool(int(x)))
            sqlite3.register_adapter(bool, lambda x: "1" if x else "0")

        else:
            raise fpdb_simple.FpdbError("unrecognised database backend:"+backend)
        self.cursor=self.db.cursor()
        # Set up query dictionary as early in the connection process as we can.
        self.sql = FpdbSQLQueries.FpdbSQLQueries(self.get_backend_name())
        self.cursor.execute(self.sql.query['set tx level'])
        self.wrongDbVersion=False
        try:
            self.cursor.execute("SELECT * FROM Settings")
            settings=self.cursor.fetchone()
            if settings[0]!=118:
                print "outdated or too new database version - please recreate tables"
                self.wrongDbVersion=True
        except:# _mysql_exceptions.ProgrammingError:
            print "failed to read settings table - please recreate tables"
            self.wrongDbVersion=True
    #end def connect

    def disconnect(self, due_to_error=False):
        """Disconnects the DB"""
        if due_to_error:
            self.db.rollback()
        else:
            self.db.commit()
        self.cursor.close()
        self.db.close()
    #end def disconnect
    
    def reconnect(self, due_to_error=False):
        """Reconnects the DB"""
        #print "started fpdb_db.reconnect"
        self.disconnect(due_to_error)
        self.connect(self.backend, self.host, self.database, self.user, self.password)
    
    def get_backend_name(self):
        """Returns the name of the currently used backend"""
        if self.backend==2:
            return "MySQL InnoDB"
        elif self.backend==3:
            return "PostgreSQL"
        elif self.backend==4:
            return "SQLite"
        else:
            raise fpdb_simple.FpdbError("invalid backend")
    #end def get_backend_name
    
    def get_db_info(self):
        return (self.host, self.database, self.user, self.password)
    #end def get_db_info

    def getLastInsertId(self, cursor=None):
        try:
            if self.backend == self.MYSQL_INNODB:
                ret = self.db.insert_id()
                if ret < 1 or ret > 999999999:
                    print "getLastInsertId(): problem fetching insert_id? ret=", ret
                    ret = -1
            elif self.backend == self.PGSQL:
                # some options:
                # currval(hands_id_seq) - use name of implicit seq here
                # lastval() - still needs sequences set up?
                # insert ... returning  is useful syntax (but postgres specific?)
                # see rules (fancy trigger type things)
                c = self.db.cursor()
                ret = c.execute ("SELECT lastval()")
                row = c.fetchone()
                if not row:
                    print "getLastInsertId(%s): problem fetching lastval? row=" % seq, row
                    ret = -1
                else:
                    ret = row[0]
            elif self.backend == fpdb_db.SQLITE:
                ret = cursor.lastrowid
            else:
                print "getLastInsertId(): unknown backend ", self.backend
                ret = -1
        except:
            ret = -1
            print "getLastInsertId error:", str(sys.exc_value), " ret =", ret
            raise fpdb_simple.FpdbError( "getLastInsertId error: " + str(sys.exc_value) )

        return ret

    def storeHand(self, p):
        #stores into table hands:
        self.cursor.execute ("""INSERT INTO Hands ( 
            tablename, 
            sitehandno,
            gametypeid, 
            handstart, 
            importtime,
            seats, 
            maxseats,
            boardcard1, 
            boardcard2, 
            boardcard3, 
            boardcard4, 
            boardcard5,
--            texture,
            playersVpi,
            playersAtStreet1, 
            playersAtStreet2,
            playersAtStreet3, 
            playersAtStreet4, 
            playersAtShowdown,
            street0Raises,
            street1Raises,
            street2Raises,
            street3Raises,
            street4Raises,
--            street1Pot,
--            street2Pot,
--            street3Pot,
--            street4Pot,
--            showdownPot
             ) 
             VALUES 
              (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s)""",
            (
                p['tablename'], 
                p['sitehandno'], 
                p['gametypeid'], 
                p['handStart'], 
                datetime.datetime.today(), 
                len(p['names']),
                p['maxSeats'],
                p['boardcard1'], 
                p['boardcard2'], 
                p['boardcard3'], 
                p['boardcard4'], 
                p['boardcard5'],
                hudCache['playersVpi'], 
                hudCache['playersAtStreet1'], 
                hudCache['playersAtStreet2'],
                hudCache['playersAtStreet3'], 
                hudCache['playersAtStreet4'], 
                hudCache['playersAtShowdown'],
                hudCache['street0Raises'], 
                hudCache['street1Raises'], 
                hudCache['street2Raises'],
                hudCache['street3Raises'], 
                hudCache['street4Raises'], 
                hudCache['street1Pot'],
                hudCache['street2Pot'], 
                hudCache['street3Pot'],
                hudCache['street4Pot'],
                hudCache['showdownPot']
            )
        )
        #return getLastInsertId(backend, conn, cursor)
#end class fpdb_db
