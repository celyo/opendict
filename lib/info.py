# OpenDict
#
# OpenDict
# Copyright (c) 2003-20045Martynas Jocius <mjoc@akl.lt>
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

import sys
import os

# OpenDict version
VERSION = "0.5.7-CVS"

# File system objects
__OPENDICT_LOCAL_DIR = ".opendict"

__DICT_DIR = "dictionaries"
__PLUGIN_DICT_DIR = "plugins" # plugin dictionaries
__FILE_DICT_DIR = "plain" # used for downloaded dictionaries
__FILE_DICT_CONFIG_DIR = "conf"
__FILE_DICT_FILES_DIR = "file"
__FILE_DICT_DATA_DIR = "data"

GLOBAL_HOME = None
LOCAL_HOME = None
      
if sys.platform == "win32":
   import _winreg
   x = _winreg.ConnectRegistry(None, _winreg.HKEY_CURRENT_USER)
   try:
      y = _winreg.OpenKey(x, "SOFTWARE\OpenDict\Settings")
      GLOBAL_HOME = _winreg.QueryValueEx(y, "Path")[0]
   except:
      GLOBAL_HOME = "C:\\Program Files\\OpenDict"
      
   LOCAL_HOME = GLOBAL_HOME

else:
   if not os.path.exists(os.path.join(os.environ.get("HOME"),
                                      __OPENDICT_LOCAL_DIR)):
      os.mkdir(os.environ.get("HOME"), __OPENDICT_LOCAL_DIR)
      
   LOCAL_HOME = os.path.join(os.environ.get("HOME"), __OPENDICT_LOCAL_DIR)
   GLOBAL_HOME = "/usr/share/opendict"
