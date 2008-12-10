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

#methods that are specific to holdem but not trivial

import fpdb_simple
import fpdb_save_to_db

#parses a holdem hand
def mainParser(backend, db, cursor, site, category, hand):
    if (category=="holdem" or category=="omahahi" or category=="omahahilo"):
        base="hold"
    else:
        base="stud"
    #part 0: create the empty arrays
    lineTypes=[] #char, valid values: header, name, cards, action, win, rake, ignore
    lineStreets=[] #char, valid values: (predeal, preflop, flop, turn, river)

    cardValues, cardSuits, boardValues, boardSuits, antes, actionTypes, allIns, actionAmounts, actionNos, actionTypeByNo, seatLines, winnings, rakes=[],[],[],[],[],[],[],[],[],[],[],[],[]

    #part 1: read hand no and check for duplicate
    siteHandNo=fpdb_simple.parseSiteHandNo(hand[0])
    handStartTime=fpdb_simple.parseHandStartTime(hand[0], site)
    siteID=fpdb_simple.recogniseSiteID(cursor, site)
    #print "parse logic, siteID:",siteID,"site:",site
    
    isTourney=fpdb_simple.isTourney(hand[0])
    smallBlindLine=0
    for i in range(len(hand)):
        if hand[i].find("posts small blind")!=-1 or hand[i].find("posts the small blind")!=-1:
            if hand[i][-2:] == "$0":
                continue
            smallBlindLine=i
            #print "found small blind line:",smallBlindLine
            break
    #print "small blind line:",smallBlindLine
    gametypeID=fpdb_simple.recogniseGametypeID(backend, db, cursor, hand[0], hand[smallBlindLine], siteID, category, isTourney)
    if isTourney:
        if site!="ps":
            raise fpdb_simple.FpdbError("tourneys are only supported on PS right now")
        siteTourneyNo=fpdb_simple.parseTourneyNo(hand[0])
        buyin=fpdb_simple.parseBuyin(hand[0])
        fee=fpdb_simple.parseFee(hand[0])
        entries=-1 #todo: parse this
        prizepool=-1 #todo: parse this
        knockout=0
        tourneyStartTime=handStartTime #todo: read tourney start time
        rebuyOrAddon=fpdb_simple.isRebuyOrAddon(hand[0])

        tourneyTypeId=fpdb_simple.recogniseTourneyTypeId(cursor, siteID, buyin, fee, knockout, rebuyOrAddon)        
    fpdb_simple.isAlreadyInDB(cursor, gametypeID, siteHandNo)
    
    #part 2: classify lines by type (e.g. cards, action, win, sectionchange) and street
    fpdb_simple.classifyLines(hand, category, lineTypes, lineStreets)
        
    #part 3: read basic player info    
    #3a read player names, startcashes
    for i in range (len(hand)): #todo: use maxseats+1 here.
        if (lineTypes[i]=="name"):
            seatLines.append(hand[i])
    names=fpdb_simple.parseNames(seatLines)
    playerIDs = fpdb_simple.recognisePlayerIDs(cursor, names, siteID)
    tmp=fpdb_simple.parseCashesAndSeatNos(seatLines, site)
    startCashes=tmp['startCashes']
    seatNos=tmp['seatNos']
    
    fpdb_simple.createArrays(category, len(names), cardValues, cardSuits, antes, winnings, rakes, actionTypes, allIns, actionAmounts, actionNos, actionTypeByNo)
    
    #3b read positions
    if base=="hold":
        positions = fpdb_simple.parsePositions (hand, names)
    
    #part 4: take appropriate action for each line based on linetype
    for i in range(len(hand)):
        if (lineTypes[i]=="cards"):
            fpdb_simple.parseCardLine (site, category, lineStreets[i], hand[i], names, cardValues, cardSuits, boardValues, boardSuits)
            #if category=="studhilo":
            #    print "hand[i]:", hand[i]
            #    print "cardValues:", cardValues
            #    print "cardSuits:", cardSuits
        elif (lineTypes[i]=="action"):
            fpdb_simple.parseActionLine (site, base, isTourney, hand[i], lineStreets[i], playerIDs, names, actionTypes, allIns, actionAmounts, actionNos, actionTypeByNo)
        elif (lineTypes[i]=="win"):
            fpdb_simple.parseWinLine (hand[i], site, names, winnings, isTourney)
        elif (lineTypes[i]=="rake"):
            if isTourney:
                totalRake=0
            else:
                totalRake=fpdb_simple.parseRake(hand[i])
            fpdb_simple.splitRake(winnings, rakes, totalRake)
        elif (lineTypes[i]=="header" or lineTypes[i]=="rake" or lineTypes[i]=="name" or lineTypes[i]=="ignore"):
            pass
        elif (lineTypes[i]=="ante"):
            fpdb_simple.parseAnteLine(hand[i], site, isTourney, names, antes)
        elif (lineTypes[i]=="table"):
            tableResult=fpdb_simple.parseTableLine(site, base, hand[i])
        else:
            raise fpdb_simple.FpdbError("unrecognised lineType:"+lineTypes[i])
    if site=="ftp":
        tableResult=fpdb_simple.parseTableLine(site, base, hand[0])
    maxSeats=tableResult['maxSeats']
    tableName=tableResult['tableName']
    #print "before part5, antes:", antes
    
    #part 5: final preparations, then call fpdb_save_to_db.* with
    #         the arrays as they are - that file will fill them.
    fpdb_simple.convertCardValues(cardValues)
    if base=="hold":
        fpdb_simple.convertCardValuesBoard(boardValues)
        fpdb_simple.convertBlindBet(actionTypes, actionAmounts)
        fpdb_simple.checkPositions(positions)
        
    cursor.execute("SELECT limitType FROM Gametypes WHERE id=%s",(gametypeID, ))
    limit_type=cursor.fetchone()[0]
    fpdb_simple.convert3B4B(site, category, limit_type, actionTypes, actionAmounts)
    
    totalWinnings=0
    for i in range(len(winnings)):
        totalWinnings+=winnings[i]
    
    if base=="hold":
        hudImportData=fpdb_simple.generateHudCacheData(playerIDs, base, category, actionTypes
                                     , allIns, actionTypeByNo, winnings, totalWinnings, positions
                                     , actionTypes, actionAmounts)
    else:
        hudImportData=fpdb_simple.generateHudCacheData(playerIDs, base, category, actionTypes
                                     , allIns, actionTypeByNo, winnings, totalWinnings, None
                                     , actionTypes, actionAmounts)
    
    if isTourney:
        ranks=[]
        for i in range (len(names)):
            ranks.append(0)
        payin_amounts=fpdb_simple.calcPayin(len(names), buyin, fee)
        
        if base=="hold":
            result = fpdb_save_to_db.tourney_holdem_omaha(
                                       backend, db, cursor, base, category, siteTourneyNo, buyin
                                     , fee, knockout, entries, prizepool, tourneyStartTime
                                     , payin_amounts, ranks, tourneyTypeId, siteID, siteHandNo
                                     , gametypeID, handStartTime, names, playerIDs, startCashes
                                     , positions, cardValues, cardSuits, boardValues, boardSuits
                                     , winnings, rakes, actionTypes, allIns, actionAmounts
                                     , actionNos, hudImportData, maxSeats, tableName, seatNos)
        elif base=="stud":
            result = fpdb_save_to_db.tourney_stud(
                                       backend, db, cursor, base, category, siteTourneyNo
                                     , buyin, fee, knockout, entries, prizepool, tourneyStartTime
                                     , payin_amounts, ranks, tourneyTypeId, siteID, siteHandNo
                                     , gametypeID, handStartTime, names, playerIDs, startCashes
                                     , antes, cardValues, cardSuits, winnings, rakes, actionTypes
                                     , allIns, actionAmounts, actionNos, hudImportData, maxSeats
                                     , tableName, seatNos)
        else:
            raise fpdb_simple.FpdbError ("unrecognised category")
    else:
        if base=="hold":
            result = fpdb_save_to_db.ring_holdem_omaha(
                                       backend, db, cursor, base, category, siteHandNo
                                     , gametypeID, handStartTime, names, playerIDs
                                     , startCashes, positions, cardValues, cardSuits
                                     , boardValues, boardSuits, winnings, rakes
                                     , actionTypes, allIns, actionAmounts, actionNos
                                     , hudImportData, maxSeats, tableName, seatNos)
        elif base=="stud":
            result = fpdb_save_to_db.ring_stud(
                                       backend, db, cursor, base, category, siteHandNo, gametypeID
                                     , handStartTime, names, playerIDs, startCashes, antes
                                     , cardValues, cardSuits, winnings, rakes, actionTypes, allIns
                                     , actionAmounts, actionNos, hudImportData, maxSeats, tableName
                                     , seatNos)
        else:
            raise fpdb_simple.FpdbError ("unrecognised category")
        db.commit()
    return result
#end def mainParser

