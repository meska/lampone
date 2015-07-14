#!/usr/bin/env python
#coding:utf-8
"""
  Author: Marco Mescalchin  --<>
  Purpose: Wrapper to telegram bot api
  Created: 06/25/15
"""
import requests,json,os
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
        print("Telegram Bot Starting")
        self.token = token
  
    def setWebhook(self):
        whurl = "%s" % (os.getenv('TELEGRAM_WEBHOOK_URL'))
        r = self.post('setWebhook',{'url':whurl.replace('http:','https:')})
        print("Telegram WebHook Setup: %s" % r)
            
    def clearWebHook(self):
        r = self.post('setWebhook',{'url':''})
        print("Telegram WebHook Cleared: %s" % r)            
  
    def get(self,method,params=None):
        
        if DEBUG_GET_POST: print("GET --> %s %s" % (method,params))
        
        r = requests.get("%s/bot%s/%s" % (self.api_url,self.token,method),params,timeout=30)
        
        if DEBUG_GET_POST: print("GET <-- %s" % r)
            
        if r.status_code == requests.codes.ok:
            j = r.json()
            if j['ok']:
                if j['result']:
                    return j['result']
        else:
            print("GET Error %s" % r.text)
                    
        
        return False
  
    def post(self,method,params=None,files=None):
        
        if DEBUG_GET_POST: print("POST --> %s %s" % (method,params))

        r = requests.post("%s/bot%s/%s" % (self.api_url,self.token,method),params,files=files,timeout=60)
        
        if DEBUG_GET_POST: print("POST <-- %s" % (r))
            
        if r.status_code == requests.codes.ok:
            j = r.json()
            if j['ok']:
                if j['result']:
                    return j['result']
        else:
            print("POST Error %s" % r.text)
        return False        
  
    def webhook(self,request):
        data = json.loads(request.body.decode('utf8'))
        print("<-- WH %s" % data['message'])
        message_received.send(self,message=data['message'])
        return 'ok'
  
    def action_typing(self,chat_id):
        self.post('sendChatAction',{'chat_id':chat_id,'action':'typing'})

    def action_upload_photo(self,chat_id):
        self.post('sendChatAction',{'chat_id':chat_id,'action':'upload_photo'})
        
  
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
                    pass
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
                    if 'document' in m:
                        self.parsedocument(cid,m)                    
                    self.offset = r['update_id'] + 1
           
            except:
                from time import sleep
                sleep(60)
