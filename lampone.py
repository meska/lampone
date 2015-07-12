#!/usr/bin/env python
#coding:utf-8
"""
  Author: Marco Mescalchin  --<>
  Purpose: Lampone telgram bot, chat to @LamponeBot
  Created: 07/12/15
"""
import os,sys
from wrapper import Bot
from megahal import MegaHAL

class Lampone(Bot):
    
    def __init__(self, token):
        super().__init__(token) # init classe principale
        # init megaHal    
        self.m = MegaHAL(brainfile=os.path.join(os.path.split(__file__)[0],"lampone.brain"))


    def learn(self,message):
        with open(os.path.join(os.path.split(__file__)[0],"learnme.txt"),"rb") as doc :
            lines = doc.readlines()
            for l in lines:
                self.m.learn(l.decode('utf8').replace("\n",""))
            self.m.sync()

    def parsemessage(self,chat_id,message):
        print("Messaggio ricevuto da %s" % message['from'] )
        print(message['text'])

        if message['text'] == "/learn":
            self.learn(message)
            return

        if not message['text'].startswith('/'):
            reply = self.m.get_reply(message['text'])
            self.sendMessage(chat_id,reply)
    

if __name__ == '__main__':
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("Token non definito, impostare TELEGRAM_TOKEN ")    
    else:
        l = Lampone(token)
        l.getUpdates()
