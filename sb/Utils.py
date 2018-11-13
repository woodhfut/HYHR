
from enum import Enum,unique
from sb.models import Customer
from wxpy import *
from django.db import models
from io import StringIO
import time
from random import randint
from collections import OrderedDict
from django.conf import settings
import os
import platform


@unique
class ProductCode(Enum):
    SB = 1
    GJJ = 2
    GS = 4


@unique
class CustomerStatusCode(Enum):
    Disabled = 0
    SB = 1
    GJJ = 2
    GS = 4


@unique
class CustomerOperations(Enum):
    ADD = 1
    REORDER =2
    REMOVE = 3

def getWXCachePath(sesskey):
    return os.path.join(settings.WXPYCACHE_DIR, '{}.pkl'.format(sesskey))

def isWXCacheExists(sesskey):    
    return os.path.exists(getWXCachePath(sesskey))

def getWXCacheMtime(sesskey):
    mtime = None
    if isWXCacheExists(sesskey):
        mtime = os.path.getmtime(getWXCachePath(sesskey))
        print('mtime : {}'.format(mtime))
    return mtime

def isWXCacheExpired(sesskey):
    mtime = getWXCacheMtime(sesskey)
    return not mtime or time.time() - mtime > settings.WXPYSTATUS_DURATION

def handleExpiredWXCache(sesskey):
    if isWXCacheExpired(sesskey): 
        try:
            os.remove(settings.WXPYCACHE_DIR)
        except Exception as ex:
            print('Error occurred while deleting cache file {}.pkl, ex={}. '.format(sesskey, ex))

def getWXBot(qrpath, sesskey):
    cachepath = settings.WXPYCACHE_DIR
    if not os.path.exists(cachepath):
        try:
            os.mkdir(cachepath)
        except:
            raise
    cachefile = os.path.join(cachepath, '{}.pkl'.format(sesskey))
    bot = Bot(cache_path = cachefile ,qr_path=qrpath)
    return bot


def SendPushMessage(bot, customers, message):
    cNames = None
    if isinstance(customers, models.QuerySet):
        cNames = (c.name for c in customers)
    else:
        cNames = customers
    
    result = OrderedDict()
    if not bot:
        print('invalid bot object, return\n')
        return (False, result)
    
    #bot.enable_puid(path='hyhr_wxpy_puid.pkl')
    print('msg to send {}'.format(message))
    failed = []
    for name in cNames:
        try:
            #output +='准备发给 {}\n'.format(name)
            friends = bot.friends().search(name)
            found = False
            for friend in friends:
                #print(friend.name)
                if friend.nick_name == name or friend.name == name:
                    friend.send(message)
                    #print('成功发消息给{},msg:{}\n'.format(name, message))
                    found = True
                    
                    break
            if not found:
                #output += '没到找{},自己手工确认一下！\n'.format(name)
                failed.append(name)               
        except Exception as ex:
            #output += '发消息给{}失败了，稍后自己重新发一下...\n'.format(name)
            #output += '失败信息：{}'.format(ex)
            failed.append(name)
        time.sleep(randint(0,3))
    
    if len(failed) > 0:
        #output += '以下{}人没有发送成功，需手动发送.\n'.format(len(failed))
        for fn  in failed:
            #output += '\t ' + fn + '\n'
            result[fn] = False
        for c in (cn for cn in cNames if cn not in failed):
            result[c] = True
    else:
        #output += '全部发送成功.\n'
        for c in cNames:
            result[c] = True

    return (True, result)