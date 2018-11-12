from channels.generic.websocket import WebsocketConsumer
import json
from wxpy import Bot
from django.conf import settings
from . import Utils
import os
import threading
import time


class WebchatBroadcastConsumer(WebsocketConsumer):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(args, kwargs)
    #     self._wxbot = Utils.GetWXBot()

    def connect(self):
        self.scope['session'].save()
        self.accept()
    
    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        cmd = text_data_json.get('command', None)
        if cmd: 
            if cmd == 'GETQR':
                print(self.scope['session']._get_session_key())
                sessKey = self.scope['session']._get_session_key()
                vqrpath = 'HYHR/img/QR_{}.png'.format(sessKey)
                if settings.DEBUG:
                    qrpath = os.path.join(settings.STATICFILES_DIRS[0], vqrpath)
                else:
                    qrpath = os.path.join(settings.STATIC_ROOT, vqrpath)
                print(qrpath)
                #self._wxbot = Utils.GetWXBot(qrpath, sessKey)
                threading.Thread(target=Utils.GetWXBot, args=(qrpath, sessKey)).start()
                counter = 30 #30sec
                
                while counter >0:
                    if os.path.exists(qrpath):
                        self.send(json.dumps({
                            'command': 'GETQR',
                            'message': vqrpath,
                        }))
                        break
                    else:
                        counter -=1
                        time.sleep(1)
                        
                    print('count: ' + str(counter))
                if counter == 0:
                    self.send(json.dumps({
                        'command': 'ERROR',
                        'message': 'Couldnot get QR code in 30 sec, refresh to try again.',
                    }))
        else:
            pass
