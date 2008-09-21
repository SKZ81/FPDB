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

import threading
import pygtk
pygtk.require('2.0')
import gtk
import os

try:
	from matplotlib.figure import Figure
	from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
	from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
	from numpy import arange, sin, pi
except:
	print "Failed to load libs for graphing, graphing will not function. Please install numpy and matplotlib."

import fpdb_import
import fpdb_db

class GuiGraphViewer (threading.Thread):
	def get_vbox(self):
		"""returns the vbox of this thread"""
		return self.mainVBox
	#end def get_vbox
	
	def showClicked(self, widget, data):
		name=self.nameTBuffer.get_text(self.nameTBuffer.get_start_iter(), self.nameTBuffer.get_end_iter())
		
		self.fig = Figure(figsize=(5,4), dpi=100)
		self.ax = self.fig.add_subplot(111)
#		x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
#		y = [2.7, 2.8, 31.4, 38.1, 58.0, 76.2, 100.5, 130.0, 149.3, 180.0]

		#self.db.reconnect()

		self.cursor.execute("SELECT handId, winnings FROM HandsPlayers INNER JOIN Players ON HandsPlayers.playerId = Players.id WHERE Players.name = %s ORDER BY handId", (name, ))

		self.results = self.db.cursor.fetchall()

#		x=map(lambda x:float(x[0]),self.results)
		y=map(lambda x:float(x[1]),self.results)
		line = range(len(y))

		for i in range(len(y)):
			line[i] = y[i] + line[i-1]

		self.ax.plot(line,)

		self.canvas = FigureCanvas(self.fig)  # a gtk.DrawingArea
		self.mainVBox.pack_start(self.canvas)
		self.canvas.show()


	
	def __init__(self, db, settings, debug=True):
		"""Constructor for table_viewer"""
		self.debug=debug
		#print "start of table_viewer constructor"
		self.db=db
		self.cursor=db.cursor
		self.settings=settings
        
		self.mainVBox = gtk.VBox(False, 0)
		self.mainVBox.show()
		
		self.settingsHBox = gtk.HBox(False, 0)
		self.mainVBox.pack_start(self.settingsHBox, False, True, 0)
		self.settingsHBox.show()
		
		self.nameLabel = gtk.Label("Name of the player to be graphed:")
		self.settingsHBox.pack_start(self.nameLabel)
		self.nameLabel.show()
		
		self.nameTBuffer=gtk.TextBuffer()
		self.nameTBuffer.set_text("name")
		self.nameTView=gtk.TextView(self.nameTBuffer)
		self.settingsHBox.pack_start(self.nameTView)
		self.nameTView.show()
		
		self.showButton=gtk.Button("Show/Refresh")
		self.showButton.connect("clicked", self.showClicked, "show clicked")
		self.settingsHBox.add(self.showButton)
 		self.showButton.show()
		
	#end of GuiGraphViewer.__init__
