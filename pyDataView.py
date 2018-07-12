#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# ========================== pyDataViewer ========================== 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import wx
import sys
import postproclib.visualiser as pplv
import argparse

def run_visualiser(parent_parser=argparse.ArgumentParser(add_help=False)):

    #Keyword arguments
    parser = argparse.ArgumentParser(
                           description="""
                           Runs visualiser XXXX where XXXX is an 
                           increasingly more futuristic and exciting number""",
                           parents=[parent_parser])

    parser.add_argument('-d', '--fdir', dest='fdir', 
                        help='Directory containing results', 
                        default='./')

    args = vars(parser.parse_args())

    app = wx.App()
    fr = pplv.MainFrame(None, fdir=args['fdir'])
    fr.Show()
    app.MainLoop()

if __name__ == "__main__":

    run_visualiser()
