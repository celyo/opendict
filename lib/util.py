#
# OpenDict
# Copyright (c) 2003-2005 Martynas Jocius <mjoc@akl.lt>
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

"""
Utility functions
"""

import os
import md5
import threading
import time
import urllib2
import traceback

import info
from logger import systemLog, debugLog, DEBUG, INFO, WARNING, ERROR


class UniqueIdGenerator:
    """Unique ID generator (using singleton design pattern)"""


    class _RealGenerator:
        """Unique ID generator"""

        def __init__(self, start=0):
            """Set starting ID value"""
            
            self.id = start
            
            
        def getID(self):
            """Return unique ID"""
            
            self.id += 1
            return self.id

    
    __instance = None


    def __init__(self, start=0):
        """Create new instance if not exists yet"""

        if UniqueIdGenerator.__instance is None:
            UniqueIdGenerator.__instance = self._RealGenerator(start)


    def getID(self):
        """Return unique ID"""

        return self.__instance.getID()


def generateUniqueID():
    """Helper function for getting unique ID"""

    gen = UniqueIdGenerator(7000)
    return gen.getID()


def getMD5Sum(filePath):
    """Return MD5 checksum for given file"""


    fd = open(filePath)
    data = fd.read()
    fd.close()

    generator = md5.new(data)

    return generator.hexdigest()


def makeDirectories():
    """Make needed directories if not exist"""

    

    plainDir = os.path.join(info.LOCAL_HOME,
                            info.PLAIN_DICT_DIR)
    pluginDir = os.path.join(info.LOCAL_HOME,
                             info.PLUGIN_DICT_DIR)


    if not os.path.exists(info.LOCAL_HOME):
        try:
            systemLog(DEBUG, "%s does not exist, creating..." \
                      % info.LOCAL_HOME)
            os.mkdir(info.LOCAL_HOME)
        except Exception, e:
            systemLog(ERROR, "Unable to create %s (%s)" % (info.LOCAL_HOME, e))

    if not os.path.exists(os.path.join(info.LOCAL_HOME, info.__DICT_DIR)):
        try:
            systemLog(DEBUG, "%s does not exist, creating..." \
                  % os.path.join(info.LOCAL_HOME, info.__DICT_DIR))
            os.mkdir(os.path.join(info.LOCAL_HOME, info.__DICT_DIR))
        except Exception, e:
            systemLog(ERROR, "Unable to create %s (%s)" \
                  % (os.path.join(info.LOCAL_HOME, info.__DICT_DIR), e))

    if not os.path.exists(plainDir):
        try:
            systemLog(DEBUG, "%s does not exist, creating..." % plainDir)
            os.mkdir(plainDir)
        except Exception, e:
            systemLog(ERROR, "Unable to create %s (%s)" % (plainDir, e))

    
    if not os.path.exists(pluginDir):
        try:
            print "DEBUG %s does not exist, creating..." % pluginDir
            os.mkdir(pluginDir)
        except Exception, e:
            print "ERROR Unable to create %s (%s)" % (pluginDir, e)



class DownloadThread:
    """Non-blocking download thread
    
    Can be used to connect and download files from the Internet.
    """

    def __init__(self, url):
        """Initialize variables"""

        self.url = url
        self.thread = threading.Thread(target=self.worker)
        self.thread.setDaemon(True) # Daemonize for fast exiting
        self.statusMessage = ''
        self.errorMessage = None
        self.percents = 0
        self.stopRequested = False
        self.done = False
        self.buffer = ''


    def start(self):
        """Start thread"""

        self.thread.start()


    def stop(self):
        """Request thread to stop, may hang for some time"""

        self.stopRequested = True


    def getMessage(self):
        """Return status message"""

        return self.statusMessage


    def getErrorMessage(self):
        """Return error message"""

        return self.errorMessage


    def getPercentage(self):
        """Return percentage"""

        return self.percents


    def finished(self):
        """Return True if finished, False otherwise"""

        return self.done


    def getBytes(self):
        """Return buffered bytes and clear the buffer"""

        bytes = self.buffer
        self.buffer = ''

        return bytes


    def worker(self):
        """Main worker method"""

        try:
            serverName = '/'.join(self.url.split('/')[:3])
        except:
            serverName = self.url

        try:
            self.statusMessage = "Connecting to %s..." % serverName
            self.up = urllib2.urlopen(self.url)
            fileSize = int(self.up.info().getheader('Content-length'))
        except Exception, e:
            self.errorMessage = "Unable to connect to %s" % serverName
            self.done = True
            return

        count = 0

        try:
            while not self.stopRequested and count < fileSize:
                self.statusMessage = "Downloading data from %s" \
                                     % (self.url)
                bytes = self.up.read(1024)
                count += len(bytes)
                self.buffer += bytes
                self.percents = int(float(count) / fileSize * 100)
                time.sleep(0.005) # To lower CPU usage
                
            self.up.close()
            self.done = True
        except Exception, e:
            self.errorMessage = "Error while fetching data from %s: %s" \
                                % (self.url, e)
            self.done =  True



class AgreementsManager:
    """Manages information about licence agreements for dictionaries"""

    def __init__(self, filePath):
        """Initialize variables"""

        self.filePath = filePath
        self.dictPaths = []

        self._load()


    def addAgreement(self, dictConfigPath):
        """Mark dictionary licence as accepted"""

        if not dictConfigPath in self.dictPaths:
            self.dictPaths.append(dictConfigPath)
            self._updateFile()


    def removeAgreement(self, dictConfigPath):
        """Mark dictionary licence as rejected,
        i.e. remove from accepted list"""

        if dictConfigPath in self.dictPaths:
            self.dictPaths.remove(dictConfigPath)
            self._updateFile()


    def getAccepted(self, dictConfigPath):
        """Return True if dictionary licence is marked as accepted"""

        if dictConfigPath in self.dictPaths:
            return True
        else:
            return False


    def _load(self):
        """Read data from file"""

        try:
            fd = open(self.filePath)
            for line in fd:
                self.dictPaths.append(line.strip())
            fd.close()
        except:
            pass


    def _updateFile(self):
        """Write changes to file"""

        fd = open(self.filePath, 'w')
        for path in self.dictPaths:
            print >> fd, path
        fd.close()
