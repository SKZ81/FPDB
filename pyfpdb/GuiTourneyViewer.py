#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2010-2011 Steffen Schaumburg
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


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk

from PyQt5.QtCore import QCoreApplication, QSortFilterProxyModel, Qt
from PyQt5.QtGui import (QPainter, QPixmap, QStandardItem, QStandardItemModel)
from PyQt5.QtWidgets import (QApplication, QFrame, QMenu,
                             QComboBox, QLabel, QLineEdit, QPushButton,
                             QProgressDialog, QScrollArea, QSplitter,
                             QTableView, QHBoxLayout, QVBoxLayout)

class GuiTourneyViewer:
    def __init__(self, config, db, sql, mainwin, debug=True):
        self.db = db
        self.colnum = {
                  'Stakes'       : 0,
                  'Pos'          : 1,
                  'Street0'      : 2,
                  'Action0'      : 3,
                  'Street1-4'    : 4,
                  'Action1-4'    : 5,
                  'Won'          : 6,
                  'Bet'          : 7,
                  'Net'          : 8,
                  'Game'         : 9,
                  'HandId'       : 10,
                 }
        
        self.mainVBox = QFrame()
        self.mainVBox.setLayout(QVBoxLayout())

        self.interfaceHBox = QFrame()
        self.interfaceHBox.setLayout(QHBoxLayout())
        self.mainVBox.layout().addWidget(self.interfaceHBox)

        self.siteBox = QComboBox()
        for site in config.supported_sites:
            self.siteBox.addItem(site)
        # self.siteBox.set_active(0)
        self.interfaceHBox.layout().addWidget(self.siteBox)
        
        label = QLabel(_("Enter the tourney number you want to display:"))
        self.interfaceHBox.layout().addWidget(label)
        
        self.entryTourney = QLineEdit()
        self.interfaceHBox.layout().addWidget(self.entryTourney)
        
        self.displayButton = QPushButton(_("Display"))
        self.displayButton.clicked.connect(self.displayClicked)
        self.interfaceHBox.layout().addWidget(self.displayButton)
        
        self.entryPlayer = QLineEdit()
        self.interfaceHBox.layout().addWidget(self.entryPlayer)
        
        self.playerButton = QPushButton(_("Display Player"))
        self.playerButton.clicked.connect(self.displayPlayerClicked)
        self.interfaceHBox.layout().addWidget(self.playerButton)
        
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.model = QStandardItemModel(0, len(self.colnum), self.table)
        self.model.setHorizontalHeaderLabels(self.colnum.keys())

        self.filterModel = QSortFilterProxyModel()
        self.filterModel.setSourceModel(self.model)
        self.filterModel.setSortRole(Qt.UserRole)
        self.table.setModel(self.filterModel)
        self.table.verticalHeader().hide()
        # self.table.doubleClicked.connect(self.row_activated)
        # self.table.contextMenuEvent = self.contextMenu
        self.filterModel.rowsInserted.connect(lambda index, start, end: [self.table.resizeRowToContents(r) for r in range(start, end + 1)])
        # self.filterModel.filterAcceptsRow = lambda row, sourceParent: self.is_row_in_card_filter(row)

        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)

        self.mainVBox.layout().addWidget(self.table)
        
        # self.mainVBox.show()
    #end def __init__
    
    def displayClicked(self, widget, data=None):
        if self.prepare(10, 9):
            result=self.db.getTourneyInfo(self.siteName, self.tourneyNo)
            if result[1] == None:
                self.table.reset()
                self.errorLabel = QLabel(_("Tournament not found.") + " " + _("Please ensure you imported it and selected the correct site."))
                self.mainVBox.layout().addWidget(self.errorLabel)
            else:
                x=0
                y=0
                for i in range(1,len(result[0])):
                    if y==9:
                        x+=2
                        y=0
            
                    label = QLabel(result[0][i])
                    self.table.attach(label,x,x+1,y,y+1)
            
                    if result[1][i]==None:
                        label = QLabel("N/A")
                    else:
                        label = QLabel(result[1][i])
                    self.table.attach(label,x+1,x+2,y,y+1)
            
                    y+=1
        # self.mainVBox.show_all()
    #def displayClicked
    
    def displayPlayerClicked(self, widget, data=None):
        if self.prepare(4, 5):
            result=self.db.getTourneyPlayerInfo(self.siteName, self.tourneyNo, self.playerName)
            if result[1] == None:
                self.table.reset()
                self.errorLabel = QLabel(_("Player or tournament not found.") + " " + _("Please ensure you imported it and selected the correct site."))
                self.mainVBox.layout().addWidget(self.errorLabel)
            else:
                x=0
                y=0
                for i in range(1,len(result[0])):
                    if y==5:
                        x+=2
                        y=0
                
                    label = QLabel(result[0][i])
                    self.table.attach(label,x,x+1,y,y+1)
                
                    if result[1][i]==None:
                        label = QLabel(_("N/A"))
                    else:
                        label = QLabel(result[1][i])
                    self.table.attach(label,x+1,x+2,y,y+1)
                
                    y+=1
        # self.mainVBox.show()
    #def displayPlayerClicked
    
    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainVBox
    #end def get_vbox
    
    def prepare(self, columns, rows):
        try: self.errorLabel.destroy()
        except: pass
        
        try:
            self.tourneyNo = int(self.entryTourney.text())
        except ValueError:
            self.errorLabel = QLabel(_("invalid entry in tourney number - must enter numbers only"))
            self.mainVBox.layout().addWidget(self.errorLabel)
            return False
        self.siteName=self.siteBox.currentText()
        self.playerName=self.entryPlayer.text()
        
        self.table.reset()

        return True
    #end def readInfo
#end class GuiTourneyViewer
