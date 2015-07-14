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
        # TODO in some os shelve appends .db to filename
        self.brainfile_name_real = os.path.join(os.path.split(__file__)[0],"lampone.brain.db")
        try:
            self.megahal = MegaHAL(brainfile=self.brainfile_name)
        except Exception as e:
            print("Database Error: %s"% e)
            # fallback to backup
            hour_current = datetime.now().hour
            hour_last_try = (datetime.now() + timedelta(hours=1)).hour
            while True:
                if os.path.exists("%s.%s" % (self.brainfile_name_real,hour_current)):
                    # unlink broken brainfile
                    os.unlink(self.brainfile_name_real)
                    # move backup file
                    copy2("%s.%s" % (self.brainfile_name_real,hour_current),self.brainfile_name_real)
                    os.unlink("%s.%s" % (self.brainfile_name_real,hour_current))
                    self.__init__(token)
                    break
                
                if hour_current == hour_last_try:
                    print("No backups found, reinit from scratch")
                    os.unlink(self.brainfile_name_real)
                    self.__init__(token)
                    break
                hour_current-=1
                if hour_current < 0:
                    hour_current = 23


    def learn(self,message):
        lines = message['text'].splitlines()[1:]
        for l in lines:
            print("learning: %s" % l)
            self.megahal.learn(l)
        self.megahal.sync()


    def backupBrain(self):
        # backup brain file in case of crash
        print("Brain Backup! %s" % datetime.now().hour)
        self.megahal.sync()

        # check for brainfile ext
        if not os.path.exists(self.brainfile_name_real):
            self.brainfile_name_real = self.brainfile_name
            
        if os.path.exists("%s.%s" % (self.brainfile_name_real,datetime.now().hour)):
            os.unlink("%s.%s" % (self.brainfile_name_real,datetime.now().hour))
        copy2(self.brainfile_name_real, "%s.%s" % (self.brainfile_name_real,datetime.now().hour))
        
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
        
        if message['text'].startswith('/update') and message['from']['id'] in self.admins:
            """
            Bot updates from git and then quits, 
            to reload automatically use a cron like this:
            */1 * * * * [ `ps aux | grep python3 | grep lampone | grep -v grep | wc -l` -eq 0 ] && /usr/bin/python3 /home/pi/lampone/lampone.py  > /dev/null 2>&1
            """
            self.sendMessage(chat_id,"Updating...")
            res = os.popen("cd %s && git pull" % os.path.join(os.path.split(__file__)[0])).read()
            self.sendMessage(chat_id,res)
            self.sendMessage(chat_id,"Restarting...")
            self.stop = True
            return        
        
        if message['text'].startswith('/f') and message['from']['id'] in self.admins:
            ## fortune auto learning, needs fortune-mod installed
            ## check for params
            count = 1
            if len(message['text'].split()) > 1:
                param = message['text'].split()[1]
                if param.isdecimal():
                    count = int(param)
                    if count > 100:
                        count = 100
            self.sendMessage(chat_id,"Learning %s fortunes"%count)
            for x in range(count):
                txt = os.popen('fortune | grep -v "\-\-\s.*" | grep -v ".*:$" | grep -v ".*http://"').read()
                if txt:
                    self.megahal.learn(txt)
            self.sendMessage(chat_id,"Done")
            return        
        
        if message['text'] == "/start":
            self.sendMessage(chat_id,"Welcome to Lampone Bot")
            return
        
        if message['text'] == "/help":
            self.sendMessage(chat_id,"This is a simple AI bot, just talk to him or invite to your group and he will learn and respond\s")
            return        
        
        if message['text'] == "/stop":
            self.sendMessage(chat_id,"Command not needed, just close the chat :)")
            return        
        
        if message['text'] == "/s" and message['from']['id'] in self.admins:
            self.megahal.sync()
            self.sendMessage(chat_id,"Sync db")
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
        for admin in l.admins:
            # notify admins when online
            l.sendMessage(admin,"Lampone is Online!")
        l.getUpdates()
