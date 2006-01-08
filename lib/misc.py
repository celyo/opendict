# OpenDict
# Copyright (c) 2003 Martynas Jocius <mjoc@delfi.lt>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your opinion) any later version.
#
# This program is distributed in the hope that will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MECHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more detals.
#
# You shoud have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# 02111-1307 USA
#
# Module: misc

from wxPython.wx import wxGetTranslation, wxGetApp
from os.path import *
import string
import traceback
import sys
import os

_ = wxGetTranslation


#
# FIXME: Remove
#
errors = {1: _("Not found"),
          2: _("Dictionary error, please report to its author"),
          3: _("Syntax error"),
          4: _("You must be connected to the internet to use this dictionary"), #4: _("Connection error"),
          5: _("Time out"),
          6: _("Bad encoding is set for this dictionary, try another")}


#
# Character Encodings
#
encodings = {"Unicode (UTF-8)": "UTF-8",
             "Western (ISO-8859-1)": "ISO-8859-1",
             "Central European (ISO-8859-2)": "ISO-8859-2",
             "Nordic (ISO-8859-10)": "ISO-8859-10",
             "South European (ISO-8859-3)": "ISO-8859-3",
             "Greek (ISO-8859-7)": "ISO-8859-7",
             "Baltic (ISO-8859-13)": "ISO-8859-13",
             "Cyrillic (KOI8-R)": "KOI8-R",
             "Arabic (ISO-8859-6)": "ISO-8859-6"}

#
# Font faces
#
fontFaces = {"Fixed": "fixed",
             "Helvetica": "helvetica",
             "Courier": "courier",
             "Times": "Times",
             "Verdana": "Verdana",
             "Lucida": "Lucida"}


#fontSizes = ["1", "2", "3", "4", "6", "8", "10", "12"]


#dictFormats = {"dwa": "Slowo",
#               "mova": "Mova",
#               "tmx": "TMX",
#               "dz": "DICT",
#               "dict": "DICT",
#               "zip": _("OpenDict plugin")}

def numVersion(str):
    """Return a float number made from x.y.z[-preV] version number"""

    nver = str.split('-')[0]
    numbers = nver.split('.')
    try:
        return (float(numbers[0]) + float(numbers[1]) * 0.1 + float(number[2]) * 0.01)
    except:
        return 0.0

def printError():
    print string.join(traceback.format_exception(sys.exc_info()[0],
                                                 sys.exc_info()[1],
                                                 sys.exc_info()[2]), "")


def getTraceback():
    return string.join(traceback.format_exception(sys.exc_info()[0],
                                                 sys.exc_info()[1],
                                                 sys.exc_info()[2]), "")



def getFileSize(path):
    """Returns the size of file in bytes"""
    
    size = -1
    
    try:
        size = os.stat(path)[6]
    except:
        print "ERROR (misc.getFileSize): path '%s' does not exist" % path
    
    return size


def getDirSize(start, followLinks, myDepth, maxDepth):
    """Return total directory size"""
    
    total = 0L
    try:
        dirList = os.listdir(start)
    except:
        if isdir(start):
            print 'ERROR: Cannot list directory %s' % start
        return 0
    
    for item in dirList:
        path = '%s/%s' % (start, item)
        try:
            stats = os.stat(path)
        except:
            print 'ERROR: Cannot stat %s' % path
            continue
        
        total += stats[6]
        if isdir(path) and (followLinks or \
                             (not followLinks and not islink(path))):
            bytes = getDirSize(path, followLinks,
                               myDepth + 1,
                               maxDepth)
            total += bytes

    return total
    
