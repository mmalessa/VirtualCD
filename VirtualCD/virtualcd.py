#
# Virtual CD Player
# by Marcin Malessa
# v. 0.4beta
#
# -- GPL --
#

from Screens.Screen import Screen
#from Components.config import config
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.FileList import FileList
from Components.MediaPlayer import PlayList
#from Components.ServicePosition import ServicePositionGauge
#from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
#from Components.Playlist import PlaylistIOInternal, PlaylistIOM3U, PlaylistIOPLS
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarNotifications
from enigma import eTimer, evfd	
	#, gFont
import os
import re

class VirtualCDScreen(Screen, InfoBarBase, InfoBarSeek, InfoBarNotifications):
	skin = """
	<screen name="virtualcd" title="VirtualCD" position="0,0" size="1280,720" backgroundColor="#00060606" flags="wfNoBorder">
	<widget name="infoLabel" position="40,10" size="1000,60" font="Regular;30"/>
	<widget source="session.CurrentService" render="Progress" position="40,100" size="460,10" backgroundColor="#00101214" borderWidth="1" borderColor="#00555556" transparent="1">
		  <convert type="ServicePosition">Position</convert>
	</widget>
	<widget source="session.CurrentService" render="Label" position="600,100" size="60,25" backgroundColor="#00101214" transparent="1" font="Regular;22" valign="center" halign="left">
		  <convert type="ServicePosition">Position</convert>
	</widget>
	<widget source="session.CurrentService" render="Label" position="700,100" size="60,25" backgroundColor="#00101214" transparent="1" font="Regular;22" valign="center" halign="right">
		  <convert type="ServicePosition">Remaining</convert>
	</widget>
	
	<widget source="session.CurrentService" render="Label" position="800,100" size="120,40" font="Regular;26" foregroundColor="#00e5b243" backgroundColor="#00101214" halign="right" transparent="1">
		  <convert type="ServicePosition">Length</convert>
	</widget>
	
	<widget name="albumList" position="40,150" size="560,500" backgroundColor="#00101214" scrollbarMode="showOnDemand" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualCD/sel.png" />
        <widget name="playList" position="620,150" size="560,500" backgroundColor="#00101214" scrollbarMode="showOnDemand" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualCD/sel.png" />
	</screen>"""
	
#    <widget name="songList" position="620,80" size="560,600" backgroundColor="#00101214" scrollbarMode="showOnDemand" selectionPixmap="/usr/lib/enigma2/python/Plugins/Extensions/YampMusicPlayer/images/sel.png" />
	
	def __init__(self, session, args=None):
		
		# FIXME - z konfiguracji
		self.albumDir='/hdd/music/'
		self.displayTime=1800
		
		
		# zmienne
		self.playStatus=False
		self.pauseStatus=False
		self.playPosition=-1
		self.vfdText=''
		self.vfdTextOld=''
		
		
		# BEGIN
		self.session = session
		Screen.__init__(self, session)
		#InfoBarSeek.__init__(self, actionmap = "VirtualCDActions")
		InfoBarBase.__init__(self)
		InfoBarNotifications.__init__(self)
		
		
		

		# switch services
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
		
		# album List
		self.albumList=VirtualCDFileList(self.albumDir, showDirectories = True, showFiles = False, isTop=True)
		self["albumList"] = self.albumList

		# play List
		self.playList=VirtualCDPlayList()
		self["playList"] = self.playList

		# info Label
		self.infoLabel=''
		self["infoLabel"] = Label()

		# timers
		#self.eofbugTimer = eTimer()
		#self.eofbugTimer.callback.append(self.checkEOF)
		
		self.globalTimer = eTimer()
		self.globalTimer.callback.append(self.globalTimerCallback)
		
		
		# ActionMap
		self["actions"] = ActionMap(["VirtualCDActions"],
		{
			"albumUp":		self.albumUp,
			"albumDn":		self.albumDn,
			"albumPgUp":		self.albumPgUp,
			"albumPgDn":		self.albumPgDn,
			"keyOK":		self.albumPlay,
			"songPrev":		self.songPrev,
			"songNext":		self.songNext,
			"songPlay":		self.songPlay,
			"songStop":		self.songStop,
			"songPause":		self.songPause,
			"exit":			self.plgExit,
			"nop":			self.testWindow

		},-2)
		
		#InfoBarSeek.__init__(self, actionmap = "VirtualCDActions")
		
		# important actions
		#self.onShown.append(self.plgBegin)
		self.onLayoutFinish.append(self.plgBegin)
		self.onClose.append(self.plgCleanup)

		
	# actions after laout create
	def plgBegin(self):
		self.globalTimer.start(500)
		self.albumDisplay()
	

	# actions on close
	def plgCleanup(self):
		self.session.nav.playService(self.oldService)
		del self.globalTimer
		

	# close plugin	
	def plgExit(self):
		self.close(False,self.session)
		
	def albumUp(self):
	    self["albumList"].up()
	    self.albumDisplay()
	    return
	
	def albumDn(self):
	    self["albumList"].down()
	    self.albumDisplay()
	    return
	
	def albumPgUp(self):
	    self["albumList"].pageUp()
	    self.albumDisplay()
	    return
	
	def albumPgDn(self):
	    self["albumList"].pageDown()
	    self.albumDisplay()
	    return
	
	
	def albumDisplay(self):
	    #albumName=self.albumList.getFilename()
	    albumName=self.albumList.getSelection()[0]
	    if albumName is None:
		text="*"
	    else:
		text = albumName.split('/')[-2]
		if len(text)>16:
			s=text.split(' - ')
			text=s[0][0:8] + '/' + s[1][0:7]
	    self.display(text)
	    
	
	
	def albumPlay(self):
	    self.playlistClear()
	    self.playlistFill()
	    self.songPlay()
	    self.playStatus=True
	    return
	    
	    
	def playlistClear(self):
		self.songStop()
		self.playList.clear()
	
	def playlistFill(self):
		directory=self.albumList.getFilename()
		#directory=self.albumList.getSelection()[0]
		if directory is None:
			return
		#filelist = FileList(directory, useServiceRef = True, showMountpoints = False, isTop = True)
		filelist = FileList(directory, matchingPattern = "^.*\.(mp3|wav|flac)", useServiceRef = True, isTop = True, showFiles=True)
		
		for x in filelist.getFileList():
			if x[0][1] != True: # not isDir
				self.playList.addFile(x[0][0])
		self.playList.updateList()
		self.playList.setCurrentPlaying(0)
	
	

	def songPrev(self):
		self.playList.stopFile()
		next = self.playList.getCurrentIndex() - 1
		if next >= 0:
			self.playList.setCurrentPlaying(next)
			if self.playStatus:
				self.songPlay()
		else:
			self.songStop()
		return
	
	def songNext(self):
		#self.playList.stopFile()
	  	next = self.playList.getCurrentIndex() + 1
		if next < len(self.playList):
			self.playList.setCurrentPlaying(next)
			if self.playStatus:
				self.songPlay()
		else:
			self.songStop()
		return
	
	# doesn't work - enigma bug?
#	def doEofInternal(self, playing):
#		if playing:
#			self.songNext()		
#		else:
#			songStop()
#			self.showPlayer()
	
	def checkEOF(self):
		if self.playStatus:
			len, pos = self.getSeekData()
			if self.playPosition == pos:
				self.songNext()
			else:
				self.playPosition = pos
	
	def getSeekData(self):
		service = self.session.nav.getCurrentService()
		seek = service and service.seek()
		if seek is None:
			return (0, 0)
		len = seek.getLength()
		pos = seek.getPlayPosition()
		if len[0] or pos[0]:
			return (0, 0)
		return (len[1], pos[1])
	
	
	def songPlay(self):
		text="song"
		if len(self.playList.getServiceRefList()):
			needsInfoUpdate = False
			currref = self.playList.getServiceRefList()[self.playList.getCurrentIndex()]
			
			if self.session.nav.getCurrentlyPlayingServiceReference() is None or currref != self.session.nav.getCurrentlyPlayingServiceReference():
				text = currref.getPath().split('/')[-1]
				self.playStatus=True
				self.playPosition=-1
				self.playList.playFile()
				self.session.nav.playService(currref)
				
				#if text[-4:] == ".mp3":
				#	text=text[:-4]
				#elif text[-5:] == ".flac":
				#	text=text[:-5]

				self.display(text)

	
	def songStop(self):
		self.playStatus=False
		self.playList.stopFile()
		self.session.nav.playService(None)
		#self.display("STOP")
		self.albumDisplay()

	
	def songPause(self):
		#self.pauseService()
		#self.playList.pauseService()
		#self.testWindow('S-Pause')
		return
	
	
	def display(self,text):
		if text is None:
			text=""
		self["infoLabel"].setText(text)
		text = text + "                "
		#if len(text)>16:
		#	text=text[0:16]
		self.vfdText=text[0:16]
		#evfd.getInstance().vfd_write_string(text)
	
	def testWindow(self,text="****"):
		self["infoLabel"].setText(text)
	    
	    
	# timer for VFD and checkEOF
	def globalTimerCallback(self):
		self.checkEOF()
		
		if self.vfdText != self.vfdTextOld:
			self.vfdTextOld=self.vfdText
			evfd.getInstance().vfd_write_string(self.vfdText)
		return
	    
class VirtualCDFileList(FileList):
	def __init__(self, directory, showDirectories = True, showFiles = True, showMountpoints = True, matchingPattern = None, useServiceRef = False, inhibitDirs = False, inhibitMounts = False, isTop = False, enableWrapAround = False, additionalExtensions = None):
		FileList.__init__(self, directory, showDirectories, showFiles, showMountpoints, matchingPattern, useServiceRef, inhibitDirs, inhibitMounts, isTop, enableWrapAround, additionalExtensions)
		#self.l.setFont(0, gFont("Regular", 24))
                #self.l.setItemHeight(30)

	def __len__(self):
		return len(self.list)

class VirtualCDPlayList(PlayList):
	def __init__(self):
		PlayList.__init__(self)