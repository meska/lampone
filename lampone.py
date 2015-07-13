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
from threading import Timer
from shutil import copy2
from datetime import datetime,timedelta
from configparser import ConfigParser



class Lampone(Bot):
    
    def __init__(self, token,admins=""):
        super().__init__(token) # init classe principale
        self.admins = [ int(x) for x in admins.split(",") ]
        # init megaHal    
        self.lastbackup = None
        self.brainfile_name = os.path.join(os.path.split(__file__)[0],"lampone.brain")
        try:
            self.megahal = MegaHAL(brainfile=self.brainfile_name)
        except Exception as e:
            print("Database Error: %s"% e)
            # fallback to backup
            hour_current = datetime.now().hour
            hour_last_try = (datetime.now() + timedelta(hours=1)).hour
            while True:
                if os.path.exists("%s.%s" % (self.brainfile_name,hour_current)):
                    # unlink broken brainfile
                    os.unlink(self.brainfile_name)
                    # move backup file
                    copy2("%s.%s" % (self.brainfile_name,hour_current),self.brainfile_name)
                    os.unlink("%s.%s" % (self.brainfile_name,hour_current))
                    self.__init__(token)
                    break
                
                if hour_current == hour_last_try:
                    print("No backups found, reinit from scratch")
                    os.unlink(self.brainfile_name)
                    self.__init__(token)
                    break
                hour_current-=1
                if hour_current < 0:
                    hour_current = 23


    def learn(self,message):
        lines = message['text'].splitlines()[1:]
        for l in lines:
            self.megahal.learn(l)
        self.megahal.sync()


    def backupBrain(self):
        # backup brain file in case of crash
        print("Brain Backup! %s" % datetime.now().hour)
        self.megahal.sync()
        if os.path.exists("%s.%s" % (self.brainfile_name,datetime.now().hour)):
            os.unlink("%s.%s" % (self.brainfile_name,datetime.now().hour))
        copy2(self.brainfile_name, "%s.%s" % (self.brainfile_name,datetime.now().hour))
        
    def parsedocument(self,chat_id,message):
        print("Documento ricevuto da %s" % message['from'] )

    def parsemessage(self,chat_id,message):
        print("Messaggio ricevuto da %s" % message['from'] )
        print(message['text'])
        
        if self.lastbackup != datetime.now().hour:
            self.lastbackup = datetime.now().hour
            self.backupBrain()

        if message['text'].startswith('/learn') and message['from']['id'] in self.admins:
            self.learn(message)
            return
        
        if message['text'] == "/start":
            self.sendMessage(chat_id,"Welcome to Lampone Bot")
            return
        
        if not message['text'].startswith('/'):
            reply = self.megahal.get_reply(message['text'])
            self.sendMessage(chat_id,reply)
    

if __name__ == '__main__':
    
    # load config
    cf = ConfigParser()
    if os.path.exists(os.path.join(os.path.split(__file__)[0],"lampone.conf")):
        cf.read(os.path.join(os.path.split(__file__)[0],"lampone.conf"))
    else:
        # set defaults
        cf.add_section("telegram")
        cf.set("telegram","token","YOUR TOKEN HERE")
        cf.set("telegram","admins","12345,12345,1232")
        with open(os.path.join(os.path.split(__file__)[0],"lampone.conf"),"w") as cf_file:
            cf.write(cf_file)
    

    if cf['telegram']['token'] == "YOUR TOKEN HERE":
        print("Token not defined, check config!")    
    else:
        l = Lampone(cf['telegram']['token'],admins=cf['telegram']['admins'])
        #l.clearWebHook()
        print(l.get('getMe'))
        l.getUpdates()
