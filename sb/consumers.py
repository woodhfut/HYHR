from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
import json
from wxpy import Bot
from django.conf import settings
from . import Utils, killableThread
import os
import threading
import asyncio
from multiprocessing.pool import ThreadPool
from random import randint
import logging

logger = logging.getLogger(__name__)


class WebchatBroadcastConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.scope['session'].save()
        await self.accept()
    
    async def close(self, code):
        print('websocket closed.')

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        cmd = text_data_json.get('command', None)
        if cmd: 
            if cmd == 'GETQR':
                print(self.scope['session']._get_session_key())
                sesskey = self.scope['session']._get_session_key()
                vqrpath = 'HYHR/img/QR_{}.png'.format(sesskey)
                if settings.DEBUG:
                    qrpath = os.path.join(settings.STATICFILES_DIRS[0], vqrpath)
                else:
                    qrpath = os.path.join(settings.STATIC_ROOT, vqrpath)
                print(qrpath)
                if os.path.exists(qrpath):
                    try:
                        os.remove(qrpath)
                    except:
                        pass
                #check wxpy cache file
                #if not Utils.isWXCacheExists(sesskey):
                if Utils.isWXCacheExpired(sesskey):
                    Utils.handleExpiredWXCache(sesskey)

                    # pool = ThreadPool(processes=1)
                    # rst = pool.apply_async(Utils.getWXBot, (qrpath, sesskey))
                    t = killableThread.ThreadWithExc(target=Utils.getWXBot, args=(qrpath, sesskey))
                    t.start()
                    counter = 30
                    while counter >0:
                        if os.path.exists(qrpath):
                            print('find the QR.')
                            await self.send(json.dumps({
                                'command': 'GETQR',
                                'message': vqrpath,
                            }))
                            break
                        else:
                            counter -=1
                            await asyncio.sleep(1)
                            
                        print('count: ' + str(counter))
                    if counter == 0:
                        await self.send(json.dumps({
                            'command': 'ERROR',
                            'message': 'Couldnot get QR code in 30 sec, refresh to try again.',
                        }))
                        self.close(code='NO_QR')
                        t.raiseExc(killableThread.KillaboutThreadException)
                        return
                    else:
                        print('wait client to scan the QR to create wxbot object.')
                        counter = 60
                        while not t.ready() and counter > 0:
                            #print('not ready, sleep 1 sec')
                            await asyncio.sleep(1)
                            counter -=1
                        
                        if counter == 0:
                            #even after 60 sec, client still doesn't scan the QR to login, exit. 
                            await self.send(json.dumps({
                                'command': 'ERROR',
                                'message': 'You should scan the QR to login in 60 sec, refresh to try again.',
                            })) 
                            self.close(code='TIMEOUT')
                            t.raiseExc(killableThread.KillaboutThreadException)
                            return
                        else:
                            self._wxbot = t.get()
                            print(self._wxbot)
                            friends = [f.name for f in self._wxbot.friends()]
                            await self.send(json.dumps({
                                'command': 'GETFRIENDS',
                                'message': friends,
                            }))
                else:
                    self._wxbot = Utils.getWXBot(qrpath, sesskey)
                    friends = [f.name for f in self._wxbot.friends()]
                    await self.send(json.dumps({
                            'command': 'GETFRIENDS',
                            'message': friends,
                        }))
            elif cmd == 'SENDMSG': 
                msg = text_data_json.get('message', '寰宇向你致以亲切问候.')
                print('got msg ' + msg)
                if msg == '':
                    msg = '寰宇向你致以亲切问候.'

                frds = text_data_json.get('friends', None)
                
                for name in frds:
                    try:
                        friends = self._wxbot.friends().search(name)
                        found = False
                        for friend in friends:
                            if friend.name == name:
                                found = True
                                friend.send(msg)
                                await self.send(json.dumps({
                                    'command' : 'SENDSTATUS',
                                    'message': (name, True),
                                }))
                                #logger.info('Sending message to {} successfully.'.format(name))
                                break
                        if not found:
                            await self.send(json.dumps({
                                'command': 'SENDSTATUS',
                                'message': (name, False),
                            }))    
                            #logger.warn('Sending message to {} failed.'.format(name))           
                    except:
                        await self.send(json.dumps({
                                'command': 'SENDSTATUS',
                                'message': (name, False),
                            }))    
                        #logger.warn('Sending message to {} failed.'.format(name))           
                    asyncio.sleep(randint(0,3))               
        else:
            pass
