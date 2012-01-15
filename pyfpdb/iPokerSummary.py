#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Carl Gherardi
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
#In the "official" distribution you can find the license in agpl-3.0.txt.

import L10n
_ = L10n.get_translation()

from decimal_wrapper import Decimal
import datetime

from Exceptions import FpdbParseError
from HandHistoryConverter import *
from TourneySummary import *


class iPokerSummary(TourneySummary):
    substitutions = {
                     'LS'  : u"\$|\xe2\x82\xac|\xe2\u201a\xac|\u20ac|\xc2\xa3|\£|",
                     'PLYR': r'(?P<PNAME>[a-zA-Z0-9]+)',
                     'NUM' : r'.,0-9',
                    }
    currencies = { u'€':'EUR', '$':'USD', '':'T$', u'£':'GBP' }

    limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl', 'LIMIT':'fl' }
    
    games = {
                    '7 Card Stud L' : ('stud','studhilo'),
                        'Holdem NL' : ('hold','holdem'),
                         'Holdem L' : ('hold','holdem'),
                         'Omaha PL' : ('hold','omahahi'),
            }

    re_GameType = re.compile(r"""
            <gametype>(?P<GAME>7\sCard\sStud\sL|Holdem\sNL|Holdem\sL|Omaha\sPL|Omaha\sL)(\s(%(LS)s)(?P<SB>[.0-9]+)/(%(LS)s)(?P<BB>[.0-9]+))?</gametype>\s+?
            <tablename>(?P<TABLE>.+)?</tablename>\s+?
            <duration>.+</duration>\s+?
            <gamecount>.+</gamecount>\s+?
            <startdate>(?P<DATETIME>.+)</startdate>\s+?
            <currency>(?P<CURRENCY>.+)</currency>\s+?
            <nickname>(?P<HERO>.+)</nickname>
            """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_GameInfoTrny = re.compile(r"""
                <tournamentname>(?P<NAME>.+?)</tournamentname><place>(?P<PLACE>.+?)</place>
                <buyin>(?P<BUYIN>(?P<BIAMT>[%(LS)s\d\.]+)\+?(?P<BIRAKE>[%(LS)s\d\.]+)?|.+?)</buyin>\s+?
                <totalbuyin>(?P<TOTBUYIN>.+)</totalbuyin>\s+?
                <ipoints>([%(NUM)s]+|N/A)</ipoints>\s+?
                <win>(?P<CURRENCY>%(LS)s)?(?P<WIN>([%(NUM)s]+)|N/A)</win>
            """ % substitutions, re.MULTILINE|re.VERBOSE)

    codepage = ["utf-8"]

    @staticmethod
    def getSplitRe(self, head):
        re_SplitTourneys = re.compile("PokerStars Tournament ")
        return re_SplitTourneys


    def parseSummary(self):
        m = self.re_GameType.search(self.summaryText)
        if not m:
            tmp = self.summaryText[0:200]
            log.error(_("iPokerSummary.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        #print "DEBUG: m.groupdict(): %s" % mg

        if 'SB' in mg and mg['SB'] != None:
            tmp = self.summaryText[0:200]
            log.error(_("iPokerSummary.determineGameType: Text does not appear to be a tournament '%s'") % tmp)
            raise FpdbParseError
        else:
            tourney = True
#                self.gametype['limitType'] = 
        if 'GAME' in mg:
            self.gametype['category'] = self.games[mg['GAME']][1]

        if mg['GAME'][-2:] == 'NL':
            self.gametype['limitType'] = 'nl'
        elif mg['GAME'][-2:] == 'PL':
            self.gametype['limitType'] = 'pl'
        else:
            self.gametype['limitType'] = 'fl'

        self.startTime = datetime.datetime.strptime(mg['DATETIME'], '%Y-%m-%d %H:%M:%S')
        self.buyinCurrency = mg['CURRENCY']
        self.currency = self.buyinCurrency

        if tourney:
            m2 = self.re_GameInfoTrny.search(self.summaryText)
            if m2:
                mg2 =  m2.groupdict()
                self.buyin = 0
                self.fee   = 0
                self.prizepool = None
                self.entries   = None
                
                if mg2['BIAMT'] and mg2['BIRAKE']:
                    self.buyin =  int(100*convert_to_decimal(mg2['BIAMT']))
                    self.fee   =  int(100*convert_to_decimal(mg2['BIRAKE']))
                else:
                    self.buyin = 0
                    self.fee   = 0
                if self.buyin == 0:
                    self.buyinCurrency = 'FREE'
                #FIXME: Tournament # looks like it is in the table name
                self.tourNo = mg['TABLE'].split(',')[-1].strip()
                self.tourneyName = mg2['NAME'][:40]

                hero     = mg['HERO']
                winnings = int(100*convert_to_decimal(mg2['WIN']))
                if mg2['CURRENCY']:
                    self.currency = self.currencies[mg2['CURRENCY']]
                rank     = mg2['PLACE']
                if rank == 'N/A':
                    rank = None

                self.addPlayer(rank, hero, winnings, self.currency, 0, 0, 0)
        else:
            tmp = self.summaryText[0:200]
            log.error(_("iPokerSummary.determineGameType: Text does not appear to be a tournament '%s'") % tmp)
            raise FpdbParseError


def convert_to_decimal(string):
    dec = string.strip(u'$£€&euro;\u20ac')
    dec = dec.replace(u',','.')
    dec = dec.replace(u' ','')
    if dec == 'N/A':
        dec = 0
    dec = Decimal(dec)
    return dec

