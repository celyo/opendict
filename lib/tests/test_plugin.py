# -*- coding: UTF-8 -*-
#
# OpenDict
# Copyright (c) 2003-2006 Martynas Jocius <martynas.jocius@idiles.com>
# Copyright (c) 2007 IDILES SYSTEMS, UAB <support@idiles.com>
#
# Unit Test for editor.py
#

"""
Unit tests for plugin.py
"""

import unittest
import os
import sys

sys.path.append('../..')

from lib import newplugin


class TestPluginInfo(unittest.TestCase):
    """PluginInfo test"""

    def test_getInfo(self):
        """PluginInfo should have correct attributes"""

        fd = open("data/plugin.xml")
        xmlData = fd.read()
        fd.close()

        info = newplugin.PluginInfo(xmlData)
        
        self.assertEqual(info.name, "Sample plugin name ąčę")
        self.assertEqual(info.version, "1.2.3")
        self.assertEqual(info.authors, [{"name": "Sample author name ąčę",
                                "email": "sample@example.com"}])
        self.assertEqual(info.module, {"name": "mymodule.py",
                                        "lang": "Python"})
        self.assertEqual(info.encoding, "UTF-8")
        self.assertEqual(info.usesWordList, True)
        self.assertEqual(info.opendictVersion, "0.5.8")
        self.assertEqual(info.pythonVersion, "2.3")

        platforms =  [{"name": "Linux"},
                                 {"name": "Windows"},
                                 {"name": "BSD"}]
        platforms.sort()
        self.assertEqual(info.platforms, platforms)
        self.assertEqual(info.description,
                          "This is short or long description ąčę.")
        self.assertEqual(info.xmlData, xmlData)


class TestDictionaryPlugin(unittest.TestCase):
    """Test PluginHandler class"""

    def test_class(self):
        """__init__ should load plugin info and module"""
        
        p = newplugin.DictionaryPlugin(os.path.realpath('data/sampleplugin'))

        self.assertEqual(p.__class__, newplugin.DictionaryPlugin)
        self.assertTrue(p.info != None)
        self.assertTrue(p.dictionary != None)
        self.assertTrue(p.isValid() == True)
        self.assertEqual(p.info.__class__, newplugin.PluginInfo)
        self.assertEqual(len(p.dictionary.search('x').words), 20)

        self.assertRaises(newplugin.InvalidPluginException,
                          newplugin.DictionaryPlugin, 'blabla')
                                        



if __name__ == "__main__":
    unittest.main()
