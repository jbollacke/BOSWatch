#!/usr/bin/python
# -*- coding: UTF-8 -*-

from yowsup.layers import YowLayerEvent, EventCallback
from yowsup.layers.axolotl.props import PROP_IDENTITY_AUTOTRUST
from yowsup.layers.interface import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.network import YowNetworkLayer
from yowsup.layers.protocol_messages.protocolentities import *
from yowsup.stacks import YowStackBuilder
from yowsup.common.tools import Jid

from Queue import Queue
from threading import Thread, Condition

from includes import globalVars
from includes.helper import wildcardHandler
from includes.helper import configHandler

import logging

empfaengerList = globalVars.config.get("yowsupex", "empfaenger").split(',')
sender = globalVars.config.get("yowsupex", "sender")
password = globalVars.config.get("yowsupex", "password")


class Layer(YowInterfaceLayer):
    def __init__(self):
        super(Layer, self).__init__()
        self.messages = {}
        self.state = YowNetworkLayer.STATE_CONNECTING
        self.lock = Condition()

    @EventCallback(YowNetworkLayer.EVENT_STATE_DISCONNECTED)
    def onDisconnected(self, event):
        logging.debug("Disconnected!")
        self.state = YowNetworkLayer.STATE_DISCONNECTED

    @EventCallback(YowNetworkLayer.EVENT_STATE_CONNECTED)
    def onConnect(self, event):
        logging.debug("Connected!")

    def sendMessage(self, recipient, text):
        message = TextMessageProtocolEntity(text, to=Jid.normalize(recipient))
        if self.state == YowNetworkLayer.STATE_DISCONNECTED:
            logging.debug("Not ready! Reconnect...")
            self.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))
            self.state = YowNetworkLayer.STATE_CONNECTING
        elif self.state == YowNetworkLayer.STATE_CONNECTED:
            self.toLower(message)

        self.messages[message.getId()] = message

    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):
        logging.debug("onMessage")
        self.toUpper(messageProtocolEntity)
        self.toLower(messageProtocolEntity.ack(True))

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        logging.debug("onReceipt")
        self.toLower(entity.ack())

    @ProtocolEntityCallback("ack")
    def onAck(self, entity):
        logging.debug("onAck")
        try:
            del self.messages[entity.getId()]
        except KeyError:
            pass

    @ProtocolEntityCallback("success")
    def onAuth(self, protocolEntity):
        logging.info("Authenticated!")
        self.state = YowNetworkLayer.STATE_CONNECTED

        # resend messages without ack
        logging.info("Resending old messages w/o ack now")
        for id, message in self.messages.items():
            self.toLower(message)


stack = YowStackBuilder().pushDefaultLayers(True).push(Layer).build()
stack.setCredentials((sender, password))
stack.setProp(PROP_IDENTITY_AUTOTRUST, True)
stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))

def send_msg_thread():
    stack.loop(timeout = 0.5, discrete = 0.5)
    logging.warn("Loop exited!")

yowsupThread = Thread(target=send_msg_thread)
yowsupThread.daemon = True
yowsupThread.start()

def run(typ,freq,data):
    try:
        if configHandler.checkConfig("yowsupex"):
            if typ in ("FMS", "ZVEI", "POC"):
                text = globalVars.config.get("yowsupex",typ.lower()+"_message")
                text = wildcardHandler.replaceWildcards(text, data)
                for empfaenger in empfaengerList:
                    stack.getLayer(-1).sendMessage(empfaenger, text)
    except:
        logging.error("unknown error")
        logging.debug("unknown error", exc_info=True)

def onLoad():
    return
