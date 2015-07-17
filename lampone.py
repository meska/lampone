#!/usr/bin/env python
#coding:utf-8
"""
  Author: Meska
  Purpose: Lampone telegram bot, chat to @LamponeBot
  Created: 07/12/15
  

  commands
  start - Starts!
  stop - stops ?
  groupmode - Set groupchat mode
  
  
"""
import os,sys
from wrapper import Bot
from megahal import MegaHAL
from threading import Timer
from shutil import copy2
from datetime import datetime,timedelta
from configparser import ConfigParser
from random import randrange

class Lampone(Bot):
    
    listening = []
    badboys = {}
    groupmode = {}

    
    def __init__(self, token,admins="",redis=None):
        super().__init__(token) # init classe principale

        self.admins = [ int(x) for x in admins.split(",") ]
        
        

        self.brainfile_name = os.path.join(os.path.split(__file__)[0],"lampone.brain")
        
        
        
        # delete old brain on restart
        if os.path.exists(self.brainfile_name):
            os.unlink(self.brainfile_name)
           
        if os.path.exists(os.path.join(os.path.split(__file__)[0],"lampone.brain.db")):
            os.unlink(os.path.join(os.path.split(__file__)[0],"lampone.brain.db"))
            
        self.megahal = MegaHAL(brainfile=self.brainfile_name)
        self.autolearn()
            
    def __del__(self):
        # salva cose varie
        pass 

    def log_learn(self,msg):
        # loggo solo le frasi in caso il db si smerdi
        try:
            with open(os.path.join(os.path.split(__file__)[0],"lampone_learn.txt"),"a") as logfile:
                logfile.write("%s\n" % msg)
        except Exception as e:
            print(e)

    def learn(self,message):
        # manual learn
        lines = message['text'].splitlines()[1:]
        for l in lines:
            print("learning: %s" % l)
            self.megahal.learn(l)
            self.log_learn(l)
        self.megahal.sync()

    def autolearn(self):
        # learns from previous chats
        self.sendMessage(self.admins[0],"Autolearn Start")
        lines = []
        with open("lampone_learn.txt","rb") as logfile:
            for l in logfile.readlines():
                l = l.decode('utf8').strip()
                ok = True
                if 'lampone' in l.lower(): ok = False
                if 'http' in l.lower(): ok = False
                if len(l) < 3: ok = False
                if l.lower() in lines: ok = False
                if len(l.split()) < 3: ok = False
                if '@' in l: ok = False
                    
                if ok:
                    print("learning: %s" % l)
                    self.megahal.learn(l)
                    lines.append(l.lower())

        with open("lampone_learn_cleaned.txt","wb") as logfile:
            for l in lines:
                logfile.write((l + "\n").encode('utf8'))
                
        self.megahal.sync()
        self.sendMessage(self.admins[0],"Autolearn Finished")

        
    def parsedocument(self,chat_id,message):
        print("Documento ricevuto da %s" % message['from'] )

    def parsemessage(self,chat_id,message):
        print("Messaggio ricevuto da %s" % message['from'] )
        print(message['text'])
        if self.stop:
            # stopping, ignore messages
            return
        

        #if self.lastbackup != datetime.now().hour:
        #    self.lastbackup = datetime.now().hour
        #    self.backupBrain()

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
            res = os.popen("cd %s && git fetch --all && git reset --hard origin" % os.path.join(os.path.split(__file__)[0])).read()
            self.sendMessage(chat_id,res)
            self.sendMessage(chat_id,"Restarting...")
            self.megahal.sync()
            self.megahal._MegaHAL__brain.db.close()            
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

        if message['text'] == "/groupmode":
            if chat_id > 0:
                self.sendMessage(chat_id,"This is not a group.")
            else:
                self.sendMessage(chat_id,"Select Group Mode:",reply_markup={'keyboard':[['/g1 Respond all messages'],['/g2 Respond some messages'],['/g3 Respond only for Lampone'],]})
            return
        
        if message['text'].startswith("/g1"):
            if chat_id > 0:
                self.sendMessage(chat_id,"This is not a group.",reply_markup={'hide_keyboard':True})
            else:
                self.groupmode[chat_id] = 1
                self.sendMessage(chat_id,"Groupmode 1 enabled",reply_markup={'hide_keyboard':True})
            return
        
        if message['text'].startswith("/g2"):
            if chat_id > 0:
                self.sendMessage(chat_id,"This is not a group.",reply_markup={'hide_keyboard':True})
            else:
                self.groupmode[chat_id] = 2
                self.sendMessage(chat_id,"Groupmode 2 enabled",reply_markup={'hide_keyboard':True})
            return
        
        if message['text'].startswith("/g3"):
            if chat_id > 0:
                self.sendMessage(chat_id,"This is not a group.",reply_markup={'hide_keyboard':True})
            else:
                self.groupmode[chat_id] = 3
                self.sendMessage(chat_id,"Groupmode 3 enabled",reply_markup={'hide_keyboard':True})
            return        
        
        if message['text'] == "/help":
            self.sendMessage(chat_id,"This is a simple AI bot, just talk to him or invite to your group and he will learn and respond\nTry /groupmode for limit group interaction")
            return        
        
        if message['text'] == "/stop":
            self.sendMessage(chat_id,"Command not needed, just close the chat :)")
            return        
        
        if message['text'] == "/s" and message['from']['id'] in self.admins:
            self.megahal.sync()
            self.megahal._MegaHAL__brain.db.close()
            self.megahal = MegaHAL(brainfile=self.brainfile_name)
            self.sendMessage(chat_id,"Sync db")
            return       
        
        if message['text'] == "/autolearn" and message['from']['id'] in self.admins:
            self.autolearn()
            return              
        
        if message['text'] == "/listen" and message['from']['id'] in self.admins:
            self.sendMessage(chat_id,"Listening enabled, stop with /stoplisten")
            if not chat_id in self.listening:
                self.listening.append(chat_id)
            return        
        
        if message['text'] == "/stoplisten" and message['from']['id'] in self.admins:
            self.sendMessage(chat_id,"Listening stopped")
            if chat_id in self.listening:
                self.listening.pop(self.listening.index(chat_id))
            return                
        
        if not message['text'].startswith('/'):
            for ll in self.listening:
                self.sendMessage(ll,"<-- %s" % message['text'])

            learn = True
            rispondi = True


            if len(message['text'].split()) < 3:
                # learn at least 2 words
                learn = False

            
            if len(message['text'].split()) > 50:
                # spam received ignore
                return

            if 'http' in message['text']:
                # spam received ignore
                return
            
            self.log_learn(message['text'])

            rispondi = True
            if chat_id in self.groupmode:
                gm = self.groupmode[chat_id]
                if gm == 2:
                    if not 'lampone' in message['text'].lower():
                        if len(message['text'].split()) > 3:
                            rispondi = True if randrange(0,3) == 0 else False
                        else:
                            rispondi = True if randrange(0,7) == 0 else False
                if gm == 3:
                    if not 'lampone' in message['text'].lower():
                        rispondi = False
            else:
                # default set group mode to 2
                if chat_id < 0:
                    #self.sendMessage(chat_id,'Lampone is here!\ndefault group mode is 2, use /groupmode to switch')
                    self.groupmode[chat_id] = 2
                    rispondi = False
                        
                        
            if rispondi:
                self.action_typing(chat_id)
                reply = self.megahal.get_reply(message['text'])
                #self.log('%s --- MSG TO:%s --- %s' % (datetime.now(),message['from'],reply))
                self.sendMessage(chat_id,reply)
    
                for ll in self.listening:
                    self.sendMessage(ll,"--> %s" % reply)
            else:
                # learn always
                self.megahal.learn(message['text'])
            
    

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

        l = Lampone(
            cf['telegram']['token'],
            admins=cf['telegram']['admins']
        )
        #l.clearWebHook()
        print(l.get('getMe'))
            
        for admin in l.admins:
            # notify admins when online
            l.action_typing(admin)
            l.sendMessage(admin,"Lampone is Online!")
            l.listening.append(admin)
            
        l.getUpdates()
