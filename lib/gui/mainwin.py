#
# OpenDict
# Copyright (c) 2003-2005 Martynas Jocius <mjoc at akl.lt>
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
Main window GUI module
"""

from wxPython.wx import *
from wxPython.html import *
import wxPython
import os
import cStringIO
import traceback

from lib import info
from lib.gui.dictconnwin import DictConnWindow
from lib.gui.pluginwin import PluginManagerWindow
from lib.gui.dicteditorwin import DictEditorWindow
from lib.gui.dictaddwin import DictAddWindow
from lib.gui.prefswin import PrefsWindow
from lib.gui.helpwin import LicenseWindow, AboutWindow
from lib.gui import errorwin
from lib.gui import miscwin
from lib.parser import SlowoParser
from lib.parser import MovaParser
from lib.parser import TMXParser
from lib.parser import DictParser
from lib.threads import Process
from lib.history import History
from lib.installer import Installer
from lib.extra.html2text import html2text
from lib.logger import systemLog, debugLog, DEBUG, INFO, WARNING, ERROR
from lib import misc
from lib import info
from lib import util
from lib import meta
from lib import enc
from lib import errortype
from lib import dicttype
from lib import plaindict

_ = wxGetTranslation

# Constants
titleTemplate = "OpenDict - %s"
NORMAL_FONT_SIZE = '10'

# Used to remember word when searching by entering text to the entry,
# selecting one from the list or clicking a link.
lastLookupWord = None


class HtmlWindow(wxHtmlWindow):

   """Html control for showing transaltion and catching
   link-clicking"""

   def OnLinkClicked(self, linkInfo):

      global lastLookupWord
      lastLookupWord = linkInfo.GetHref()
      debugLog(DEBUG, "LinkInfo: searching for '%s'" % lastLookupWord)
      wxBeginBusyCursor()
      parent = self.GetParent().GetParent().GetParent()
      parent.SetStatusText(_("Searching..."))
      parent.timerSearch.Start(parent.delay)
      parent.search = Process(parent.activeDictionary.search,
                              lastLookupWord)

      

class MainWindow(wxFrame):

   """Main OpenDict window with basic controls"""

   def __init__(self, parent, id, title, pos=wxDefaultPosition,
                size=wxDefaultSize, style=wxDEFAULT_FRAME_STYLE):
      wxFrame.__init__(self, parent, id, title, pos, size, style)

      self.app = wxGetApp()
      self.printer = wxHtmlEasyPrinting()
      self.history = History()
      self.htmlCode = ""
      self.dictName = ""
      self.activeDictionary = None
      self.words = []
      self.delay = 10 # miliseconds
      
      self.lastInstalledDictName = None

      # This var is used by onTimerSearch to recognize search method.
      # If search was done by selecting a word in a list, then word list
      # is not updated, otherwise is.
      self.__searchedBySelecting = 0

      # Box sizers
      vboxMain = wxBoxSizer(wxVERTICAL)
      self.hboxToolbar = wxBoxSizer(wxHORIZONTAL)

      #
      # Menu Bar
      #
      self.menuBar = wxMenuBar()

      #
      # File menu
      #
      menuFile = wxMenu()

      idPrint = wx.NewId()
      #menuFile.Append(idPrint, _("Print Translation"), "")

      idPreview = wx.NewId()
      #menuFile.Append(idPreview, _("Print Preview"), "")

      idFind = wx.NewId()
      menuFile.Append(idFind, _("Look Up\tCtrl-U"),
                      _("Lookup up word in the dictionary"))
      
      menuFile.AppendSeparator()

      idCloseDict = wx.NewId()
      menuFile.Append(idCloseDict, _("&Close\tCtrl-W"),
                      _("Close opened dicitonary"))

      idExit = wx.NewId()
      menuFile.Append(idExit, _("E&xit\tCtrl-Q"),
                      _("Exit program"))

      self.menuBar.Append(menuFile, _("&File"))

      menuEdit = wxMenu()

      #
      # Clear functions
      #
      idClearEntry = wx.NewId()
      menuEdit.Append(idClearEntry, _("&Clear Search Entry\tCtrl-L"))

      idClearHistory = wx.NewId()
      menuEdit.Append(idClearHistory, _("Clear History"))

      menuEdit.AppendSeparator()

      #
      # Clipboard functions
      #
      idCopy = wx.NewId()
      menuEdit.Append(idCopy, _("Copy\tCtrl-C"),
                      _("Copy selected translation text"))

      idPaste = wx.NewId()
      menuEdit.Append(idPaste, _("Paste\tCtrl-V"),
                      _("Paste clipboard text into the search entry"))
      
      menuEdit.AppendSeparator()

      idPrefs = wx.NewId()
      menuEdit.Append(idPrefs, _("Preferences...\tCtrl-P"), _("Edit preferences"))

      self.menuBar.Append(menuEdit, _("&Edit"))


      #
      # View menu
      #      
      menuView = wxMenu()

      # Font size
      self.menuFontSize = wxMenu()
      self.menuFontSize.Append(2007, _("Increase\tCtrl-="),
                               _("Increase text size"))
      self.menuFontSize.Append(2008, _("Decrease\tCtrl--"),
                               _("Decrease text size"))
      self.menuFontSize.AppendSeparator()
      self.menuFontSize.Append(2009, _("Normal\tCtrl-0"),
                               _("Set normal text size"))
      menuView.AppendMenu(2002, _("Font Size"), self.menuFontSize)
      

      # Font face
      self.menuFontFace = wxMenu()
      i = 0
      keys = misc.fontFaces.keys()
      keys.sort()
      
      for face in keys:
         self.menuFontFace.AppendRadioItem(2500+i, face, "")
         EVT_MENU(self, 2500+i, self.onDefault)
         if self.app.config.get('fontFace') == misc.fontFaces[face]:
            self.menuFontFace.FindItemById(2500+i).Check(1)
         i+=1
         
      menuView.AppendMenu(2001, _("Font Face"), self.menuFontFace)
      

      # Font encoding
      self.menuEncodings = wxMenu()
      i = 0
      keys = misc.encodings.keys()
      keys.sort()
      for encoding in keys:
         self.menuEncodings.AppendRadioItem(2100+i , encoding, "")
         EVT_MENU(self, 2100+i, self.onDefault)
         if self.app.config.get('encoding') == misc.encodings[encoding]:
            self.menuEncodings.FindItemById(2100+i).Check(1)
         i+=1
         
      menuView.AppendMenu(2000, _("Character Encoding"), self.menuEncodings)

      self.menuBar.Append(menuView, _("&View"))

      
      #
      # Dictionaries menu
      #
      self.menuDict = wxMenu()

      dictNames = []
      for dictionary in self.app.dictionaries.values():
         dictNames.append(dictionary.getName())
      dictNames.sort()
      
      for name in dictNames:
         encoded = enc.toWX(name)

         itemID = self.app.config.ids.keys()[\
            self.app.config.ids.values().index(name)]

         try:
            item = wxMenuItem(self.menuDict,
                              itemID,
                              encoded)
            self.menuDict.AppendItem(item)
            EVT_MENU(self, itemID, self.onDefault)
         except Exception, e:
            systemLog(ERROR, "Unable to create menu item for '%s' (%s)" \
                  % (name, e))

      self.menuDict.AppendSeparator()

      idAddDict = wx.NewId()
      self.menuDict.Append(idAddDict, _("&Install Dictionary From File..."))
      
      self.menuBar.Append(self.menuDict, _("&Dictionaries"))


      #
      # Tools menu
      #
      menuTools = wxMenu()

      idManageDict = wx.NewId()
      menuTools.Append(idManageDict, _("Manage Dictionaries...\tCtrl-M"),
                      _("Install or remove dictionaries"))

      menuTools.AppendSeparator()

      idUseScan = wx.NewId()
      menuTools.Append(idUseScan, _("Scan Clipboard For Words"),
                       _("Scan the clipboard for text to translate"),
                       wx.ITEM_CHECK)

      menuTools.AppendSeparator()

      idDictServer = wx.NewId()
      menuTools.Append(idDictServer, _("Connect to DICT Server..."),
                          _("Open connection to DICT server"))

      menuTools.AppendSeparator()
      
      menuTools.Append(5002, _("Edit Dictionaries..."),
                       _("Create and edit dictionaries"))  
                           
      self.menuBar.Append(menuTools, _("Tools"))


      #
      # Help menu
      #
      menuHelp = wxMenu()

      idLicence = wx.NewId()
      menuHelp.Append(idLicence, _("&License"))
      
      menuHelp.AppendSeparator()
      
      idAbout = wx.NewId()
      menuHelp.Append(idAbout, _("&About\tCtrl-A"))

      self.menuBar.Append(menuHelp, _("&Help"))

      self.SetMenuBar(self.menuBar)

      # Search Bar
      labelWord = wxStaticText(self, -1, _("Word:"));
      self.hboxToolbar.Add(labelWord, 0, wxALL | wxCENTER | wx.ALIGN_RIGHT, 5)
      
      self.entry = wxComboBox(self, 153, "", wxPoint(-1, -1),
                              wxSize(-1, -1), [], wxCB_DROPDOWN)
      self.entry.SetToolTipString(_("Enter some text and press " \
                                    "\"Look Up\" button or "
                                    "[ENTER] key on your keyboard"))
      self.hboxToolbar.Add(self.entry, 1, wxALL | wxCENTER, 1)

      #self.buttonSearch = wxButton(self, wx.ID_FIND)
      self.buttonSearch = wxButton(self, idFind, _("Look Up"))
      self.buttonSearch.SetToolTipString(_("Click this button to look " \
                                           "up word in " \
                                           "the dictionary"))
      
      self.hboxToolbar.Add(self.buttonSearch, 0, wxALL | wxCENTER, 1)

      # Back button
      bmp = wxBitmap(os.path.join(info.GLOBAL_HOME, "pixmaps", "left.png"),
                     wxBITMAP_TYPE_PNG)
      self.buttonBack = wxBitmapButton(self, 2010, bmp, (24, 24),
                                         style=wxNO_BORDER)
      self.buttonBack.SetToolTipString(_("History Back"))
      self.buttonBack.Disable()
      self.hboxToolbar.Add(self.buttonBack, 0, wxALL | wxCENTER, 1)

      # Forward button
      bmp = wxBitmap(os.path.join(info.GLOBAL_HOME, "pixmaps", "right.png"),
                     wxBITMAP_TYPE_PNG)
      self.buttonForward = wxBitmapButton(self, 2011, bmp, (24, 24),
                                         style=wxNO_BORDER)
      self.buttonForward.SetToolTipString(_("History Forward"))
      self.buttonForward.Disable()
      self.hboxToolbar.Add(self.buttonForward, 0, wxALL | wxCENTER, 1)

      # Stop threads
      # TODO: how thread can be killed?
      bmp = wxBitmap(os.path.join(info.GLOBAL_HOME, "pixmaps", "stop.png"),
                     wxBITMAP_TYPE_PNG)
      self.buttonStop = wxBitmapButton(self, 155, bmp, (16, 16),
                                       style=wxNO_BORDER)
      self.buttonStop.SetToolTipString(_("Stop searching"))
      self.buttonStop.Disable()
      self.hboxToolbar.Add(self.buttonStop, 0, wxALL | wxCENTER, 1)

      # Word list is hidden by default
      self.wlHidden = True
      
      bmp = wxBitmap(os.path.join(info.GLOBAL_HOME, "pixmaps", "hide.png"),
                     wxBITMAP_TYPE_PNG)
      self.buttonHide = wxBitmapButton(self, 152, bmp, (24, 24),
                                       style=wxNO_BORDER)
      self.hboxToolbar.Add(self.buttonHide, 0, wxALL | wxCENTER, 1)

      vboxMain.Add(self.hboxToolbar, 0, wxALL | wxEXPAND | wxGROW, 0)

      # Splitter Window
      self.splitter = wxSplitterWindow(self, -1)

      # List panel
      self.createListPanel()
      
      # Html window panel
      self.panelHtml = wxPanel(self.splitter, -1)
      sbSizerHtml = wxStaticBoxSizer(wxStaticBox(self.panelHtml, -1, 
                                                 _("Translation")),
                                     wxVERTICAL)
      self.htmlWin = HtmlWindow(self.panelHtml, -1, style=wxSUNKEN_BORDER)
      sbSizerHtml.Add(self.htmlWin, 1, wxALL | wxEXPAND, 0)
      self.panelHtml.SetSizer(sbSizerHtml)
      self.panelHtml.SetAutoLayout(true)
      sbSizerHtml.Fit(self.panelHtml)

      self.splitter.SplitVertically(self.panelList, self.panelHtml,
                                    int(self.app.config.get('sashPos')))
         
      self.splitter.SetMinimumPaneSize(90)
      self.splitter.SetSashSize(5)

      if not self.activeDictionary:
         self.hideWordList()

      vboxMain.Add(self.splitter, 1, wxALL | wxGROW | wxEXPAND, 0)

      # Status bar
      self.CreateStatusBar()

      # Main sizer
      self.SetSizer(vboxMain)

      self.timerSearch = wxTimer(self, 5000)
      self.timerLoad = wxTimer(self, 5001)

      idClipboard = wx.NewId()
      self.timerClipboard = wxTimer(self, idClipboard)
      self.scanTimeout = 2000
      
      self.search = None
      self.load = None

      wxInitAllImageHandlers()      
      self.SetIcon(wxIcon(os.path.join(info.GLOBAL_HOME,
                                       "pixmaps",
                                       "icon-32x32.png"),
                          wxBITMAP_TYPE_PNG))


      #
      # Loading default dictionary
      #
      if self.app.config.get('defaultDict'):
         self.loadDictionary(self.app.dictionaries.get(\
            self.app.config.get('defaultDict')))


      self.SetMinSize((320, 160))


      #
      # Events
      #
      # TODO: New-style event definition

      # File menu events
      EVT_MENU(self, idPrint, self.onPrint)
      EVT_MENU(self, idPreview, self.onPreview)
      EVT_MENU(self, idCloseDict, self.onCloseDict)
      EVT_MENU(self, idExit, self.onExit)

      # Edit menu events
      EVT_MENU(self, idClearHistory, self.onClearHistory)
      EVT_MENU(self, idCopy, self.onCopy)
      EVT_MENU(self, idPaste, self.onPaste)
      EVT_MENU(self, idClearEntry, self.onClean)

      # View menu events
      EVT_MENU(self, 2007, self.onIncreaseFontSize)
      EVT_MENU(self, 2008, self.onDecreaseFontSize)
      EVT_MENU(self, 2009, self.onNormalFontSize)

      # Dictionaries menu events
      EVT_MENU(self, idAddDict, self.onAddDict)

      # Tools menu events
      EVT_MENU(self, idDictServer, self.onOpenDictConn)
      EVT_MENU(self, idUseScan, self.onUseScanClipboard)
      EVT_MENU(self, idManageDict, self.onShowPluginManager)
      EVT_MENU(self, 5002, self.onShowDictEditor)
      EVT_MENU(self, idPrefs, self.onShowPrefsWindow)

      # Help menu events
      EVT_MENU(self, idLicence, self.onLicence)
      EVT_MENU(self, idAbout, self.onAbout)

      # Other events
      self.Bind(wx.EVT_BUTTON, self.onSearch, self.buttonSearch)
      EVT_MENU(self, idFind, self.onSearch)
         
      EVT_BUTTON(self, 2010, self.onBack)
      EVT_BUTTON(self, 2011, self.onForward)
      EVT_BUTTON(self, 155, self.onStop)
      EVT_BUTTON(self, 151, self.onClean)
      EVT_BUTTON(self, 152, self.onHideUnhide)
      EVT_TEXT_ENTER(self, 153, self.onSearch)
      EVT_LISTBOX(self, 154, self.onWordSelected)
      EVT_TIMER(self, 5000, self.onTimerSearch)
      EVT_TIMER(self, idClipboard, self.onTimerClipboard)
      EVT_CLOSE(self, self.onCloseWindow)

      # Prepare help message
      self.htmlCode = _("""
<html>
<head>
<meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\">
</head>
<body>
<h3>Welcome to OpenDict</h3>
<p><b>Short usage information:</b></p>
<ul>
  <li>To start using dictionary, select one from <i><b>Dictionaries</b></i>
    menu.
  </li>
  <li>To install new dictionary from the Internet, select
    <i><b>Manage Dictionaries</b></i>
    from <i><b>Tools</b></i> menu and choose <i><b>Available</b></i> tab.</li>
  <li>To install new dictionary from file, select <i><b>Add New Dictionary</b></i>
  from <i><b>Dictionaries</b></i> menu.
  </li>
</ul>
</body>
</html>
""")

      if self.activeDictionary:
         self.htmlCode = ""

      self.updateHtmlScreen()


      if self.app.invalidDictionaries:
         title = _("Invalid Dictionaries")
         msg = _("The following dictionaries are invalid and cannot be " \
                 "loaded:\n\n%s\n\nThis may be because of critical changes "\
                 "in OpenDict archtecture. Remove listed directories by " \
                 "hand to avoid this message in the future" \
                 % '\n'.join(self.app.invalidDictionaries))
         from lib.gui import errorwin
         errorwin.showErrorMessage(title, msg)


   def onExit(self, event):

      self.onCloseWindow(None)


   def onCloseWindow(self, event):

      self.onCloseDict(None)
      self.savePreferences()
      self.Destroy()


   # TODO: Move aftersearch actions into separate method
   def onTimerSearch(self, event):
      """Search timer. When finished, sets search results"""
      
      if self.search != None and self.search.isDone():
         wxEndBusyCursor()
         self.timerSearch.Stop()
         self.search.stop()

         global lastLookupWord
         word = lastLookupWord

         if self.entry.FindString(word) == -1:
            self.entry.Append(word)
         
         result = self.search()

         # Check if search result is SerachResult object.
         # SearchResult class is used by new-type plugins.
         try:
            assert result.__class__ == meta.SearchResult
         except:
            self.SetStatusText(_(errortype.INTERNAL_ERROR.getMessage()))
            self.entry.Enable(1)
            self.buttonStop.Disable()
            self.entry.SetFocus()

            if self.activeDictionary.getType() == dicttype.PLUGIN:
               title = errortype.INTERNAL_ERROR.getMessage()
               message = errortype.INTERNAL_ERROR.getLongMessage()
            else:
               title = errortype.OPENDICT_BUG.getMessage()
               message = errortype.OPENDICT_BUG.getLongMessage()

            systemLog(ERROR, "%s: %s" % (message, misc.getTraceback()))
            errorwin.showErrorMessage(title, message)
            
            return

         self.SetStatusText("")
         self.entry.Enable(1)
         self.buttonStop.Disable()
         self.search = None

         # Check status code
         if result.getError() != errortype.OK:
            systemLog(ERROR, result.getError())
            
            self.htmlWin.SetPage("")
            self.wordList.Clear()

            if result.getError() in \
                   [errortype.INTERNAL_ERROR, errortype.INVALID_ENCODING]:
               errorwin.showErrorMessage(result.getError().getMessage(),
                                         result.getError().getLongMessage())
            else:
               self.SetStatusText(result.getError().getMessage())
               self.entry.Enable(1)
               self.entry.SetFocus()
               self.buttonStop.Disable()
               
            return


         #
         # If dictionary (plugin) does not use NOT_FOUND notification,
         # check for translation and show it manually
         #
         translation = result.getTranslation()
         if not translation:
            self.setStatusText(errortype.NOT_FOUND.getMessage())
            

         try:
            debugLog(DEBUG, "Decoding translation in %s" \
                  % self.activeDictionary.getEncoding())
            transUnicode = unicode(result.translation,
                                   self.activeDictionary.getEncoding())
         except Exception, e:
            systemLog(ERROR, "Unable to decode translation in %s (%s)" \
                      % (self.activeDictionary.getEncoding(),
                         e))
            title = _(errortype.INVALID_ENCODING.getMessage())
            msg = _("Translation cannot be displayed using selected " \
                    "encoding %s. Please try another encoding from " \
                    "View > Character Encoding menu." \
                    % self.activeDictionary.getEncoding())
            self.SetStatusText(title)
            errorwin.showErrorMessage(title, msg)
            return 
            
         transPreparedForWX = enc.toWX(transUnicode)

         self.htmlWin.SetPage(transPreparedForWX)
         self.history.add(transPreparedForWX)

         # FIXME: Nasty names
         # Where it is used? htmlWin.GetPage
         self.htmlCode = transPreparedForWX
         
         if not self.wordListHidden():
            if not self.__searchedBySelecting:
               self.wordList.Clear()

               toUnicode = lambda s: unicode(s,
                                             self.activeDictionary.getEncoding())
               wordsInUnicode = map(toUnicode, result.words)
               wordsPreparedForWX = map(enc.toWX, wordsInUnicode)
               
               self.wordList.InsertItems(wordsPreparedForWX, 0)
               self.words = wordsPreparedForWX

         if not self.__searchedBySelecting:
            matches = self.wordList.GetCount()
            if matches == 1:
               self.SetStatusText(_("1 word matches"))
            elif matches > 1:
               self.SetStatusText(_("%d words match") % matches)

         if self.history.canBack():
            self.buttonBack.Enable(1)
         self.buttonForward.Disable()
         self.entry.SetFocus()
         self.buttonStop.Disable()


   def onTimerClipboard(self, event):
      """Clipboard timer, used to watch new text in a clipboard"""

      def getText():
         do = wxTextDataObject()
         text = None
         wxTheClipboard.Open()
         if wxTheClipboard.GetData(do):
            try:
               text = do.GetText()
            except Exception, e:
               print e
         wxTheClipboard.Close()
         return enc.toWX(text)
      

      def clear():
         do = wxTextDataObject()
         do.SetText('')
         wxTheClipboard.Open()
         wxTheClipboard.SetData(do)
         wxTheClipboard.Close()

      text = getText()
      if text:
         self.entry.SetValue(text)
         self.onSearch(None)
         clear()


   def onUseScanClipboard(self, event):
      """Scan Clipboard menu item selected"""

      if event and event.GetInt():
         self.timerClipboard.Start(self.scanTimeout)
      else:
         self.timerClipboard.Stop()


   def onSearch(self, event):
      if self.activeDictionary == None:
         if len(self.app.dictionaries):
            title = _("No dictionary activated")
            msg = _("No dictionary activated. Please select one from "\
                 "\"Dictionaries\" menu and try again.")
         else:
            title = _("No dictionaries installed")
            msg = _("There is no dictionaries installed. You can " \
                      "install one by selecting Tools > Manage " \
                      "Dictionaries > Available")

         errorwin.showErrorMessage(title, msg)
         return

      word = self.entry.GetValue()

      if word == "":
         self.SetStatusText(_("Enter a word and try again"))
         self.entry.SetFocus()
         return

      global lastLookupWord
      lastLookupWord = word
      wxBeginBusyCursor()

      self.__searchedBySelecting = 0
      self.SetStatusText(_("Searching..."))

      self.timerSearch.Stop()
      self.search = None # should be killed here

      self.buttonStop.Enable(1)
      self.entry.Disable()
      self.timerSearch.Start(self.delay)

      word = enc.fromWX(word)
      word = word.encode(self.activeDictionary.getEncoding())
      self.search = Process(self.activeDictionary.search, word)


   def onBack(self, event):
      
      self.buttonForward.Enable(1)
      self.htmlWin.SetPage(self.history.back())
      if not self.history.canBack():
         self.buttonBack.Disable()


   def onForward(self, event):
      
      self.buttonBack.Enable(1)
      self.htmlWin.SetPage(self.history.forward())
      if not self.history.canForward():
         self.buttonForward.Disable()


   def onStop(self, event):

      self.entry.Enable(1)
      self.SetStatusText(_("Stopped"))
      self.timerSearch.Stop()
      self.timerLoad.Stop()

      if self.search:
         self.search.stop()
         self.search = None

      if self.load:
         self.load.stop()
         self.load = None

      wxEndBusyCursor()
      self.buttonStop.Disable()
      

   def onClean(self, event):
      self.entry.SetValue("")
         

   def onClearHistory(self, event):
      self.entry.Clear()
      self.history.clear()
      self.buttonBack.Disable()
      self.buttonForward.Disable()


   def wordListHidden(self):
      """Returns True if word list marked to be hidden, False
      otherwise"""

      if self.wlHidden:
         return True

      return False
   

   def onHideUnhide(self, event):
      if self.wordListHidden():
            self.unhideWordList()
      else:
            self.hideWordList()



   def onOpenDictConn(self, event):
      
      window = DictConnWindow(self, -1,
                              _("Connect to DICT server"),
                              style=wxDEFAULT_FRAME_STYLE)
      window.CentreOnScreen()
      window.Show(True)


   def onCloseDict(self, event):
      """Clear widgets and set messages"""

      # If there was a registered dict, set it's default encoding
      # FIXME: new way
      try:
         if self.dict.name in self.app.config.registers.keys():
            self.app.config.registers[self.dict.name][2] = self.app.config.encoding
      except:
         pass

      self.wordList.Clear()
      self.htmlWin.SetPage("")
      self.SetTitle("OpenDict")
      self.words = []

      if self.activeDictionary:
         self.activeDictionary.stop()
         self.activeDictionary = None


      self.SetStatusText(_("Choose a dictionary from \"Dictionaries\" menu"))

   
   def onCopy(self, event):
      
      self.do = wxTextDataObject()
      self.do.SetText(self.htmlWin.SelectionToText())
      
      wxTheClipboard.Open()
      wxTheClipboard.SetData(self.do)
      wxTheClipboard.Close()

   
   def onPaste(self, event):
      """This method is invoked when Paste menu item is selected"""
      do = wxTextDataObject()
      wxTheClipboard.Open()
      if wxTheClipboard.GetData(do):
         try:
            self.entry.SetValue(do.GetText())
         except:
            self.SetStatusText(_("Failed to copy text from the clipboard"))
      else:
         self.SetStatusText(_("Clipboard contains no text data"))
      wxTheClipboard.Close()


   def onShowGroupsWindow(self, event):
      """This method is invoked when Groups menu item is selected"""
      self.groupsWindow = GroupsWindow(self, -1,
                                          _("Groups"),
                                          size=(330, 150),
                                          style=wxDEFAULT_FRAME_STYLE)
      self.groupsWindow.CentreOnScreen()
      self.groupsWindow.Show(True)


   def onShowPluginManager(self, event):
      """This method is invoked when Dictionaries Manager
      menu item is selected"""
      try:
         self.pmWindow = PluginManagerWindow(self, -1,
                                             _("Manage Dictionaries"),
                                             size=(500, 500),
                                             style=wxDEFAULT_FRAME_STYLE)
         self.pmWindow.CentreOnScreen()
         self.pmWindow.Show(True)
      except Exception, e:
         traceback.print_exc()
         systemLog(ERROR, "Unable to show prefs window: %s" % e)
         self.SetStatusText("Error occured, please contact developers (%s)" \
                            % e)
         

   def onShowFileRegistry(self, event):
      self.regWindow = FileRegistryWindow(self, -1,
                                          _("File Register"),
                                          size=(340, 200),
                                          style=wxDEFAULT_FRAME_STYLE)
      self.regWindow.CentreOnScreen()
      self.regWindow.Show(True)


   def onShowDictEditor(self, event):
      editor = DictEditorWindow(self, -1, _("Edit Dictionaries"),
                                     size=(400, 500),
                                     style=wxDEFAULT_FRAME_STYLE)
      editor.CentreOnScreen()
      editor.Show(True)

      
   def onShowPrefsWindow(self, event):
      try:
         self.prefsWindow = PrefsWindow(self, -1, _("Preferences"),
                                        size=(-1, -1),
                                        style=wxDEFAULT_FRAME_STYLE)
         self.prefsWindow.CentreOnScreen()
         self.prefsWindow.Show(True)
      except Exception, e:
         traceback.print_exc()
         systemLog(ERROR, "Unable to show preferences window: %s" % e)
         title = errortype.OPENDICT_BUG.getMessage()
         msg = errortype.OPENDICT_BUG.getLongMessage()
         errorwin.showErrorMessage(title, msg)
         

   def onDefault(self, event):
      # FIXME: Bad way. Try setting a few constants for each type
      # of dictionary and then check this type instead of IDs.

      eventID = event.GetId()
      debugLog(DEBUG, "Event ID = %d" % eventID)
      
      if eventID in self.app.config.ids.keys():
         dictionary = self.app.dictionaries.get(self.app.config.ids.get(eventID))
         self.loadDictionary(dictionary)

      elif 2100 <= eventID < 2500:
         label = self.menuEncodings.FindItemById(eventID).GetLabel()
         self.changeEncoding(label)
      elif 2500 <= eventID < 2600:
         label = self.menuFontFace.FindItemById(eventID).GetLabel()
         self.changeFontFace(label)
      elif 2600 <= eventID < 2700:
         label = self.menuFontSize.FindItemById(eventID).GetLabel()
         self.changeFontSize(label)


   def checkIfNeedsList(self):
      """Unhides word list if current dictionary uses it"""
      
      if self.activeDictionary.getUsesWordList():
         if self.wordListHidden():
            self.unhideWordList()
      else:
         if not self.wordListHidden():
            self.hideWordList()


   def addDictionary(self, dictInstance):
      """Add dictionary to menu and updates ids"""

      app = wxGetApp()
      app.dictionaries[dictInstance.getName()] = dictInstance
      unid = util.generateUniqueID()

      # Insert new menu item only if no same named dictionary exists
      #if not dictInstance.getName() in app.config.ids.values():
      app.config.ids[unid] = dictInstance.getName()
      item = wxMenuItem(self.menuDict,
                        unid,
                        dictInstance.getName())
      EVT_MENU(self, unid, self.onDefault)
      
      self.menuDict.InsertItem(self.menuDict.GetMenuItemCount()-2, item)


   def loadDictionary(self, dictInstance):
      """Prepares main window for using dictionary"""

      #
      # Check licence agreement
      #
      licence = dictInstance.getLicence()
      
      if licence \
             and not self.app.agreements.getAccepted(dictInstance.getPath()):
         if not miscwin.showLicenceAgreement(None, licence):
            from lib.gui import errorwin
            title = _("Licence Agreement Rejected")
            msg = _("You cannot use dictionary \"%s\" without accepting "\
                    "licence agreement" % dictInstance.getName())
            errorwin.showErrorMessage(title, msg)
            return
         else:
            self.app.agreements.addAgreement(dictInstance.getPath())

      self.onCloseDict(None)
      self.activeDictionary = dictInstance
        
      if dictInstance.getType() in dicttype.indexableTypes:
         if plaindict.indexShouldBeMade(dictInstance):
            # Notify about indexing
            from lib.gui import errorwin
            title = _("Dictionary Index")
            msg = _("This is the first time you use this dictionary or it " \
                    "has been changed on disk since last indexing. " \
                    "Indexing is used to make search more efficient. " \
                    "The dictionary will be indexed now. It can take a few " \
                    "or more seconds.\n\n" \
                    "Press OK to continue...")
            errorwin.showInfoMessage(title, msg)

            # Make index
            try:
               wx.BeginBusyCursor()
               plaindict.makeIndex(dictInstance, 
                                   self.app.config.get('encoding'))
               wx.EndBusyCursor()
            except Exception, e:
               wx.EndBusyCursor()
               traceback.print_exc()
               title = _("Index Creation Error")
               msg = _("Error occured while indexing file. " \
                       "This may be because of currently selected " \
                       "character encoding %s is not correct for this " \
                       "dictionary. Try selecting " \
                       "another encoding from View > Character Encoding " \
                       "menu" % self.app.config.get('encoding'))

               from lib.gui import errorwin
               errorwin.showErrorMessage(title, msg)
               return

         # Load index
         try:
            wx.BeginBusyCursor()
            index = plaindict.loadIndex(dictInstance)
            self.activeDictionary.setIndex(index)
            wx.EndBusyCursor()
         except Exception, e:
            wx.EndBusyCursor()
            traceback.print_exc()
            title = _("Error")
            msg = _("Unable to load dictionary index table. " \
                    "Got error: %s" % e)
            from lib.gui import errorwin
            errorwin.showErrorMessage(title, msg)
            return

      wx.BeginBusyCursor()
      self.activeDictionary.start()
      self.checkIfNeedsList()
      self.SetTitle(titleTemplate % dictInstance.getName())
      self.SetStatusText(_(enc.toWX("Dictionary \"%s\" loaded" \
                                    % dictInstance.getName())))

      self.entry.SetFocus()

      try:
         self.checkEncMenuItem(self.activeDictionary.getEncoding())
      except Exception, e:
         systemLog(ERROR, "Unable to select encoding menu item: %s" % e)

      wxEndBusyCursor()

      #if bool(self.app.config.get('scan-clipboard')):
      #   print 'starting scan'
      #   self.timerClipboard.Start(self.scanTimeout)
      #else:
      #   print 'not starting scan'
      

   def loadPlugin(self, name):
      """Sets plugin as currently used dictionary"""

      systemLog(INFO, "Loading plugin '%s'..." % name)
      self.entry.Disable()
      self.dictName = name
      self.activeDictionary = self.app.dictionaries.get(name)
      self.checkIfNeedsList()
      debugLog(INFO, "Dictionary instance: %s" % self.activeDictionary)
      self.SetTitle(titleTemplate % name)
      self.entry.Enable(1)
      self.SetStatusText("Done") # TODO: Set something more useful
      self.htmlWin.SetPage("")
      


   # FIXME: deprecated, update!
   def loadRegister(self, name):

      self.SetTitle(titleTemplate % name) # TODO: should be set after loading
      item = self.app.config.registers[name]
      self.dictName = name
      self.entry.Disable()

      if item[1] == "dwa":
         self.timerLoad.Start(self.delay)
         self.load = Process(SlowoParser, item[0], self)
      elif item[1] == "mova":
         self.timerLoad.Start(self.delay)
         self.load = Process(MovaParser, item[0],
                             self)
      elif item[1] == "tmx":
         self.timerLoad.Start(self.delay)
         self.load = Process(TMXParser, item[0],
                             self)
      elif item[1] == "dz":
         self.timerLoad.Start(self.delay)
         self.load = Process(DictParser, item[0],
                             self)
      else:
         self.SetStatusText(_("Error: not supported dictionary type"))
         return

      self.app.config.encoding = item[2]
      self.checkEncMenuItem(self.app.config.encoding)


   def changeEncoding(self, name):
      self.app.config.set('encoding', misc.encodings[name])

      if self.activeDictionary:
         self.activeDictionary.setEncoding(self.app.config.get('encoding'))
         systemLog(INFO, "Dictionary encoding set to %s" \
               % self.activeDictionary.getEncoding())
         plaindict.savePlainConfiguration(self.activeDictionary)
         

   def changeFontFace(self, name):
      """Save font face changes"""
      
      self.app.config.set('fontFace', misc.fontFaces[name])
      self.updateHtmlScreen()


   def changeFontSize(self, name):
      
      fontSize = int(name) * 10
      systemLog(INFO, "Setting font size %d" % fontSize)
      self.app.config.set('fontSize', fontSize)
      self.updateHtmlScreen()


   def updateHtmlScreen(self):
      """Update HtmlWindow screen"""

      self.htmlWin.SetFonts(self.app.config.get('fontFace'), "Fixed",
                            [int(self.app.config.get('fontSize'))]*5)
      self.htmlWin.SetPage(self.htmlCode)


   def onIncreaseFontSize(self, event):
      """Increase font size"""

      self.app.config.set('fontSize', int(self.app.config.get('fontSize'))+2)
      self.updateHtmlScreen()


   def onDecreaseFontSize(self, event):
      """Decrease font size"""

      self.app.config.set('fontSize', int(self.app.config.get('fontSize'))-2)
      self.updateHtmlScreen()


   def onNormalFontSize(self, event):
      """Set normal font size"""

      self.app.config.set('fontSize', NORMAL_FONT_SIZE)
      self.updateHtmlScreen()


   def checkEncMenuItem(self, name):
      """Select menu item defined by name"""
      
      ename = ""
      for key in misc.encodings:
         if name == misc.encodings[key]:
            ename = key
            break
         
      debugLog(DEBUG, "Encoding name to select: '%s'" % ename)
      if len(ename) == 0:
         systemLog(ERROR, "Something wrong with encodings (name == None)")
         return
      
      self.menuEncodings.FindItemById(self.menuEncodings.FindItem(ename)).Check(1)


   def getCurrentEncoding(self):
      """Return currently set encoding"""

      # Is this the best way for keeping it?
      return self.app.config.encoding
   

   def onAddDict(self, event):
      installer = Installer(self, self.app.config)
      installer.showGUI()

      
   def onAddFromFile(self, event):
      """Starts dictionary registration process"""

      fileDialog = wxFileDialog(self, _("Choose dictionary file"), "", "",
                            "", wxOPEN|wxMULTIPLE)

      if fileDialog.ShowModal() == wxID_OK:
         file = fileDialog.GetPaths()[0]
      else:
         fileDialog.Destroy()
         return

      flist = ["Slowo", "Mova", "TMX", "Dict"]

      msg = _("Select dictionary format. If you can't find\n" \
              "the format of your dictionary, the register\n" \
              "system does not support it yet.")
      formatDialog = wxSingleChoiceDialog(self,
                                          msg,
                                          _("Dictionary format"),
                                          flist, wxOK|wxCANCEL)
      if formatDialog.ShowModal() == wxID_OK:
         format = formatDialog.GetStringSelection()
      else:
         formatDialog.Destroy()
         return

      fileDialog.Destroy()
      formatDialog.Destroy()

      return self.app.reg.registerDictionary(file, format,
                                             self.app.config.defaultEnc)

   def onAddFromPlugin(self, event):
      """Starts plugin installation process"""

      dialog = wxFileDialog(self, _("Choose plugin file"), "", "",
                            "", wxOPEN|wxMULTIPLE)
      if dialog.ShowModal() == wxID_OK:
         plugin.installPlugin(self.app.config, dialog.GetPaths()[0])
      dialog.Destroy()

   def onManual(self, event):
      """Shows Manual window"""

      systemLog(WARNING, "Manual function is not impelemented yet")
      

   def onLicence(self, event):
      """Shows 'License' window"""

      licenseWindow = LicenseWindow(self, -1,
                                _("License"),
                                size=(500, 400),
                                style=wxDEFAULT_FRAME_STYLE)
      licenseWindow.CenterOnScreen()
      licenseWindow.Show(True)


   def onAbout(self, event):
      """Shows 'About' window"""

      aboutWindow = AboutWindow(self, -1,
                                _("About"),
                                style=wxDEFAULT_DIALOG_STYLE)
      aboutWindow.CentreOnScreen()
      aboutWindow.Show(True)


   def onWordSelected(self, event):
      """Is called when word list item is selected"""

      self.__searchedBySelecting = 1
      self.SetStatusText(_("Searching..."))
      self.buttonStop.Enable(1)
      self.timerSearch.Start(self.delay)
      word = event.GetString()
      global lastLookupWord
      lastLookupWord = word
      self.entry.SetValue(word)
      word = enc.fromWX(word)
      word = word.encode(self.activeDictionary.getEncoding())
      self.search = Process(self.activeDictionary.search, word)
      wxBeginBusyCursor()


   def createListPanel(self):
      self.panelList = wxPanel(self.splitter, -1)
      sbSizerList = wxStaticBoxSizer(wxStaticBox(self.panelList, -1, 
                                                 _("Word List")), 
                                     wxVERTICAL)
      self.wordList = wxListBox(self.panelList, 154, wxPoint(-1, -1),
                                wxSize(-1, -1), self.words, wxLB_SINGLE)
      sbSizerList.Add(self.wordList, 1, wxALL | wxEXPAND, 0)
      self.panelList.SetSizer(sbSizerList)
      self.panelList.SetAutoLayout(true)
      sbSizerList.Fit(self.panelList)

      
   def hideWordList(self):
      """Hides word list"""

      systemLog(DEBUG, "Hiding word list...")
      self.splitter.SetSashPosition(0)
      self.splitter.Unsplit(self.panelList)
      self.wlHidden = True

      # And change the button pixmap
      debugLog(DEBUG, "Setting unhide.png icon...")
      bmp = wxBitmap(os.path.join(info.GLOBAL_HOME, "pixmaps", "unhide.png"),
                     wxBITMAP_TYPE_PNG)
      self.buttonHide.SetBitmapLabel(bmp)
      self.buttonHide.SetToolTipString(_("Show word list"))


   def unhideWordList(self):
      """Shows word list"""

      systemLog(DEBUG, "Showing word list...")
      self.createListPanel()
      self.splitter.SplitVertically(self.panelList, self.panelHtml)
      self.splitter.SetSashPosition(int(self.app.config.get('sashPos')))
      self.wlHidden = False

      # And change the pixmap
      debugLog(DEBUG, "Setting hide.png icon...")
      bmp = wxBitmap(os.path.join(info.GLOBAL_HOME, "pixmaps", "hide.png"),
                     wxBITMAP_TYPE_PNG)
      self.buttonHide.SetBitmapLabel(bmp)
      self.buttonHide.SetToolTipString(_("Hide word list"))


   def onPrint(self, event):
      """This method is invoked when print menu item is selected"""

      try:
         self.printer.PrintText(self.htmlCode)
      except Exception, e:
         self.SetStatusText(_("Failed to print"))
         systemLog(ERROR, "Unable to print translation (%s)" % e)
         traceback.print_exc()


   def onPreview(self, event):
      """This method is invoked when preview menu item is selected"""

      try:
         self.printer.PreviewText(self.htmlCode)
      except Exception, e:
         systemLog(ERROR, "Unable to preview translation (%s)" % e)
         self.SetStatusText(_("Page preview failed"))
         traceback.print_exc()


   def savePreferences(self):
      """Saves window preferences when exiting"""

      if self.app.config.get('saveWindowSize'):
         self.app.config.set('windowWidth', self.GetSize()[0])
         self.app.config.set('windowHeight', self.GetSize()[1])
      if self.app.config.get('saveWindowPos'):
         self.app.config.set('windowPosX', self.GetPosition()[0])
         self.app.config.set('windowPosY', self.GetPosition()[1])
      if self.app.config.get('saveSashPos'):
         if not self.wordListHidden():
             self.app.config.set('sashPos', self.splitter.GetSashPosition())

      try:
         self.app.config.save()
      except Exception, e:
         systemLog(ERROR, "Unable to save configuration: %s" % e)
         
