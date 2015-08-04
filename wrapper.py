#!/usr/bin/env python
#coding:utf-8
"""
  Author: Marco Mescalchin  --<>
  Purpose: Wrapper to telegram bot api
  Created: 06/25/15
"""
import requests,json,os
from time import sleep
import logging
logging.getLogger(__name__)
DEBUG_GET_POST = False

########################################################################
class Bot:
    """"""
    api_url = "https://api.telegram.org"
    offset = 0 
    stop = False
    #----------------------------------------------------------------------
    def __init__(self,token):
        """Constructor"""
        logging.info("Telegram Bot Starting")
        self.token = token
  
    def setWebhook(self,whurl):
        r = self.post('setWebhook',{'url':whurl})
        logging.info("Telegram WebHook Setup: %s" % r)
            
    def clearWebHook(self):
        r = self.post('setWebhook',{'url':''})
        logging.info("Telegram WebHook Cleared: %s" % r)            
  
    def get(self,method,params=None):
        
        if DEBUG_GET_POST: logging.info("GET --> %s %s" % (method,params))
        
        r = requests.get("%s/bot%s/%s" % (self.api_url,self.token,method),params,timeout=30)
        
        if DEBUG_GET_POST: logging.info("GET <-- %s" % r)
            
        if r.status_code == requests.codes.ok:
            j = r.json()
            if j['ok']:
                if j['result']:
                    return j['result']
        else:
            logging.info("GET Error %s" % r.text)
                    
        
        return False
  
    def post(self,method,params=None,files=None):
        logging.debug("POST --> %s %s" % (method,params))
        r = requests.post("%s/bot%s/%s" % (self.api_url,self.token,method),params,files=files,timeout=60)
        logging.debug("POST <-- %s" % (r))
            
        if r.status_code == requests.codes.ok:
            j = r.json()
            if j['ok']:
                if j['result']:
                    return j['result']
        else:
            logging.error("POST Error %s" % r.text)
        return False        
  
    def webhook(self,request):
        data = json.loads(request.body.decode('utf8'))
        logging.info("<-- WH %s" % data['message'])
        message_received.send(self,message=data['message'])
        return 'ok'
  
    def action_typing(self,chat_id):
        self.post('sendChatAction',{'chat_id':chat_id,'action':'typing'})

    def action_upload_photo(self,chat_id):
        self.post('sendChatAction',{'chat_id':chat_id,'action':'upload_photo'})
        
  
    def forwardMessage(self,chat_id,from_chat_id,message_id):
        r = self.post('forwardMessage',{
            'chat_id':chat_id,
            'from_chat_id':from_chat_id,
            'message_id':message_id
        })
        
    def sendMessage(self,chat_id,text,disable_web_page_preview=True,reply_to_message_id=None,reply_markup=None):
        r = self.post('sendMessage',{
            'chat_id':chat_id,
            'text':text,
            'disable_web_page_preview':disable_web_page_preview,
            'reply_to_message_id':reply_to_message_id,
            'reply_markup':json.dumps(reply_markup)
        })        
        #TODO: check result

        
    def sendPhoto(self,chat_id,photo,caption=None,reply_to_message_id=None,reply_markup=None):
        r = self.post('sendPhoto',{
            'chat_id':chat_id,
            'caption':caption,
            'reply_to_message_id':reply_to_message_id,
            'reply_markup':json.dumps(reply_markup)
        },files={'photo':('image.jpg', photo, 'image/jpeg', {'Expires': '0'})})        
        #TODO: check result
    
    
    def parsemessage(self,chat_id,message):
        # parse message here
        pass
    
    def parsepicture(self,chat_id,message):
        # parse message here
        pass
    
    def parsedocument(self,chat_id,message):
        # parse document here but no api from telegram yet
        pass    
    
    def getUpdates(self):
        timeout = 60
        geturl =  "%s/bot%s/getUpdates" % (self.api_url,self.token)
        while True:
            if self.stop:
                try:
                    # ask for the next message before exit ( if not it will loop )
                    dt = dict(offset=self.offset, timeout=timeout)
                    j = requests.post(geturl, data=dt, timeout=None).json()
                except:
                    sleep(60)
                break                 
            try:
                dt = dict(offset=self.offset, timeout=timeout)
                try:
                    j = requests.post(geturl, data=dt, timeout=None).json()
                except ValueError:  # incomplete data
                    continue
                if not j['ok'] or not j['result']:
                    continue
                for r in j['result']:
                    m = r['message']
                    cid = m['chat']['id']
                    if 'text' in m:
                        self.parsemessage(cid,m)
                    if 'photo' in m:
                        self.parsepicture(cid,m)
                    if 'document' in m:
                        self.parsedocument(cid,m)                    
                    self.offset = r['update_id'] + 1
           
            except:
                sleep(60)
