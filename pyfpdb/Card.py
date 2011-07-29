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

import sys
import L10n
_ = L10n.get_translation()

card_map = { "0": 0, "2": 2, "3" : 3, "4" : 4, "5" : 5, "6" : 6, "7" : 7, "8" : 8,
            "9" : 9, "T" : 10, "J" : 11, "Q" : 12, "K" : 13, "A" : 14, "n": 0}

card_map_low = { "0": 0, "A":1, "2": 2, "3" : 3, "4" : 4, "5" : 5, "6" : 6, "7" : 7, "8" : 8,
            "9" : 9, "T" : 10, "J" : 11, "Q" : 12, "K" : 13, "n": 0}

games = {              # base, category
             'holdem' : ('hold','holdem', 'h'), 
            'omahahi' : ('hold','omaha','h'), 
          'omahahilo' : ('hold','omaha8', 's'),
               'razz' : ('stud','razz', 'l'), 
             'studhi' : ('stud','7stud', 'h'), 
           'studhilo' : ('stud','7stud8', 's'),
           '27_3draw' : ('draw','lowball27', 'r'),
           'fivedraw' : ('draw','5draw', 'h'),
             'badugi' : ('draw','lowball27', 'l'),
           '27_1draw' : ('draw','lowball27', 'r')
       }

hands = {'hi':{
            'NoPair'  : 'high card, %s',
            'OnePair' : 'a pair of %s',
            'TwoPair' : 'two pair, %s',
            'Trips'   : 'three of a kind, %s',
            'Straight': 'a straight, %s',
            'Flush'   : 'a flush, %s',
            'FlHouse' : 'a full house, %s',
            'Quads'   : 'four of a kind, %s',
            'StFlush' : 'a straight flush, %s'
            },
         'lo':{
            'Nothing' : '%s',
            'NoPair'  : '%s',
            'OnePair' : 'a pair of %s',
            'TwoPair' : 'two pair, %s',
            'Trips'   : 'three of a kind, %s',
            'FlHouse' : 'a full house, %s',
            'Quads'   : 'four of a kind, %s',
            }
         }

names = {
            'A' : ('Ace', 'Aces', 14),
            'K' : ('King', 'Kings', 13),
            'Q' : ('Queen', 'Queens', 12),
            'J' : ('Jack', 'Jacks', 11),
            'T' : ('Ten', 'Tens', 10),
            '9' : ('Nine', 'Nines', 9),
            '8' : ('Eight', 'Eights', 8),
            '7' : ('Seven', 'Sevens', 7),
            '6' : ('Six', 'Sixes', 6),
            '5' : ('Five', 'Fives', 5),
            '4' : ('Four', 'Fours', 4),
            '3' : ('Three', 'Threes', 3),
            '2' : ('Two', 'Twos', 2)
            }

streets = {'stud': {'THIRD': 0,'FOURTH': 1,'FIFTH': 2,'SIXTH': 3,'SEVENTH': 4},
           'hold': {'PREFLOP':0,'FLOP':1,'TURN':2,'RIVER':3},
           'draw': {'DEAL':0, 'DRAWONE':1, 'DRAWTWO':2, 'DRAWTHREE':3}
          }

iter = {0: 100000,
        1: 0,
        2: 0,
        3: 0
        }

def decodeStartHandValue(game, value):
    if game == "holdem":
        return twoStartCardString(value)
    elif game == "razz":
        return decodeRazzStartHand(value)
    else:
        return "xx"


# FIXME: the following is a workaround until switching to newimport.
#        This should be moved into DerivedStats
#        I'd also like to change HandsPlayers.startCards to a different datatype
#        so we can 'trivially' add different start card classifications

def calcStartCards(hand, player):
    hcs = hand.join_holecards(player, asList=True)
    if hand.gametype['category'] == 'holdem':
        value1 = card_map[hcs[0][0]]
        value2 = card_map[hcs[1][0]]
        return twoStartCards(value1, hcs[0][1], value2, hcs[1][1])
    elif hand.gametype['category'] == 'razz':
        return encodeRazzStartHand(hcs)
    else:
        # FIXME: Only do startCards value for holdem at the moment
        return 0


# The following depends on the exact implementation of twoStartCards.
_firstcard = '((hp.startcards - 1) /  13)'
_secondcard = '((hp.startcards - 1) - 13 * %s)' % _firstcard
_gap = '(%s - %s = %d)'

DATABASE_FILTERS = {
    'pair': '%s = %s' % (_firstcard, _secondcard),
    'suited': '%s > %s' % (_firstcard, _secondcard),
    'offsuit': '%s < %s' % (_firstcard, _secondcard),
    'suited_connectors': _gap % (_firstcard, _secondcard, 1),
    'offsuit_connectors': _gap % (_secondcard, _firstcard, 1)
}

def twoStartCards(value1, suit1, value2, suit2):
    """ Function to convert 2 value,suit pairs into a Holdem style starting hand e.g. AQo
        Incoming values should be ints 2-14 (2,3,...K,A), suits are 'd'/'h'/'c'/'s'
        Hand is stored as an int 13 * x + y + 1 where (x+2) represents rank of 1st card and
        (y+2) represents rank of second card (2=2 .. 14=Ace)
        If x > y then pair is suited, if x < y then unsuited
        Examples:
           0  Unknown / Illegal cards
           1  22
           2  32o
           3  42o
              ...
          14  32s
          15  33
          16  42o
              ...
         170  AA
    """
    if value1 is None or value1 < 2 or value1 > 14 or value2 is None or value2 < 2 or value2 > 14:
        ret = 0
    elif value1 == value2: # pairs
        ret = (13 * (value2-2) + (value2-2) ) + 1
    elif suit1 == suit2:
        if value1 > value2:
            ret = 13 * (value1-2) + (value2-2) + 1
        else:
            ret = 13 * (value2-2) + (value1-2) + 1
    else:
        if value1 > value2:
            ret = 13 * (value2-2) + (value1-2) + 1
        else:
            ret = 13 * (value1-2) + (value2-2) + 1

#    print "twoStartCards(", value1, suit1, value2, suit2, ")=", ret
    return ret

def twoStartCardString(card):
    """ Function to convert an int representing 2 holdem hole cards (as created by twoStartCards)
        into a string like AQo """
    ret = 'xx'
    if card > 0:
        s = ('2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A')
        x = (card-1) / 13
        y = (card-1) - 13 * x
        if x == y:  ret = s[x] + s[y]
        elif x > y: ret = s[x] + s[y] + 's'
        else:       ret = s[y] + s[x] + 'o'
    #print "twoStartCardString(", card ,") = " + ret
    return ret

def cardFromValueSuit(value, suit):
    """ 0=none, 1-13=2-Ah 14-26=2-Ad 27-39=2-Ac 40-52=2-As """
    if suit == 'h':  return(value-1)
    elif suit == 'd':  return(value+12)
    elif suit == 'c':  return(value+25)
    elif suit == 's':  return(value+38)
    else: return(0)

suitFromCardList = ['', '2h', '3h', '4h', '5h', '6h', '7h', '8h', '9h', 'Th', 'Jh', 'Qh', 'Kh', 'Ah'
                     , '2d', '3d', '4d', '5d', '6d', '7d', '8d', '9d', 'Td', 'Jd', 'Qd', 'Kd', 'Ad'
                     , '2c', '3c', '4c', '5c', '6c', '7c', '8c', '9c', 'Tc', 'Jc', 'Qc', 'Kc', 'Ac'
                     , '2s', '3s', '4s', '5s', '6s', '7s', '8s', '9s', 'Ts', 'Js', 'Qs', 'Ks', 'As'
                ]
def valueSuitFromCard(card):
    """ Function to convert a card stored in the database (int 0-52) into value
        and suit like 9s, 4c etc """
    global suitFromCardList
    if card < 0 or card > 52 or not card:
        return('')
    else:
        return suitFromCardList[card]

encodeCardList = {'2h':  1, '3h':  2, '4h':  3, '5h':  4, '6h':  5, '7h':  6, '8h':  7, '9h':  8, 'Th':  9, 'Jh': 10, 'Qh': 11, 'Kh': 12, 'Ah': 13,
                  '2d': 14, '3d': 15, '4d': 16, '5d': 17, '6d': 18, '7d': 19, '8d': 20, '9d': 21, 'Td': 22, 'Jd': 23, 'Qd': 24, 'Kd': 25, 'Ad': 26,
                  '2c': 27, '3c': 28, '4c': 29, '5c': 30, '6c': 31, '7c': 32, '8c': 33, '9c': 34, 'Tc': 35, 'Jc': 36, 'Qc': 37, 'Kc': 38, 'Ac': 39,
                  '2s': 40, '3s': 41, '4s': 42, '5s': 43, '6s': 44, '7s': 45, '8s': 46, '9s': 47, 'Ts': 48, 'Js': 49, 'Qs': 50, 'Ks': 51, 'As': 52,
                  '  ':  0
                }

def encodeCard(cardString):
    """Take a card string (Ah) and convert it to the db card code (1)."""
    global encodeCardList
    if cardString not in encodeCardList: return 0
    return encodeCardList[cardString]

def decodeRazzStartHand(idx):
    decodeRazzList = {
    -13:'(00)A',-12:'(00)2',-11:'(00)3',-10:'(00)4',-9:'(00)5',-8:'(00)6',-7:'(00)7',-6:'(00)8',-5:'(00)9',-4:'(00)T',
    -3:'(00)J',-2:'(00)Q',-1:'(00)K',0:'xxx',
    1:'(32)A',2:'(3A)2',3:'(2A)3',4:'(42)A',5:'(4A)2',6:'(2A)4',7:'(43)A',8:'(4A)3',9:'(3A)4',
    10:'(43)2',11:'(42)3',12:'(32)4',13:'(52)A',14:'(5A)2',15:'(2A)5',16:'(53)A',17:'(5A)3',18:'(3A)5',19:'(53)2',
    20:'(52)3',21:'(32)5',22:'(54)A',23:'(5A)4',24:'(4A)5',25:'(54)2',26:'(52)4',27:'(42)5',28:'(54)3',29:'(53)4',
    30:'(43)5',31:'(62)A',32:'(6A)2',33:'(2A)6',34:'(63)A',35:'(6A)3',36:'(3A)6',37:'(63)2',38:'(62)3',39:'(32)6',
    40:'(64)A',41:'(6A)4',42:'(4A)6',43:'(64)2',44:'(62)4',45:'(42)6',46:'(64)3',47:'(63)4',48:'(43)6',49:'(65)A',
    50:'(6A)5',51:'(5A)6',52:'(65)2',53:'(62)5',54:'(52)6',55:'(65)3',56:'(63)5',57:'(53)6',58:'(65)4',59:'(64)5',
    60:'(54)6',61:'(72)A',62:'(7A)2',63:'(2A)7',64:'(73)A',65:'(7A)3',66:'(3A)7',67:'(73)2',68:'(72)3',69:'(32)7',
    70:'(74)A',71:'(7A)4',72:'(4A)7',73:'(74)2',74:'(72)4',75:'(42)7',76:'(74)3',77:'(73)4',78:'(43)7',79:'(75)A',
    80:'(7A)5',81:'(5A)7',82:'(75)2',83:'(72)5',84:'(52)7',85:'(75)3',86:'(73)5',87:'(53)7',88:'(75)4',89:'(74)5',
    90:'(54)7',91:'(76)A',92:'(7A)6',93:'(6A)7',94:'(76)2',95:'(72)6',96:'(62)7',97:'(76)3',98:'(73)6',99:'(63)7',
    100:'(76)4',101:'(74)6',102:'(64)7',103:'(76)5',104:'(75)6',105:'(65)7',106:'(82)A',107:'(8A)2',108:'(2A)8',109:'(83)A',
    110:'(8A)3',111:'(3A)8',112:'(83)2',113:'(82)3',114:'(32)8',115:'(84)A',116:'(8A)4',117:'(4A)8',118:'(84)2',119:'(82)4',
    120:'(42)8',121:'(84)3',122:'(83)4',123:'(43)8',124:'(85)A',125:'(8A)5',126:'(5A)8',127:'(85)2',128:'(82)5',129:'(52)8',
    130:'(85)3',131:'(83)5',132:'(53)8',133:'(85)4',134:'(84)5',135:'(54)8',136:'(86)A',137:'(8A)6',138:'(6A)8',139:'(86)2',
    140:'(82)6',141:'(62)8',142:'(86)3',143:'(83)6',144:'(63)8',145:'(86)4',146:'(84)6',147:'(64)8',148:'(86)5',149:'(85)6',
    150:'(65)8',151:'(87)A',152:'(8A)7',153:'(7A)8',154:'(87)2',155:'(82)7',156:'(72)8',157:'(87)3',158:'(83)7',159:'(73)8',
    160:'(87)4',161:'(84)7',162:'(74)8',163:'(87)5',164:'(85)7',165:'(75)8',166:'(87)6',167:'(86)7',168:'(76)8',169:'(92)A',
    170:'(9A)2',171:'(2A)9',172:'(93)A',173:'(9A)3',174:'(3A)9',175:'(93)2',176:'(92)3',177:'(32)9',178:'(94)A',179:'(9A)4',
    180:'(4A)9',181:'(94)2',182:'(92)4',183:'(42)9',184:'(94)3',185:'(93)4',186:'(43)9',187:'(95)A',188:'(9A)5',189:'(5A)9',
    190:'(95)2',191:'(92)5',192:'(52)9',193:'(95)3',194:'(93)5',195:'(53)9',196:'(95)4',197:'(94)5',198:'(54)9',199:'(96)A',
    200:'(9A)6',201:'(6A)9',202:'(96)2',203:'(92)6',204:'(62)9',205:'(96)3',206:'(93)6',207:'(63)9',208:'(96)4',209:'(94)6',
    210:'(64)9',211:'(96)5',212:'(95)6',213:'(65)9',214:'(97)A',215:'(9A)7',216:'(7A)9',217:'(97)2',218:'(92)7',219:'(72)9',
    220:'(97)3',221:'(93)7',222:'(73)9',223:'(97)4',224:'(94)7',225:'(74)9',226:'(97)5',227:'(95)7',228:'(75)9',229:'(97)6',
    230:'(96)7',231:'(76)9',232:'(98)A',233:'(9A)8',234:'(8A)9',235:'(98)2',236:'(92)8',237:'(82)9',238:'(98)3',239:'(93)8',
    240:'(83)9',241:'(98)4',242:'(94)8',243:'(84)9',244:'(98)5',245:'(95)8',246:'(85)9',247:'(98)6',248:'(96)8',249:'(86)9',
    250:'(98)7',251:'(97)8',252:'(87)9',253:'(T2)A',254:'(TA)2',255:'(2A)T',256:'(T3)A',257:'(TA)3',258:'(3A)T',259:'(T3)2',
    260:'(T2)3',261:'(32)T',262:'(T4)A',263:'(TA)4',264:'(4A)T',265:'(T4)2',266:'(T2)4',267:'(42)T',268:'(T4)3',269:'(T3)4',
    270:'(43)T',271:'(T5)A',272:'(TA)5',273:'(5A)T',274:'(T5)2',275:'(T2)5',276:'(52)T',277:'(T5)3',278:'(T3)5',279:'(53)T',
    280:'(T5)4',281:'(T4)5',282:'(54)T',283:'(T6)A',284:'(TA)6',285:'(6A)T',286:'(T6)2',287:'(T2)6',288:'(62)T',289:'(T6)3',
    290:'(T3)6',291:'(63)T',292:'(T6)4',293:'(T4)6',294:'(64)T',295:'(T6)5',296:'(T5)6',297:'(65)T',298:'(T7)A',299:'(TA)7',
    300:'(7A)T',301:'(T7)2',302:'(T2)7',303:'(72)T',304:'(T7)3',305:'(T3)7',306:'(73)T',307:'(T7)4',308:'(T4)7',309:'(74)T',
    310:'(T7)5',311:'(T5)7',312:'(75)T',313:'(T7)6',314:'(T6)7',315:'(76)T',316:'(T8)A',317:'(TA)8',318:'(8A)T',319:'(T8)2',
    320:'(T2)8',321:'(82)T',322:'(T8)3',323:'(T3)8',324:'(83)T',325:'(T8)4',326:'(T4)8',327:'(84)T',328:'(T8)5',329:'(T5)8',
    330:'(85)T',331:'(T8)6',332:'(T6)8',333:'(86)T',334:'(T8)7',335:'(T7)8',336:'(87)T',337:'(T9)A',338:'(TA)9',339:'(9A)T',
    340:'(T9)2',341:'(T2)9',342:'(92)T',343:'(T9)3',344:'(T3)9',345:'(93)T',346:'(T9)4',347:'(T4)9',348:'(94)T',349:'(T9)5',
    350:'(T5)9',351:'(95)T',352:'(T9)6',353:'(T6)9',354:'(96)T',355:'(T9)7',356:'(T7)9',357:'(97)T',358:'(T9)8',359:'(T8)9',
    360:'(98)T',361:'(J2)A',362:'(JA)2',363:'(2A)J',364:'(J3)A',365:'(JA)3',366:'(3A)J',367:'(J3)2',368:'(J2)3',369:'(32)J',
    370:'(J4)A',371:'(JA)4',372:'(4A)J',373:'(J4)2',374:'(J2)4',375:'(42)J',376:'(J4)3',377:'(J3)4',378:'(43)J',379:'(J5)A',
    380:'(JA)5',381:'(5A)J',382:'(J5)2',383:'(J2)5',384:'(52)J',385:'(J5)3',386:'(J3)5',387:'(53)J',388:'(J5)4',389:'(J4)5',
    390:'(54)J',391:'(J6)A',392:'(JA)6',393:'(6A)J',394:'(J6)2',395:'(J2)6',396:'(62)J',397:'(J6)3',398:'(J3)6',399:'(63)J',
    400:'(J6)4',401:'(J4)6',402:'(64)J',403:'(J6)5',404:'(J5)6',405:'(65)J',406:'(J7)A',407:'(JA)7',408:'(7A)J',409:'(J7)2',
    410:'(J2)7',411:'(72)J',412:'(J7)3',413:'(J3)7',414:'(73)J',415:'(J7)4',416:'(J4)7',417:'(74)J',418:'(J7)5',419:'(J5)7',
    420:'(75)J',421:'(J7)6',422:'(J6)7',423:'(76)J',424:'(J8)A',425:'(JA)8',426:'(8A)J',427:'(J8)2',428:'(J2)8',429:'(82)J',
    430:'(J8)3',431:'(J3)8',432:'(83)J',433:'(J8)4',434:'(J4)8',435:'(84)J',436:'(J8)5',437:'(J5)8',438:'(85)J',439:'(J8)6',
    440:'(J6)8',441:'(86)J',442:'(J8)7',443:'(J7)8',444:'(87)J',445:'(J9)A',446:'(JA)9',447:'(9A)J',448:'(J9)2',449:'(J2)9',
    450:'(92)J',451:'(J9)3',452:'(J3)9',453:'(93)J',454:'(J9)4',455:'(J4)9',456:'(94)J',457:'(J9)5',458:'(J5)9',459:'(95)J',
    460:'(J9)6',461:'(J6)9',462:'(96)J',463:'(J9)7',464:'(J7)9',465:'(97)J',466:'(J9)8',467:'(J8)9',468:'(98)J',469:'(JT)A',
    470:'(JA)T',471:'(TA)J',472:'(JT)2',473:'(J2)T',474:'(T2)J',475:'(JT)3',476:'(J3)T',477:'(T3)J',478:'(JT)4',479:'(J4)T',
    480:'(T4)J',481:'(JT)5',482:'(J5)T',483:'(T5)J',484:'(JT)6',485:'(J6)T',486:'(T6)J',487:'(JT)7',488:'(J7)T',489:'(T7)J',
    490:'(JT)8',491:'(J8)T',492:'(T8)J',493:'(JT)9',494:'(J9)T',495:'(T9)J',496:'(Q2)A',497:'(QA)2',498:'(2A)Q',499:'(Q3)A',
    500:'(QA)3',501:'(3A)Q',502:'(Q3)2',503:'(Q2)3',504:'(32)Q',505:'(Q4)A',506:'(QA)4',507:'(4A)Q',508:'(Q4)2',509:'(Q2)4',
    510:'(42)Q',511:'(Q4)3',512:'(Q3)4',513:'(43)Q',514:'(Q5)A',515:'(QA)5',516:'(5A)Q',517:'(Q5)2',518:'(Q2)5',519:'(52)Q',
    520:'(Q5)3',521:'(Q3)5',522:'(53)Q',523:'(Q5)4',524:'(Q4)5',525:'(54)Q',526:'(Q6)A',527:'(QA)6',528:'(6A)Q',529:'(Q6)2',
    530:'(Q2)6',531:'(62)Q',532:'(Q6)3',533:'(Q3)6',534:'(63)Q',535:'(Q6)4',536:'(Q4)6',537:'(64)Q',538:'(Q6)5',539:'(Q5)6',
    540:'(65)Q',541:'(Q7)A',542:'(QA)7',543:'(7A)Q',544:'(Q7)2',545:'(Q2)7',546:'(72)Q',547:'(Q7)3',548:'(Q3)7',549:'(73)Q',
    550:'(Q7)4',551:'(Q4)7',552:'(74)Q',553:'(Q7)5',554:'(Q5)7',555:'(75)Q',556:'(Q7)6',557:'(Q6)7',558:'(76)Q',559:'(Q8)A',
    560:'(QA)8',561:'(8A)Q',562:'(Q8)2',563:'(Q2)8',564:'(82)Q',565:'(Q8)3',566:'(Q3)8',567:'(83)Q',568:'(Q8)4',569:'(Q4)8',
    570:'(84)Q',571:'(Q8)5',572:'(Q5)8',573:'(85)Q',574:'(Q8)6',575:'(Q6)8',576:'(86)Q',577:'(Q8)7',578:'(Q7)8',579:'(87)Q',
    580:'(Q9)A',581:'(QA)9',582:'(9A)Q',583:'(Q9)2',584:'(Q2)9',585:'(92)Q',586:'(Q9)3',587:'(Q3)9',588:'(93)Q',589:'(Q9)4',
    590:'(Q4)9',591:'(94)Q',592:'(Q9)5',593:'(Q5)9',594:'(95)Q',595:'(Q9)6',596:'(Q6)9',597:'(96)Q',598:'(Q9)7',599:'(Q7)9',
    600:'(97)Q',601:'(Q9)8',602:'(Q8)9',603:'(98)Q',604:'(QT)A',605:'(QA)T',606:'(TA)Q',607:'(QT)2',608:'(Q2)T',609:'(T2)Q',
    610:'(QT)3',611:'(Q3)T',612:'(T3)Q',613:'(QT)4',614:'(Q4)T',615:'(T4)Q',616:'(QT)5',617:'(Q5)T',618:'(T5)Q',619:'(QT)6',
    620:'(Q6)T',621:'(T6)Q',622:'(QT)7',623:'(Q7)T',624:'(T7)Q',625:'(QT)8',626:'(Q8)T',627:'(T8)Q',628:'(QT)9',629:'(Q9)T',
    630:'(T9)Q',631:'(QJ)A',632:'(QA)J',633:'(JA)Q',634:'(QJ)2',635:'(Q2)J',636:'(J2)Q',637:'(QJ)3',638:'(Q3)J',639:'(J3)Q',
    640:'(QJ)4',641:'(Q4)J',642:'(J4)Q',643:'(QJ)5',644:'(Q5)J',645:'(J5)Q',646:'(QJ)6',647:'(Q6)J',648:'(J6)Q',649:'(QJ)7',
    650:'(Q7)J',651:'(J7)Q',652:'(QJ)8',653:'(Q8)J',654:'(J8)Q',655:'(QJ)9',656:'(Q9)J',657:'(J9)Q',658:'(QJ)T',659:'(QT)J',
    660:'(JT)Q',661:'(K2)A',662:'(KA)2',663:'(2A)K',664:'(K3)A',665:'(KA)3',666:'(3A)K',667:'(K3)2',668:'(K2)3',669:'(32)K',
    670:'(K4)A',671:'(KA)4',672:'(4A)K',673:'(K4)2',674:'(K2)4',675:'(42)K',676:'(K4)3',677:'(K3)4',678:'(43)K',679:'(K5)A',
    680:'(KA)5',681:'(5A)K',682:'(K5)2',683:'(K2)5',684:'(52)K',685:'(K5)3',686:'(K3)5',687:'(53)K',688:'(K5)4',689:'(K4)5',
    690:'(54)K',691:'(K6)A',692:'(KA)6',693:'(6A)K',694:'(K6)2',695:'(K2)6',696:'(62)K',697:'(K6)3',698:'(K3)6',699:'(63)K',
    700:'(K6)4',701:'(K4)6',702:'(64)K',703:'(K6)5',704:'(K5)6',705:'(65)K',706:'(K7)A',707:'(KA)7',708:'(7A)K',709:'(K7)2',
    710:'(K2)7',711:'(72)K',712:'(K7)3',713:'(K3)7',714:'(73)K',715:'(K7)4',716:'(K4)7',717:'(74)K',718:'(K7)5',719:'(K5)7',
    720:'(75)K',721:'(K7)6',722:'(K6)7',723:'(76)K',724:'(K8)A',725:'(KA)8',726:'(8A)K',727:'(K8)2',728:'(K2)8',729:'(82)K',
    730:'(K8)3',731:'(K3)8',732:'(83)K',733:'(K8)4',734:'(K4)8',735:'(84)K',736:'(K8)5',737:'(K5)8',738:'(85)K',739:'(K8)6',
    740:'(K6)8',741:'(86)K',742:'(K8)7',743:'(K7)8',744:'(87)K',745:'(K9)A',746:'(KA)9',747:'(9A)K',748:'(K9)2',749:'(K2)9',
    750:'(92)K',751:'(K9)3',752:'(K3)9',753:'(93)K',754:'(K9)4',755:'(K4)9',756:'(94)K',757:'(K9)5',758:'(K5)9',759:'(95)K',
    760:'(K9)6',761:'(K6)9',762:'(96)K',763:'(K9)7',764:'(K7)9',765:'(97)K',766:'(K9)8',767:'(K8)9',768:'(98)K',769:'(KT)A',
    770:'(KA)T',771:'(TA)K',772:'(KT)2',773:'(K2)T',774:'(T2)K',775:'(KT)3',776:'(K3)T',777:'(T3)K',778:'(KT)4',779:'(K4)T',
    780:'(T4)K',781:'(KT)5',782:'(K5)T',783:'(T5)K',784:'(KT)6',785:'(K6)T',786:'(T6)K',787:'(KT)7',788:'(K7)T',789:'(T7)K',
    790:'(KT)8',791:'(K8)T',792:'(T8)K',793:'(KT)9',794:'(K9)T',795:'(T9)K',796:'(KJ)A',797:'(KA)J',798:'(JA)K',799:'(KJ)2',
    800:'(K2)J',801:'(J2)K',802:'(KJ)3',803:'(K3)J',804:'(J3)K',805:'(KJ)4',806:'(K4)J',807:'(J4)K',808:'(KJ)5',809:'(K5)J',
    810:'(J5)K',811:'(KJ)6',812:'(K6)J',813:'(J6)K',814:'(KJ)7',815:'(K7)J',816:'(J7)K',817:'(KJ)8',818:'(K8)J',819:'(J8)K',
    820:'(KJ)9',821:'(K9)J',822:'(J9)K',823:'(KJ)T',824:'(KT)J',825:'(JT)K',826:'(KQ)A',827:'(KA)Q',828:'(QA)K',829:'(KQ)2',
    830:'(K2)Q',831:'(Q2)K',832:'(KQ)3',833:'(K3)Q',834:'(Q3)K',835:'(KQ)4',836:'(K4)Q',837:'(Q4)K',838:'(KQ)5',839:'(K5)Q',
    840:'(Q5)K',841:'(KQ)6',842:'(K6)Q',843:'(Q6)K',844:'(KQ)7',845:'(K7)Q',846:'(Q7)K',847:'(KQ)8',848:'(K8)Q',849:'(Q8)K',
    850:'(KQ)9',851:'(K9)Q',852:'(Q9)K',853:'(KQ)T',854:'(KT)Q',855:'(QT)K',856:'(KQ)J',857:'(KJ)Q',858:'(QJ)K',859:'(2A)A',
    860:'(22)A',861:'(AA)2',862:'(2A)2',863:'(3A)A',864:'(33)A',865:'(AA)3',866:'(3A)3',867:'(32)2',868:'(33)2',869:'(22)3',
    870:'(32)3',871:'(4A)A',872:'(44)A',873:'(AA)4',874:'(4A)4',875:'(42)2',876:'(44)2',877:'(22)4',878:'(42)4',879:'(43)3',
    880:'(44)3',881:'(33)4',882:'(43)4',883:'(5A)A',884:'(55)A',885:'(AA)5',886:'(5A)5',887:'(52)2',888:'(55)2',889:'(22)5',
    890:'(52)5',891:'(53)3',892:'(55)3',893:'(33)5',894:'(53)5',895:'(54)4',896:'(55)4',897:'(44)5',898:'(54)5',899:'(6A)A',
    900:'(66)A',901:'(AA)6',902:'(6A)6',903:'(62)2',904:'(66)2',905:'(22)6',906:'(62)6',907:'(63)3',908:'(66)3',909:'(33)6',
    910:'(63)6',911:'(64)4',912:'(66)4',913:'(44)6',914:'(64)6',915:'(65)5',916:'(66)5',917:'(55)6',918:'(65)6',919:'(7A)A',
    920:'(77)A',921:'(AA)7',922:'(7A)7',923:'(72)2',924:'(77)2',925:'(22)7',926:'(72)7',927:'(73)3',928:'(77)3',929:'(33)7',
    930:'(73)7',931:'(74)4',932:'(77)4',933:'(44)7',934:'(74)7',935:'(75)5',936:'(77)5',937:'(55)7',938:'(75)7',939:'(76)6',
    940:'(77)6',941:'(66)7',942:'(76)7',943:'(8A)A',944:'(88)A',945:'(AA)8',946:'(8A)8',947:'(82)2',948:'(88)2',949:'(22)8',
    950:'(82)8',951:'(83)3',952:'(88)3',953:'(33)8',954:'(83)8',955:'(84)4',956:'(88)4',957:'(44)8',958:'(84)8',959:'(85)5',
    960:'(88)5',961:'(55)8',962:'(85)8',963:'(86)6',964:'(88)6',965:'(66)8',966:'(86)8',967:'(87)7',968:'(88)7',969:'(77)8',
    970:'(87)8',971:'(9A)A',972:'(99)A',973:'(AA)9',974:'(9A)9',975:'(92)2',976:'(99)2',977:'(22)9',978:'(92)9',979:'(93)3',
    980:'(99)3',981:'(33)9',982:'(93)9',983:'(94)4',984:'(99)4',985:'(44)9',986:'(94)9',987:'(95)5',988:'(99)5',989:'(55)9',
    990:'(95)9',991:'(96)6',992:'(99)6',993:'(66)9',994:'(96)9',995:'(97)7',996:'(99)7',997:'(77)9',998:'(97)9',999:'(98)8',
    1000:'(99)8',1001:'(88)9',1002:'(98)9',1003:'(TA)A',1004:'(TT)A',1005:'(AA)T',1006:'(TA)T',1007:'(T2)2',1008:'(TT)2',1009:'(22)T',
    1010:'(T2)T',1011:'(T3)3',1012:'(TT)3',1013:'(33)T',1014:'(T3)T',1015:'(T4)4',1016:'(TT)4',1017:'(44)T',1018:'(T4)T',1019:'(T5)5',
    1020:'(TT)5',1021:'(55)T',1022:'(T5)T',1023:'(T6)6',1024:'(TT)6',1025:'(66)T',1026:'(T6)T',1027:'(T7)7',1028:'(TT)7',1029:'(77)T',
    1030:'(T7)T',1031:'(T8)8',1032:'(TT)8',1033:'(88)T',1034:'(T8)T',1035:'(T9)9',1036:'(TT)9',1037:'(99)T',1038:'(T9)T',1039:'(JA)A',
    1040:'(JJ)A',1041:'(AA)J',1042:'(JA)J',1043:'(J2)2',1044:'(JJ)2',1045:'(22)J',1046:'(J2)J',1047:'(J3)3',1048:'(JJ)3',1049:'(33)J',
    1050:'(J3)J',1051:'(J4)4',1052:'(JJ)4',1053:'(44)J',1054:'(J4)J',1055:'(J5)5',1056:'(JJ)5',1057:'(55)J',1058:'(J5)J',1059:'(J6)6',
    1060:'(JJ)6',1061:'(66)J',1062:'(J6)J',1063:'(J7)7',1064:'(JJ)7',1065:'(77)J',1066:'(J7)J',1067:'(J8)8',1068:'(JJ)8',1069:'(88)J',
    1070:'(J8)J',1071:'(J9)9',1072:'(JJ)9',1073:'(99)J',1074:'(J9)J',1075:'(JT)T',1076:'(JJ)T',1077:'(TT)J',1078:'(JT)J',1079:'(QA)A',
    1080:'(QQ)A',1081:'(AA)Q',1082:'(QA)Q',1083:'(Q2)2',1084:'(QQ)2',1085:'(22)Q',1086:'(Q2)Q',1087:'(Q3)3',1088:'(QQ)3',1089:'(33)Q',
    1090:'(Q3)Q',1091:'(Q4)4',1092:'(QQ)4',1093:'(44)Q',1094:'(Q4)Q',1095:'(Q5)5',1096:'(QQ)5',1097:'(55)Q',1098:'(Q5)Q',1099:'(Q6)6',
    1100:'(QQ)6',1101:'(66)Q',1102:'(Q6)Q',1103:'(Q7)7',1104:'(QQ)7',1105:'(77)Q',1106:'(Q7)Q',1107:'(Q8)8',1108:'(QQ)8',1109:'(88)Q',
    1110:'(Q8)Q',1111:'(Q9)9',1112:'(QQ)9',1113:'(99)Q',1114:'(Q9)Q',1115:'(QT)T',1116:'(QQ)T',1117:'(TT)Q',1118:'(QT)Q',1119:'(QJ)J',
    1120:'(QQ)J',1121:'(JJ)Q',1122:'(QJ)Q',1123:'(KA)A',1124:'(KK)A',1125:'(AA)K',1126:'(KA)K',1127:'(K2)2',1128:'(KK)2',1129:'(22)K',
    1130:'(K2)K',1131:'(K3)3',1132:'(KK)3',1133:'(33)K',1134:'(K3)K',1135:'(K4)4',1136:'(KK)4',1137:'(44)K',1138:'(K4)K',1139:'(K5)5',
    1140:'(KK)5',1141:'(55)K',1142:'(K5)K',1143:'(K6)6',1144:'(KK)6',1145:'(66)K',1146:'(K6)K',1147:'(K7)7',1148:'(KK)7',1149:'(77)K',
    1150:'(K7)K',1151:'(K8)8',1152:'(KK)8',1153:'(88)K',1154:'(K8)K',1155:'(K9)9',1156:'(KK)9',1157:'(99)K',1158:'(K9)K',1159:'(KT)T',
    1160:'(KK)T',1161:'(TT)K',1162:'(KT)K',1163:'(KJ)J',1164:'(KK)J',1165:'(JJ)K',1166:'(KJ)K',1167:'(KQ)Q',1168:'(KK)Q',1169:'(QQ)K',
    1170:'(KQ)K',1171:'(AA)A',1172:'(22)2',1173:'(33)3',1174:'(44)4',1175:'(55)5',1176:'(66)6',1177:'(77)7',1178:'(88)8',1179:'(99)9',
    1180:'(TT)T',1181:'(JJ)J',1182:'(QQ)Q',1183:'(KK)K',
    }
    return decodeRazzList[idx]

def encodeRazzStartHand(cards):
    """Take Razz starting hand and return an integer index for storing in db"""
    startHand = ""
    if card_map_low[cards[0][0]] > card_map_low[cards[1][0]]:
        startHand = "(%s%s)%s" %(cards[0][0], cards[1][0], cards[2][0])
    else:
        startHand = "(%s%s)%s" %(cards[1][0], cards[0][0], cards[2][0])
    #print "DEBUG: startHand: %s" % startHand
    encodeRazzList = { 
    '(00)A':-13,'(00)2':-12,'(00)3':-11,'(00)4':-10,'(00)5':-9,'(00)6':-8,'(00)7':-7,'(00)8':-6,'(00)9':-5,'(00)T':-4,
    '(00)J':-3,'(00)Q':-2,'(00)K':-1,
    '(00)0':0,
    '(32)A':1,'(3A)2':2,'(2A)3':3,'(42)A':4,'(4A)2':5,'(2A)4':6,'(43)A':7,'(4A)3':8,'(3A)4':9,
    '(43)2':10,'(42)3':11,'(32)4':12,'(52)A':13,'(5A)2':14,'(2A)5':15,'(53)A':16,'(5A)3':17,'(3A)5':18,'(53)2':19,
    '(52)3':20,'(32)5':21,'(54)A':22,'(5A)4':23,'(4A)5':24,'(54)2':25,'(52)4':26,'(42)5':27,'(54)3':28,'(53)4':29,
    '(43)5':30,'(62)A':31,'(6A)2':32,'(2A)6':33,'(63)A':34,'(6A)3':35,'(3A)6':36,'(63)2':37,'(62)3':38,'(32)6':39,
    '(64)A':40,'(6A)4':41,'(4A)6':42,'(64)2':43,'(62)4':44,'(42)6':45,'(64)3':46,'(63)4':47,'(43)6':48,'(65)A':49,
    '(6A)5':50,'(5A)6':51,'(65)2':52,'(62)5':53,'(52)6':54,'(65)3':55,'(63)5':56,'(53)6':57,'(65)4':58,'(64)5':59,
    '(54)6':60,'(72)A':61,'(7A)2':62,'(2A)7':63,'(73)A':64,'(7A)3':65,'(3A)7':66,'(73)2':67,'(72)3':68,'(32)7':69,
    '(74)A':70,'(7A)4':71,'(4A)7':72,'(74)2':73,'(72)4':74,'(42)7':75,'(74)3':76,'(73)4':77,'(43)7':78,'(75)A':79,
    '(7A)5':80,'(5A)7':81,'(75)2':82,'(72)5':83,'(52)7':84,'(75)3':85,'(73)5':86,'(53)7':87,'(75)4':88,'(74)5':89,
    '(54)7':90,'(76)A':91,'(7A)6':92,'(6A)7':93,'(76)2':94,'(72)6':95,'(62)7':96,'(76)3':97,'(73)6':98,'(63)7':99,
    '(76)4':100,'(74)6':101,'(64)7':102,'(76)5':103,'(75)6':104,'(65)7':105,'(82)A':106,'(8A)2':107,'(2A)8':108,'(83)A':109,
    '(8A)3':110,'(3A)8':111,'(83)2':112,'(82)3':113,'(32)8':114,'(84)A':115,'(8A)4':116,'(4A)8':117,'(84)2':118,'(82)4':119,
    '(42)8':120,'(84)3':121,'(83)4':122,'(43)8':123,'(85)A':124,'(8A)5':125,'(5A)8':126,'(85)2':127,'(82)5':128,'(52)8':129,
    '(85)3':130,'(83)5':131,'(53)8':132,'(85)4':133,'(84)5':134,'(54)8':135,'(86)A':136,'(8A)6':137,'(6A)8':138,'(86)2':139,
    '(82)6':140,'(62)8':141,'(86)3':142,'(83)6':143,'(63)8':144,'(86)4':145,'(84)6':146,'(64)8':147,'(86)5':148,'(85)6':149,
    '(65)8':150,'(87)A':151,'(8A)7':152,'(7A)8':153,'(87)2':154,'(82)7':155,'(72)8':156,'(87)3':157,'(83)7':158,'(73)8':159,
    '(87)4':160,'(84)7':161,'(74)8':162,'(87)5':163,'(85)7':164,'(75)8':165,'(87)6':166,'(86)7':167,'(76)8':168,'(92)A':169,
    '(9A)2':170,'(2A)9':171,'(93)A':172,'(9A)3':173,'(3A)9':174,'(93)2':175,'(92)3':176,'(32)9':177,'(94)A':178,'(9A)4':179,
    '(4A)9':180,'(94)2':181,'(92)4':182,'(42)9':183,'(94)3':184,'(93)4':185,'(43)9':186,'(95)A':187,'(9A)5':188,'(5A)9':189,
    '(95)2':190,'(92)5':191,'(52)9':192,'(95)3':193,'(93)5':194,'(53)9':195,'(95)4':196,'(94)5':197,'(54)9':198,'(96)A':199,
    '(9A)6':200,'(6A)9':201,'(96)2':202,'(92)6':203,'(62)9':204,'(96)3':205,'(93)6':206,'(63)9':207,'(96)4':208,'(94)6':209,
    '(64)9':210,'(96)5':211,'(95)6':212,'(65)9':213,'(97)A':214,'(9A)7':215,'(7A)9':216,'(97)2':217,'(92)7':218,'(72)9':219,
    '(97)3':220,'(93)7':221,'(73)9':222,'(97)4':223,'(94)7':224,'(74)9':225,'(97)5':226,'(95)7':227,'(75)9':228,'(97)6':229,
    '(96)7':230,'(76)9':231,'(98)A':232,'(9A)8':233,'(8A)9':234,'(98)2':235,'(92)8':236,'(82)9':237,'(98)3':238,'(93)8':239,
    '(83)9':240,'(98)4':241,'(94)8':242,'(84)9':243,'(98)5':244,'(95)8':245,'(85)9':246,'(98)6':247,'(96)8':248,'(86)9':249,
    '(98)7':250,'(97)8':251,'(87)9':252,'(T2)A':253,'(TA)2':254,'(2A)T':255,'(T3)A':256,'(TA)3':257,'(3A)T':258,'(T3)2':259,
    '(T2)3':260,'(32)T':261,'(T4)A':262,'(TA)4':263,'(4A)T':264,'(T4)2':265,'(T2)4':266,'(42)T':267,'(T4)3':268,'(T3)4':269,
    '(43)T':270,'(T5)A':271,'(TA)5':272,'(5A)T':273,'(T5)2':274,'(T2)5':275,'(52)T':276,'(T5)3':277,'(T3)5':278,'(53)T':279,
    '(T5)4':280,'(T4)5':281,'(54)T':282,'(T6)A':283,'(TA)6':284,'(6A)T':285,'(T6)2':286,'(T2)6':287,'(62)T':288,'(T6)3':289,
    '(T3)6':290,'(63)T':291,'(T6)4':292,'(T4)6':293,'(64)T':294,'(T6)5':295,'(T5)6':296,'(65)T':297,'(T7)A':298,'(TA)7':299,
    '(7A)T':300,'(T7)2':301,'(T2)7':302,'(72)T':303,'(T7)3':304,'(T3)7':305,'(73)T':306,'(T7)4':307,'(T4)7':308,'(74)T':309,
    '(T7)5':310,'(T5)7':311,'(75)T':312,'(T7)6':313,'(T6)7':314,'(76)T':315,'(T8)A':316,'(TA)8':317,'(8A)T':318,'(T8)2':319,
    '(T2)8':320,'(82)T':321,'(T8)3':322,'(T3)8':323,'(83)T':324,'(T8)4':325,'(T4)8':326,'(84)T':327,'(T8)5':328,'(T5)8':329,
    '(85)T':330,'(T8)6':331,'(T6)8':332,'(86)T':333,'(T8)7':334,'(T7)8':335,'(87)T':336,'(T9)A':337,'(TA)9':338,'(9A)T':339,
    '(T9)2':340,'(T2)9':341,'(92)T':342,'(T9)3':343,'(T3)9':344,'(93)T':345,'(T9)4':346,'(T4)9':347,'(94)T':348,'(T9)5':349,
    '(T5)9':350,'(95)T':351,'(T9)6':352,'(T6)9':353,'(96)T':354,'(T9)7':355,'(T7)9':356,'(97)T':357,'(T9)8':358,'(T8)9':359,
    '(98)T':360,'(J2)A':361,'(JA)2':362,'(2A)J':363,'(J3)A':364,'(JA)3':365,'(3A)J':366,'(J3)2':367,'(J2)3':368,'(32)J':369,
    '(J4)A':370,'(JA)4':371,'(4A)J':372,'(J4)2':373,'(J2)4':374,'(42)J':375,'(J4)3':376,'(J3)4':377,'(43)J':378,'(J5)A':379,
    '(JA)5':380,'(5A)J':381,'(J5)2':382,'(J2)5':383,'(52)J':384,'(J5)3':385,'(J3)5':386,'(53)J':387,'(J5)4':388,'(J4)5':389,
    '(54)J':390,'(J6)A':391,'(JA)6':392,'(6A)J':393,'(J6)2':394,'(J2)6':395,'(62)J':396,'(J6)3':397,'(J3)6':398,'(63)J':399,
    '(J6)4':400,'(J4)6':401,'(64)J':402,'(J6)5':403,'(J5)6':404,'(65)J':405,'(J7)A':406,'(JA)7':407,'(7A)J':408,'(J7)2':409,
    '(J2)7':410,'(72)J':411,'(J7)3':412,'(J3)7':413,'(73)J':414,'(J7)4':415,'(J4)7':416,'(74)J':417,'(J7)5':418,'(J5)7':419,
    '(75)J':420,'(J7)6':421,'(J6)7':422,'(76)J':423,'(J8)A':424,'(JA)8':425,'(8A)J':426,'(J8)2':427,'(J2)8':428,'(82)J':429,
    '(J8)3':430,'(J3)8':431,'(83)J':432,'(J8)4':433,'(J4)8':434,'(84)J':435,'(J8)5':436,'(J5)8':437,'(85)J':438,'(J8)6':439,
    '(J6)8':440,'(86)J':441,'(J8)7':442,'(J7)8':443,'(87)J':444,'(J9)A':445,'(JA)9':446,'(9A)J':447,'(J9)2':448,'(J2)9':449,
    '(92)J':450,'(J9)3':451,'(J3)9':452,'(93)J':453,'(J9)4':454,'(J4)9':455,'(94)J':456,'(J9)5':457,'(J5)9':458,'(95)J':459,
    '(J9)6':460,'(J6)9':461,'(96)J':462,'(J9)7':463,'(J7)9':464,'(97)J':465,'(J9)8':466,'(J8)9':467,'(98)J':468,'(JT)A':469,
    '(JA)T':470,'(TA)J':471,'(JT)2':472,'(J2)T':473,'(T2)J':474,'(JT)3':475,'(J3)T':476,'(T3)J':477,'(JT)4':478,'(J4)T':479,
    '(T4)J':480,'(JT)5':481,'(J5)T':482,'(T5)J':483,'(JT)6':484,'(J6)T':485,'(T6)J':486,'(JT)7':487,'(J7)T':488,'(T7)J':489,
    '(JT)8':490,'(J8)T':491,'(T8)J':492,'(JT)9':493,'(J9)T':494,'(T9)J':495,'(Q2)A':496,'(QA)2':497,'(2A)Q':498,'(Q3)A':499,
    '(QA)3':500,'(3A)Q':501,'(Q3)2':502,'(Q2)3':503,'(32)Q':504,'(Q4)A':505,'(QA)4':506,'(4A)Q':507,'(Q4)2':508,'(Q2)4':509,
    '(42)Q':510,'(Q4)3':511,'(Q3)4':512,'(43)Q':513,'(Q5)A':514,'(QA)5':515,'(5A)Q':516,'(Q5)2':517,'(Q2)5':518,'(52)Q':519,
    '(Q5)3':520,'(Q3)5':521,'(53)Q':522,'(Q5)4':523,'(Q4)5':524,'(54)Q':525,'(Q6)A':526,'(QA)6':527,'(6A)Q':528,'(Q6)2':529,
    '(Q2)6':530,'(62)Q':531,'(Q6)3':532,'(Q3)6':533,'(63)Q':534,'(Q6)4':535,'(Q4)6':536,'(64)Q':537,'(Q6)5':538,'(Q5)6':539,
    '(65)Q':540,'(Q7)A':541,'(QA)7':542,'(7A)Q':543,'(Q7)2':544,'(Q2)7':545,'(72)Q':546,'(Q7)3':547,'(Q3)7':548,'(73)Q':549,
    '(Q7)4':550,'(Q4)7':551,'(74)Q':552,'(Q7)5':553,'(Q5)7':554,'(75)Q':555,'(Q7)6':556,'(Q6)7':557,'(76)Q':558,'(Q8)A':559,
    '(QA)8':560,'(8A)Q':561,'(Q8)2':562,'(Q2)8':563,'(82)Q':564,'(Q8)3':565,'(Q3)8':566,'(83)Q':567,'(Q8)4':568,'(Q4)8':569,
    '(84)Q':570,'(Q8)5':571,'(Q5)8':572,'(85)Q':573,'(Q8)6':574,'(Q6)8':575,'(86)Q':576,'(Q8)7':577,'(Q7)8':578,'(87)Q':579,
    '(Q9)A':580,'(QA)9':581,'(9A)Q':582,'(Q9)2':583,'(Q2)9':584,'(92)Q':585,'(Q9)3':586,'(Q3)9':587,'(93)Q':588,'(Q9)4':589,
    '(Q4)9':590,'(94)Q':591,'(Q9)5':592,'(Q5)9':593,'(95)Q':594,'(Q9)6':595,'(Q6)9':596,'(96)Q':597,'(Q9)7':598,'(Q7)9':599,
    '(97)Q':600,'(Q9)8':601,'(Q8)9':602,'(98)Q':603,'(QT)A':604,'(QA)T':605,'(TA)Q':606,'(QT)2':607,'(Q2)T':608,'(T2)Q':609,
    '(QT)3':610,'(Q3)T':611,'(T3)Q':612,'(QT)4':613,'(Q4)T':614,'(T4)Q':615,'(QT)5':616,'(Q5)T':617,'(T5)Q':618,'(QT)6':619,
    '(Q6)T':620,'(T6)Q':621,'(QT)7':622,'(Q7)T':623,'(T7)Q':624,'(QT)8':625,'(Q8)T':626,'(T8)Q':627,'(QT)9':628,'(Q9)T':629,
    '(T9)Q':630,'(QJ)A':631,'(QA)J':632,'(JA)Q':633,'(QJ)2':634,'(Q2)J':635,'(J2)Q':636,'(QJ)3':637,'(Q3)J':638,'(J3)Q':639,
    '(QJ)4':640,'(Q4)J':641,'(J4)Q':642,'(QJ)5':643,'(Q5)J':644,'(J5)Q':645,'(QJ)6':646,'(Q6)J':647,'(J6)Q':648,'(QJ)7':649,
    '(Q7)J':650,'(J7)Q':651,'(QJ)8':652,'(Q8)J':653,'(J8)Q':654,'(QJ)9':655,'(Q9)J':656,'(J9)Q':657,'(QJ)T':658,'(QT)J':659,
    '(JT)Q':660,'(K2)A':661,'(KA)2':662,'(2A)K':663,'(K3)A':664,'(KA)3':665,'(3A)K':666,'(K3)2':667,'(K2)3':668,'(32)K':669,
    '(K4)A':670,'(KA)4':671,'(4A)K':672,'(K4)2':673,'(K2)4':674,'(42)K':675,'(K4)3':676,'(K3)4':677,'(43)K':678,'(K5)A':679,
    '(KA)5':680,'(5A)K':681,'(K5)2':682,'(K2)5':683,'(52)K':684,'(K5)3':685,'(K3)5':686,'(53)K':687,'(K5)4':688,'(K4)5':689,
    '(54)K':690,'(K6)A':691,'(KA)6':692,'(6A)K':693,'(K6)2':694,'(K2)6':695,'(62)K':696,'(K6)3':697,'(K3)6':698,'(63)K':699,
    '(K6)4':700,'(K4)6':701,'(64)K':702,'(K6)5':703,'(K5)6':704,'(65)K':705,'(K7)A':706,'(KA)7':707,'(7A)K':708,'(K7)2':709,
    '(K2)7':710,'(72)K':711,'(K7)3':712,'(K3)7':713,'(73)K':714,'(K7)4':715,'(K4)7':716,'(74)K':717,'(K7)5':718,'(K5)7':719,
    '(75)K':720,'(K7)6':721,'(K6)7':722,'(76)K':723,'(K8)A':724,'(KA)8':725,'(8A)K':726,'(K8)2':727,'(K2)8':728,'(82)K':729,
    '(K8)3':730,'(K3)8':731,'(83)K':732,'(K8)4':733,'(K4)8':734,'(84)K':735,'(K8)5':736,'(K5)8':737,'(85)K':738,'(K8)6':739,
    '(K6)8':740,'(86)K':741,'(K8)7':742,'(K7)8':743,'(87)K':744,'(K9)A':745,'(KA)9':746,'(9A)K':747,'(K9)2':748,'(K2)9':749,
    '(92)K':750,'(K9)3':751,'(K3)9':752,'(93)K':753,'(K9)4':754,'(K4)9':755,'(94)K':756,'(K9)5':757,'(K5)9':758,'(95)K':759,
    '(K9)6':760,'(K6)9':761,'(96)K':762,'(K9)7':763,'(K7)9':764,'(97)K':765,'(K9)8':766,'(K8)9':767,'(98)K':768,'(KT)A':769,
    '(KA)T':770,'(TA)K':771,'(KT)2':772,'(K2)T':773,'(T2)K':774,'(KT)3':775,'(K3)T':776,'(T3)K':777,'(KT)4':778,'(K4)T':779,
    '(T4)K':780,'(KT)5':781,'(K5)T':782,'(T5)K':783,'(KT)6':784,'(K6)T':785,'(T6)K':786,'(KT)7':787,'(K7)T':788,'(T7)K':789,
    '(KT)8':790,'(K8)T':791,'(T8)K':792,'(KT)9':793,'(K9)T':794,'(T9)K':795,'(KJ)A':796,'(KA)J':797,'(JA)K':798,'(KJ)2':799,
    '(K2)J':800,'(J2)K':801,'(KJ)3':802,'(K3)J':803,'(J3)K':804,'(KJ)4':805,'(K4)J':806,'(J4)K':807,'(KJ)5':808,'(K5)J':809,
    '(J5)K':810,'(KJ)6':811,'(K6)J':812,'(J6)K':813,'(KJ)7':814,'(K7)J':815,'(J7)K':816,'(KJ)8':817,'(K8)J':818,'(J8)K':819,
    '(KJ)9':820,'(K9)J':821,'(J9)K':822,'(KJ)T':823,'(KT)J':824,'(JT)K':825,'(KQ)A':826,'(KA)Q':827,'(QA)K':828,'(KQ)2':829,
    '(K2)Q':830,'(Q2)K':831,'(KQ)3':832,'(K3)Q':833,'(Q3)K':834,'(KQ)4':835,'(K4)Q':836,'(Q4)K':837,'(KQ)5':838,'(K5)Q':839,
    '(Q5)K':840,'(KQ)6':841,'(K6)Q':842,'(Q6)K':843,'(KQ)7':844,'(K7)Q':845,'(Q7)K':846,'(KQ)8':847,'(K8)Q':848,'(Q8)K':849,
    '(KQ)9':850,'(K9)Q':851,'(Q9)K':852,'(KQ)T':853,'(KT)Q':854,'(QT)K':855,'(KQ)J':856,'(KJ)Q':857,'(QJ)K':858,'(2A)A':859,
    '(22)A':860,'(AA)2':861,'(2A)2':862,'(3A)A':863,'(33)A':864,'(AA)3':865,'(3A)3':866,'(32)2':867,'(33)2':868,'(22)3':869,
    '(32)3':870,'(4A)A':871,'(44)A':872,'(AA)4':873,'(4A)4':874,'(42)2':875,'(44)2':876,'(22)4':877,'(42)4':878,'(43)3':879,
    '(44)3':880,'(33)4':881,'(43)4':882,'(5A)A':883,'(55)A':884,'(AA)5':885,'(5A)5':886,'(52)2':887,'(55)2':888,'(22)5':889,
    '(52)5':890,'(53)3':891,'(55)3':892,'(33)5':893,'(53)5':894,'(54)4':895,'(55)4':896,'(44)5':897,'(54)5':898,'(6A)A':899,
    '(66)A':900,'(AA)6':901,'(6A)6':902,'(62)2':903,'(66)2':904,'(22)6':905,'(62)6':906,'(63)3':907,'(66)3':908,'(33)6':909,
    '(63)6':910,'(64)4':911,'(66)4':912,'(44)6':913,'(64)6':914,'(65)5':915,'(66)5':916,'(55)6':917,'(65)6':918,'(7A)A':919,
    '(77)A':920,'(AA)7':921,'(7A)7':922,'(72)2':923,'(77)2':924,'(22)7':925,'(72)7':926,'(73)3':927,'(77)3':928,'(33)7':929,
    '(73)7':930,'(74)4':931,'(77)4':932,'(44)7':933,'(74)7':934,'(75)5':935,'(77)5':936,'(55)7':937,'(75)7':938,'(76)6':939,
    '(77)6':940,'(66)7':941,'(76)7':942,'(8A)A':943,'(88)A':944,'(AA)8':945,'(8A)8':946,'(82)2':947,'(88)2':948,'(22)8':949,
    '(82)8':950,'(83)3':951,'(88)3':952,'(33)8':953,'(83)8':954,'(84)4':955,'(88)4':956,'(44)8':957,'(84)8':958,'(85)5':959,
    '(88)5':960,'(55)8':961,'(85)8':962,'(86)6':963,'(88)6':964,'(66)8':965,'(86)8':966,'(87)7':967,'(88)7':968,'(77)8':969,
    '(87)8':970,'(9A)A':971,'(99)A':972,'(AA)9':973,'(9A)9':974,'(92)2':975,'(99)2':976,'(22)9':977,'(92)9':978,'(93)3':979,
    '(99)3':980,'(33)9':981,'(93)9':982,'(94)4':983,'(99)4':984,'(44)9':985,'(94)9':986,'(95)5':987,'(99)5':988,'(55)9':989,
    '(95)9':990,'(96)6':991,'(99)6':992,'(66)9':993,'(96)9':994,'(97)7':995,'(99)7':996,'(77)9':997,'(97)9':998,'(98)8':999,
    '(99)8':1000,'(88)9':1001,'(98)9':1002,'(TA)A':1003,'(TT)A':1004,'(AA)T':1005,'(TA)T':1006,'(T2)2':1007,'(TT)2':1008,'(22)T':1009,
    '(T2)T':1010,'(T3)3':1011,'(TT)3':1012,'(33)T':1013,'(T3)T':1014,'(T4)4':1015,'(TT)4':1016,'(44)T':1017,'(T4)T':1018,'(T5)5':1019,
    '(TT)5':1020,'(55)T':1021,'(T5)T':1022,'(T6)6':1023,'(TT)6':1024,'(66)T':1025,'(T6)T':1026,'(T7)7':1027,'(TT)7':1028,'(77)T':1029,
    '(T7)T':1030,'(T8)8':1031,'(TT)8':1032,'(88)T':1033,'(T8)T':1034,'(T9)9':1035,'(TT)9':1036,'(99)T':1037,'(T9)T':1038,'(JA)A':1039,
    '(JJ)A':1040,'(AA)J':1041,'(JA)J':1042,'(J2)2':1043,'(JJ)2':1044,'(22)J':1045,'(J2)J':1046,'(J3)3':1047,'(JJ)3':1048,'(33)J':1049,
    '(J3)J':1050,'(J4)4':1051,'(JJ)4':1052,'(44)J':1053,'(J4)J':1054,'(J5)5':1055,'(JJ)5':1056,'(55)J':1057,'(J5)J':1058,'(J6)6':1059,
    '(JJ)6':1060,'(66)J':1061,'(J6)J':1062,'(J7)7':1063,'(JJ)7':1064,'(77)J':1065,'(J7)J':1066,'(J8)8':1067,'(JJ)8':1068,'(88)J':1069,
    '(J8)J':1070,'(J9)9':1071,'(JJ)9':1072,'(99)J':1073,'(J9)J':1074,'(JT)T':1075,'(JJ)T':1076,'(TT)J':1077,'(JT)J':1078,'(QA)A':1079,
    '(QQ)A':1080,'(AA)Q':1081,'(QA)Q':1082,'(Q2)2':1083,'(QQ)2':1084,'(22)Q':1085,'(Q2)Q':1086,'(Q3)3':1087,'(QQ)3':1088,'(33)Q':1089,
    '(Q3)Q':1090,'(Q4)4':1091,'(QQ)4':1092,'(44)Q':1093,'(Q4)Q':1094,'(Q5)5':1095,'(QQ)5':1096,'(55)Q':1097,'(Q5)Q':1098,'(Q6)6':1099,
    '(QQ)6':1100,'(66)Q':1101,'(Q6)Q':1102,'(Q7)7':1103,'(QQ)7':1104,'(77)Q':1105,'(Q7)Q':1106,'(Q8)8':1107,'(QQ)8':1108,'(88)Q':1109,
    '(Q8)Q':1110,'(Q9)9':1111,'(QQ)9':1112,'(99)Q':1113,'(Q9)Q':1114,'(QT)T':1115,'(QQ)T':1116,'(TT)Q':1117,'(QT)Q':1118,'(QJ)J':1119,
    '(QQ)J':1120,'(JJ)Q':1121,'(QJ)Q':1122,'(KA)A':1123,'(KK)A':1124,'(AA)K':1125,'(KA)K':1126,'(K2)2':1127,'(KK)2':1128,'(22)K':1129,
    '(K2)K':1130,'(K3)3':1131,'(KK)3':1132,'(33)K':1133,'(K3)K':1134,'(K4)4':1135,'(KK)4':1136,'(44)K':1137,'(K4)K':1138,'(K5)5':1139,
    '(KK)5':1140,'(55)K':1141,'(K5)K':1142,'(K6)6':1143,'(KK)6':1144,'(66)K':1145,'(K6)K':1146,'(K7)7':1147,'(KK)7':1148,'(77)K':1149,
    '(K7)K':1150,'(K8)8':1151,'(KK)8':1152,'(88)K':1153,'(K8)K':1154,'(K9)9':1155,'(KK)9':1156,'(99)K':1157,'(K9)K':1158,'(KT)T':1159,
    '(KK)T':1160,'(TT)K':1161,'(KT)K':1162,'(KJ)J':1163,'(KK)J':1164,'(JJ)K':1165,'(KJ)K':1166,'(KQ)Q':1167,'(KK)Q':1168,'(QQ)K':1169,
    '(KQ)K':1170,'(AA)A':1171,'(22)2':1172,'(33)3':1173,'(44)4':1174,'(55)5':1175,'(66)6':1176,'(77)7':1177,'(88)8':1178,'(99)9':1179,
    '(TT)T':1180,'(JJ)J':1181,'(QQ)Q':1182,'(KK)K':1183,
    }
    #print "DEBUG: encodeRazzList['%s']: %s" % (startHand, encodeRazzList[startHand])
    return encodeRazzList[startHand]

if __name__ == '__main__':
    print("1) Card from list id (suitFromCardList: 1=2h)")
    print("2) listid from Card (encodeCardList: 2h=2)")
    s = raw_input('--> ')
    if s == '1':
        cardid = raw_input('Enter cardid: ')
        print("Value: '%s'" % suitFromCardList[int(cardid)])
    elif s == '2':
        while True:
            cardid = raw_input('Enter card: ')
            print("Encoded card: '%s'" % encodeCard(cardid))

