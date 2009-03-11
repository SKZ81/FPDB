# -*- coding: utf-8 -*-
import EverleafToFpdb
import py


def checkGameInfo(hhc, header, info):
    assert hhc.determineGameType(header) == info

def testGameInfo():
    hhc = EverleafToFpdb.Everleaf(autostart=False)    
    pairs = (
    (u"""Everleaf Gaming Game #3732225
***** Hand history for game #3732225 *****
Blinds  €0.50/ €1 NL Hold'em - 2009/01/11 - 16:09:40
Table Casino Lyon Vert 58
Seat 3 is the button
Total number of players: 6""",
    {'type':'ring', 'base':"hold", 'category':'holdem', 'limitType':'nl', 'sb':'0.50', 'bb':'1', 'currency':'EUR'}),
    
    ("""Everleaf Gaming Game #55198191
***** Hand history for game #55198191 *****
Blinds $0.50/$1 NL Hold'em - 2008/09/01 - 10:02:11
Table Speed Kuala
Seat 8 is the button
Total number of players: 10""",
    {'type':'ring', 'base':"hold", 'category':'holdem', 'limitType':'nl', 'sb':'0.50', 'bb':'1', 'currency':'USD'}),
    
    ("""Everleaf Gaming Game #75065769
***** Hand history for game #75065769 *****
Blinds 10/20 NL Hold'em - 2009/02/25 - 17:30:32
Table 2
Seat 1 is the button
Total number of players: 10""",
    {'type':'ring', 'base':"hold", 'category':'holdem', 'limitType':'nl', 'sb':'10', 'bb':'20', 'currency':'T$'}),
    
    ("""Everleaf Gaming Game #65087798
***** Hand history for game #65087798 *****
$0.25/$0.50 7 Card Stud - 2008/12/05 - 21:46:00
Table Plymouth""",
    {'type':'ring', 'base':'stud', 'category':'studhi', 'limitType':'fl', 'sb':'0.25', 'bb':'0.50', 'currency':'USD'}),
    
    ("""Everleaf Gaming Game #65295370
***** Hand history for game #65295370 *****
Blinds $0.50/$1 PL Omaha - 2008/12/07 - 21:59:48
Table Guanajuato""",
    {'type':'ring', 'base':'hold', 'category':'omahahi', 'limitType':'pl', 'sb':'0.50', 'bb':'1','currency':'USD'})
    
    )
    for (header, info) in pairs:
        yield checkGameInfo, hhc, header, info


