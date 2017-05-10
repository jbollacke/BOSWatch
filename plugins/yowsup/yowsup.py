#!/usr/bin/python
# -*- coding: cp1252 -*-

"""
Yowsup-Plugin to dispatch POCSAG - messages to WhatsApp Numbers or Chats

@author: fwmarcel, mezzobob

@requires: 	yowsup2 has to be installed
			whatsapp number and password
			yowsup-Configuration has to be set in the config.ini
"""

import logging
import subprocess
import shlex
import os

from includes import globalVars

#from includes.helper import timeHandler
from includes.helper import wildcardHandler
from includes.helper import configHandler

from Queue import Queue
from threading import Thread

def send_msg_thread():
	empfaengerList = globalVars.config.get("yowsup", "empfaenger").split(',')
	sender = globalVars.config.get("yowsup", "sender")
	password = globalVars.config.get("yowsup", "password")

	while True:
		logging.debug("waiting for messages")
		text = queue.get()
		if not text:
			logging.debug("received end of queue")
			queue.task_done()
			return
		for empfaenger in empfaengerList:
			devnull = open(os.devnull, "wb")
			cmd = 'yowsup-cli demos -l ' + sender + ':' + password + ' -s ' + empfaenger + ' "' + text + '"'
			subprocess.call(shlex.split(cmd), stdout=devnull, stderr=devnull)
			logging.debug("Message has been sent to "+ str(empfaenger))
			devnull.close()
		queue.task_done()

def onLoad():
	return

def onUnload():
	queue.put(None)
	return

def run(typ,freq,data):
	try:
		if configHandler.checkConfig("yowsup"):
			if typ in ("FMS", "ZVEI", "POC"):
				text = globalVars.config.get("yowsup",typ.lower()+"_message")
				text = wildcardHandler.replaceWildcards(text, data)
				queue.put(text)
	except:
		logging.error("unknown error")
		logging.debug("unknown error", exc_info=True)

queue = Queue()
thread = Thread(target=send_msg_thread).start()
