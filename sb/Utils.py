
from enum import Enum,unique
from sb.models import Customer
from wxpy import *
from django.db import models
from io import StringIO
import time
from random import randint

@unique
class ProductCode(Enum):
    SB = 1
    GJJ = 2
    OTHER = 4


@unique
class CustomerStatusCode(Enum):
    Disabled = 0
    SB = 1
    GJJ = 2
    OTHER = 4


@unique
class CustomerOperations(Enum):
    ADD = 1
    REORDER =2
    REMOVE = 3



DEFAULT_PAGE_COUNT = 30    


def SendPushMessage(customers, message):
    cNames = None
    if isinstance(customers, models.QuerySet):
        cNames = (c.name for c in customers)
    
    else:
        cNames = customers
    
    bot = Bot(cache_path=True, qr_path='QR.png')
    bot.enable_puid(path='hyhr_wxpy_puid.pkl')
    msgIO = StringIO()
    failed = []
    for name in cNames:
        try:
            msgIO.write('准备发给 {}'.format(name))
            friends = bot.friends().search(name)
            found = False
            for friend in friends:
                #print(friend.name)
                if friend.nick_name == name or friend.name == name:
                    friend.send(message.format(name))
                    msgIO.write('成功发消息给{}'.format(name))
                    found = True
                    
                    break
            if not found:
                msgIO.write('没到找{},自己手工确认一下！'.format(name))
                failed.append(name)               
        except Exception as ex:
            msgIO.write('发消息给{}失败了，稍后自己重新发一下...'.format(name))
            msgIO.write('失败信息：{}'.format(ex))
            failed.append(name)
        time.sleep(randint(0,3))
    
    if len(failed) > 0:
        msgIO.write('以下{}人没有发送成功，需手动发送.'.format(len(failed)))
        for fn  in failed:
            msgIO.write('\t ' + fn)
    else:
        msgIO.write('全部发送成功.')

    return msgIO