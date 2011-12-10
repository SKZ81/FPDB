#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Aux_Hud.py

Simple HUD display for FreePokerTools/fpdb HUD.
"""
#    Copyright 2011,  Ray E. Barker
#    
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

########################################################################

#    to do

#    Standard Library modules

#    pyGTK modules
import gtk
import gobject
import pango

#    FreePokerTools modules
import Mucked
import Stats
import Popup

class Stat_Window(Mucked.Seat_Window):
    """Simple window class for stat windows."""

    def create_contents(self, i):
        self.grid = gtk.Table(rows = self.aw.nrows, columns = self.aw.ncols, homogeneous = False)
        self.add(self.grid)
        self.grid.modify_bg(gtk.STATE_NORMAL, self.aw.bgcolor)
        self.modify_bg(gtk.STATE_NORMAL, self.aw.bgcolor)

        self.stat_box = [ [None]*self.aw.ncols for i in range(self.aw.nrows) ]

        for r in xrange(self.aw.nrows):
            for c in xrange(self.aw.ncols):
                self.stat_box[r][c] = Simple_stat(self.aw.stats[r][c], 
                                                seat = self.seat, 
                                                popup = self.aw.popups[r][c], 
                                                game_stat_config = self.aw.config.supported_games[self.aw.poker_game].stats[self.aw.stats[r][c]],
                                                aw = self.aw)
                self.grid.attach(self.stat_box[r][c].widget, c, c+1, r, r+1, xpadding = self.aw.xpad, ypadding = self.aw.ypad)
                self.stat_box[r][c].set_color(self.aw.fgcolor, self.aw.bgcolor)
                self.stat_box[r][c].set_font(self.aw.font)
                self.stat_box[r][c].widget.connect("button_press_event", self.button_press_cb)

    def update_contents(self, i):
        if i == "common": return
        player_id = self.aw.get_id_from_seat(i)
        if player_id is None: return
        for r in xrange(self.aw.nrows):
            for c in xrange(self.aw.ncols):
                self.stat_box[r][c].update(player_id, self.aw.hud.stat_dict)

class Simple_HUD(Mucked.Aux_Seats):
    """A simple HUD class based on the Aux_Window interface."""

    def __init__(self, hud, config, params):
        super(Simple_HUD, self).__init__(hud, config, params)
#    Save everything you need to know about the hud as attrs.
#    That way a subclass doesn't have to grab them.
#    Also, the subclass can override any of these attributes
        self.poker_game  = self.hud.poker_game
        self.game_params = self.hud.config.get_game_parameters(self.hud.poker_game)
        self.game        = self.hud.config.supported_games[self.hud.poker_game]
        self.max         = self.hud.max
        self.nrows       = self.game_params['rows']
        self.ncols       = self.game_params['cols']
        self.xpad        = self.game_params['xpad']
        self.ypad        = self.game_params['ypad']
        self.xshift      = self.game_params['xshift']
        self.yshift      = self.game_params['yshift']

        self.fgcolor   = gtk.gdk.color_parse(params["fgcolor"])
        self.bgcolor   = gtk.gdk.color_parse(params["bgcolor"])
        self.opacity   = params["opacity"]
        self.font      = pango.FontDescription("%s %s" % (params["font"], params["font_size"]))
        #todo - checkout what these two commands are doing, exactly
        self.aw_window_type = Stat_Window
        self.aw_mw_type = Simple_table_mw

#    layout is handled by superclass!
#    retrieve the contents of the game element for future use
#    do this here so that subclasses don't have to bother
        self.stats  = [ [None]*self.ncols for i in range(self.nrows) ]
        self.popups = [ [None]*self.ncols for i in range(self.nrows) ]
        self.tips   = [ [None]*self.ncols for i in range(self.nrows) ]
        for stat in self.game.stats:
            self.stats[self.config.supported_games[self.poker_game].stats[stat].row] \
                      [self.config.supported_games[self.poker_game].stats[stat].col] = \
                      self.config.supported_games[self.poker_game].stats[stat].stat_name

            self.popups[self.config.supported_games[self.poker_game].stats[stat].row] \
                      [self.config.supported_games[self.poker_game].stats[stat].col] = \
                      self.config.supported_games[self.poker_game].stats[stat].popup
#                       Popup.__dict__.get(self.config.supported_games[self.poker_game].stats[stat].popup, "default")
                 
            self.tips[self.config.supported_games[self.poker_game].stats[stat].row] \
                      [self.config.supported_games[self.poker_game].stats[stat].col] = \
                      self.config.supported_games[self.poker_game].stats[stat].tip

    def create_contents(self, container, i):
        container.create_contents(i)

    def update_contents(self, container, i):
        container.update_contents(i)

    def create_common(self, x, y):
        return self.aw_mw_type(self.hud, aw = self)
#        return Simple_table_mw(self.hud, aw = self)

class Simple_stat(object):
    """A simple class for displaying a single stat."""
    def __init__(self, stat, seat, popup, game_stat_config=None, aw=None):
        self.stat = stat
        self.eb = Simple_eb();
        self.eb.aw_seat = seat
        self.eb.aw_popup = popup
        self.eb.stat_dict = None
        self.lab = Simple_label("xxx") # xxx is used as initial value because label does't shrink
        self.eb.add(self.lab)
        self.widget = self.eb
        self.stat_dict = None

    def update(self, player_id, stat_dict):
        self.stat_dict = stat_dict     # So the Simple_stat obj always has a fresh stat_dict
        self.eb.stat_dict = stat_dict
        self.number = Stats.do_stat(stat_dict, player_id, self.stat)
        self.lab.set_text( str(self.number[1]))

    def set_color(self, fg=None, bg=None):
        if fg:
            self.eb.modify_fg(gtk.STATE_NORMAL, fg)
            self.lab.modify_fg(gtk.STATE_NORMAL, fg)
        if bg:
            self.eb.modify_bg(gtk.STATE_NORMAL, bg)
            self.lab.modify_bg(gtk.STATE_NORMAL, bg)

    def set_font(self, font):
        self.lab.modify_font(font)

#    Override thise methods to customize your eb or label
class Simple_eb(gtk.EventBox): pass
class Simple_label(gtk.Label): pass

class Simple_table_mw(Mucked.Seat_Window):
    """Create a default table hud main window with a menu."""
#    This is a recreation of the table main windeow from the default HUD
#    in the old Hud.py. This has the menu options from that hud. 

#    BTW: It might be better to do this with a different AW.

    def __init__(self, hud, aw = None):
        #### FIXME: (Gimick)
        #### I had to replace super() call with direct call to __init__
        #### Needed for the moment because Classic_hud can't patch MRO for 
        #### table_mw class.  Get a wierd recursion level exceeded message
        Mucked.Seat_Window.__init__(self, aw)
        #####super(Simple_table_mw, self).__init__(aw)
        self.hud = hud
#        self.set_skip_taskbar_hint(True)  # invisible to taskbar
#        self.set_gravity(gtk.gdk.GRAVITY_STATIC)
#        self.set_decorated(False)    # kill titlebars
#        self.set_focus(None)
#        self.set_focus_on_map(False)
#        self.set_accept_focus(False)
        self.connect("configure_event", self.aw.configure_event_cb, "common")

        eb = gtk.EventBox()
        try: lab=gtk.Label(self.menu_label)
        except: lab=gtk.Label("defmenu")

        eb.modify_bg(gtk.STATE_NORMAL, self.aw.bgcolor)
        eb.modify_fg(gtk.STATE_NORMAL, self.aw.fgcolor)
        lab.modify_bg(gtk.STATE_NORMAL, self.aw.bgcolor)
        lab.modify_fg(gtk.STATE_NORMAL, self.aw.fgcolor)

        self.add(eb)
        eb.add(lab)

        self.menu = gtk.Menu()
        self.create_menu_items(self.menu)
        eb.connect_object("button-press-event", self.button_press_cb, self.menu)

        (x, y) = self.aw.params['layout'][self.hud.max].common
        self.move(x + self.hud.table.x, y + self.hud.table.y)
        self.menu.show_all()
        self.show_all()
        self.hud.table.topify(self)

    def create_menu_items(self, menu):
        #a gtk.menu item is passed in and returned
        
        menu_item_build_list = ( ('Kill This HUD', self.kill),
                        ('Save HUD Layout', self.save_current_layouts), 
                        ('Show Player Stats', None) )
        
        for item, cb in menu_item_build_list:
            this_item = gtk.MenuItem(item)
            menu.append(this_item)
            if cb is not None:
                this_item.connect("activate", cb)
                     
        return menu
                     
    def button_press_cb(self, widget, event, *args):
        """Handle button clicks in the main window event box."""

        if event.button == 3:   # right button event does nothing for now
            widget.popup(None, None, None, event.button, event.time)
 
#    button 2 is not handled here because it is the pupup window

        elif event.button == 1:   # left button event -- drag the window
            try:
                self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
            except AttributeError:  # in case get_ancestor returns None
                pass
            return True
        return False

    def create_contents(self, *args):
        pass
    def update_contents(self, *args):
        pass

    def save_current_layouts(self, event):
#    This calls the save_layout method of the Hud object. The Hud object 
#    then calls the save_layout method in each installed AW.
        self.hud.save_layout()

    def kill(self, event):
        self.hud.parent.kill_hud(event, self.hud.table.key)
