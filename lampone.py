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
  
  TODO: sarebbe utile fare database multipli in base alla lingua parlata:  https://pypi.python.org/pypi/guess_language-spirit/0.5.1
  una volta decisa la lingua va impostato lo stemmer corretto
  http://pythonhosted.org/pyenchant/
  
  su mac ricordarsi di installare tutti i dizionari: brew install aspell --with-all-langs
  
  
"""
import os,sys
from wrapper import Bot
from cobe.brain import Brain
from threading import Timer
from shutil import copy2
from datetime import datetime,timedelta
from configparser import ConfigParser
from random import randrange
from threading import Thread
from guess_language import guess_language_name
from Stemmer import algorithms as stemmer_languages
import logging
import re

logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__)


class Lampone(Bot):
    
    listening = []
    badboys = {}
    groupmode = {}
    admins = []
    reply_time = 500
    brains = {}
    multibrain = False # works better with a single one
    
    def __init__(self, token,admins=""):
        super().__init__(token) # init classe principale
        
        self.admins = [ int(x) for x in admins.split(",") ]
        self.languages = stemmer_languages()

        if not os.path.exists(os.path.join(os.path.split(__file__)[0],'brains')):
            os.mkdir(os.path.join(os.path.split(__file__)[0],'brains'))
           

    def log_learn(self,msg):
        # TODO: loggare solo quelle di un certo peso
        try:
            with open(os.path.join(os.path.split(__file__)[0],"lampone_learn.txt"),"ab") as logfile:
                logfile.write(msg.encode('utf8'))
                logfile.write(b"\n")
        except Exception as e:
            logging.error(e)

    def learn_lines(self,message):
        # manual learn
        lines = message['text'].splitlines()[1:]
        for l in lines:
            logging.info("learning: %s" % l)
            self.learn(l)
            self.log_learn(l)

    def learn(self,msg):
        # learn message
        if self.multibrain:
            lang = guess_language_name(msg).lower()
        else:
            lang = 'multi'

        try:
            if not lang in self.brains:
                self.brains[lang] =  Brain(os.path.join(os.path.split(__file__)[0],"brains","lampone_%s.brain" % lang))
                if self.brains[lang]  in self.languages:
                    brain.set_stemmer(lang)
            self.brains[lang].learn(msg)
        except Exception as e:
            logging.error("ERR - learn - %s" % e )
             
        return lang
    
    
    def reply(self,lang,msg):
        # reply message
        
        if self.multibrain:
            lang = guess_language_name(msg).lower()
        else:
            lang = 'multi'

        if not lang in self.brains:
            self.brains[lang] =  Brain(os.path.join(os.path.split(__file__)[0],"brains","lampone_%s.brain" % lang))
            if lang in self.languages:
                self.brains[lang] .set_stemmer(lang)
            
        return self.brains[lang] .reply(msg,loop_ms=self.reply_time)
    
    def sendMessageThreaded(self,chat_id,text,disable_web_page_preview=True,reply_to_message_id=None,reply_markup=None):
        Thread(target=self.sendMessage,kwargs={
            'chat_id':chat_id,
            'text':text,
            'disable_web_page_preview':disable_web_page_preview,
            'reply_to_message_id':reply_to_message_id,
            'reply_markup':reply_markup
        }).start()

    def autolearn(self):
        # learns from previous chats
        
        self.sendMessageThreaded(self.admins[0],"Autolearn Start")
        lines = []
        with open("lampone_learn.txt","rb") as logfile:
            for l in logfile.readlines():
                try:
                    l = l.decode('utf8').strip()
                    ok = True
                    if 'lampone' in l.lower(): ok = False
                    if 'http' in l.lower(): ok = False
                    if len(l) < 3: ok = False
                    if l.lower() in lines: ok = False
                    if len(l.split()) < 3: ok = False
                    if '@' in l: ok = False
                        
                    if ok:
                        lang = self.learn(l)
                        logging.info("learned: %s -- %s" % (lang,l))
                        lines.append(l.lower())
                except Exception as e:
                    logging.error("ERR - autolearn - %s" % e )
                    

        with open("lampone_learn_cleaned.txt","wb") as logfile:
            for l in lines:
                try:
                    logfile.write((l + "\n").encode('utf8'))
                except Exception as e:
                    logging.error("ERR - autolearn write - %s" % e )
                
        self.sendMessageThreaded(self.admins[0],"Autolearn Finished")
        self.listening.append(self.admins[0])

        
    def parsedocument(self,chat_id,message):
        logging.info("Documento ricevuto da %s" % message['from'] )

    def parsemessage(self,chat_id,message):
        logging.info("Messaggio ricevuto da %s" % message['from'] )
        logging.info(message['text'])
        if self.stop:
            # stopping, ignore messages
            return
        

        #if self.lastbackup != datetime.now().hour:
        #    self.lastbackup = datetime.now().hour
        #    self.backupBrain()

        if message['text'].startswith('/learn') and message['from']['id'] in self.admins:
            self.learn_lines(message)
            return
        
        if message['text'].startswith('/update') and message['from']['id'] in self.admins:
            """
            Bot updates from git and then quits, 
            to reload automatically use a cron like this:
            */1 * * * * [ `ps aux | grep python3 | grep lampone | grep -v grep | wc -l` -eq 0 ] && /usr/bin/python3 /home/pi/lampone/lampone.py  > /dev/null 2>&1
            """
            self.sendMessageThreaded(chat_id,"Updating...")
            res = os.popen("cd %s && git fetch --all && git reset --hard origin" % os.path.join(os.path.split(__file__)[0])).read()
            self.sendMessageThreaded(chat_id,res)
            self.sendMessageThreaded(chat_id,"Restarting...")
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
            self.sendMessageThreaded(chat_id,"Learning %s fortunes"%count)
            for x in range(count):
                txt = os.popen('fortune | grep -v "\-\-\s.*" | grep -v ".*:$" | grep -v ".*http://"').read()
                if txt:
                    self.learn(txt)
            self.sendMessageThreaded(chat_id,"Done")
            return        
        
        if message['text'] == "/start":
            self.sendMessageThreaded(chat_id,"Welcome to Lampone Bot")
            return

        if message['text'].startswith("/rt")  and message['from']['id'] in self.admins:
            if message['text'].split()[-1].isdigit():
                val = int(message['text'].split()[-1])
                if val < 30:
                    self.reply_time = int(message['text'].split()[-1])*1000
                    self.sendMessageThreaded(chat_id,"Reply Timer set to %s seconds" % val)
                else:
                    self.sendMessageThreaded(chat_id,"Bad n. of seconds: %s" % message['text'].split()[-1] )
            else:
                self.sendMessageThreaded(chat_id,"Bad n. of seconds: %s" % message['text'].split()[-1] )
            return

        if message['text'] == "/groupmode":
            if chat_id > 0:
                self.sendMessageThreaded(chat_id,"This is not a group.")
            else:
                self.sendMessageThreaded(chat_id,"Select Group Mode:",reply_markup={'keyboard':[['/g1 Respond all messages'],['/g2 Respond some messages'],['/g3 Respond only for Lampone'],]})
            return
        
        if message['text'].startswith("/g1"):
            if chat_id > 0:
                self.sendMessageThreaded(chat_id,"This is not a group.",reply_markup={'hide_keyboard':True})
            else:
                self.groupmode[chat_id] = 1
                self.sendMessageThreaded(chat_id,"Groupmode 1 enabled",reply_markup={'hide_keyboard':True})
            return
        
        if message['text'].startswith("/g2"):
            if chat_id > 0:
                self.sendMessageThreaded(chat_id,"This is not a group.",reply_markup={'hide_keyboard':True})
            else:
                self.groupmode[chat_id] = 2
                self.sendMessageThreaded(chat_id,"Groupmode 2 enabled",reply_markup={'hide_keyboard':True})
            return
        
        if message['text'].startswith("/g3"):
            if chat_id > 0:
                self.sendMessageThreaded(chat_id,"This is not a group.",reply_markup={'hide_keyboard':True})
            else:
                self.groupmode[chat_id] = 3
                self.sendMessageThreaded(chat_id,"Groupmode 3 enabled",reply_markup={'hide_keyboard':True})
            return        
        
        if message['text'] == "/help":
            self.sendMessageThreaded(chat_id,"This is a simple AI bot, just talk to him or invite to your group and he will learn and respond\nTry /groupmode for limit group interaction")
            self.sendMessageThreaded(chat_id,"Vote for lampone here if you like it: https://telegram.me/storebot?start=lamponebot")
            return        
        
        if message['text'] == "/stop":
            self.sendMessageThreaded(chat_id,"Command not needed, just close the chat :)")
            return        
        
        if message['text'] == "/autolearn" and message['from']['id'] in self.admins:
            try:
                self.autolearn()
            except Exception as e:
                logging.error("ERR - /autolearn - %s" % e )
                
            return              
        
        if message['text'] == "/listen" and message['from']['id'] in self.admins:
            self.sendMessageThreaded(chat_id,"Listening enabled, stop with /stoplisten")
            if not chat_id in self.listening:
                self.listening.append(chat_id)
            return        
        
        if message['text'] == "/stoplisten" and message['from']['id'] in self.admins:
            self.sendMessageThreaded(chat_id,"Listening stopped")
            if chat_id in self.listening:
                self.listening.pop(self.listening.index(chat_id))
            return                
        
        if not message['text'].startswith('/'):
            for ll in self.listening:
                self.sendMessageThreaded(ll,"<-- %s" % message['text'])

            delta = delta = datetime.now() - datetime.fromtimestamp(message['date'])
            learn = True
            rispondi = True

            text = message['text'].strip().strip("'").strip('"')            
            
            # se passati più di 30 minuti non rispondo, probabilmente è crashato il bot
            if delta.total_seconds()/60 > 30.0:
                rispondi = False

            # skip links 
            
            if 'http' in text.lower(): learn = False # don't learn urls
            if re.match('.*[\w\d]+\.\w{2,4}',text) : learn = False # try don't learn hostnames
            if len(text.split()) < 2: learn = False # don't learn shorter phrases
            if re.match('.*@\w+',text): learn = False # don't learn usernames
            if len(text.split()) > 100: learn = False # don't learn too long messages

            
            if chat_id in self.groupmode:
                gm = self.groupmode[chat_id]

                if gm == 2:
                    # responds sometimes
                    if not 'lampone' in text.lower():
                        rispondi = True if randrange(0,5) == 0 else False
                        
                if gm == 3:
                    # responds only if asked
                    if not 'lampone' in text.lower():
                        rispondi = False
            else:
                if chat_id < 0:
                    # default set group mode to 2 in groups
                    self.groupmode[chat_id] = 2
                    rispondi = False

            try: 
                logging.info("Learn: %s, Rispondi: %s" % (learn,rispondi) )
                if learn:
                    self.log_learn(text) # log messages for retrain
                    lang = self.learn(text)
                else:
                    if self.multibrain:
                        lang = guess_language_name(text).lower()
                    else:
                        lang = 'multi'
             
                if rispondi:
                    # se proprio devo rispondere
                    self.action_typing(chat_id)
                    try:
                        logging.info("get reply l:%s text:%s" % (lang,text))
                        reply = self.reply(lang,text)
                    except Exception as e:
                        # manda un messaggio a caso se non gli piace ?
                        logging.error("ERR - rispondi - %s" % e )
                        reply = self.reply(lang,"")

                    # rispondi se e diversa, copiare no buono
                    if not reply.lower().strip('.').strip('!').strip('?').strip() == text.lower().strip('.').strip('!').strip('?').strip():
                        self.sendMessageThreaded(chat_id,reply)
                    else:
                        # manda un messaggio a caso invece di ripetere
                        reply = self.reply(lang,"")
                        if reply.strip():
                            self.sendMessageThreaded(chat_id,reply)
                        

                    for ll in self.listening:
                        self.sendMessageThreaded(ll,"--> %s" % reply)

            except Exception as e:
                logging.error("ERR - try learn/rispondi - %s" % e )
                self.sendMessageThreaded(self.admins[0],"Brain error: %s\nbad text:\n%s" % (e,text))
            
    

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
        cf.add_section("brain")
        cf.set("brain","multi",True)
        with open(os.path.join(os.path.split(__file__)[0],"lampone.conf"),"w") as cf_file:
            cf.write(cf_file)
    

    if cf['telegram']['token'] == "YOUR TOKEN HERE":
        logging.info("Token not defined, check config!")    
    else:

        l = Lampone(
            cf['telegram']['token'],
            admins=cf['telegram']['admins']
        )
        #l.clearWebHook()
        logging.info(l.get('getMe'))
            
        for admin in l.admins:
            # notify admins when online
            l.action_typing(admin)
            l.sendMessageThreaded(admin,"Lampone is Online!")
            
        l.getUpdates()
