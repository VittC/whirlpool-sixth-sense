from whirlpool.appliance import Appliance
import logging
from typing import Callable
from queue import Queue
from whirlpool.auth import Auth
import asyncio


logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

class Ap (Appliance):
    def __init__(self, auth, said, attr_changed: Callable):
        Appliance.__init__(self, auth, said, attr_changed)

    def get_online(self):
        return self.get_attribute("Online")==1
    
    def get_attr(self, attr):
        try:
            return self.get_attribute(attr)
        except:
            _LOGGER.warn("Wrong attribute: ",str(attr))
            return None
    
    def get_attr_list (self, list):
        out = {}
        for e in list:
            out[e]=self.get_attr(e)
        return out

   

class Bridge:

    def __init__(self, username, password, list):
          
        self._username = username
        self._password = password
        self.attr_list = list
        self.val_list = []
        self.connected = False
        self.ap = None
        self._name = None
    
    def start(self,loop):
        self._queue = Queue()
        if (not self.connected):
            loop.run_until_complete(self.connect())
            self._name = loop.run_until_complete(self.ap.fetch_name())
        self.getattrs()
            

    async def connect (self):
        def _do():
            _LOGGER.info("updated")
        self.auth = Auth(self._username, self._password)
        await self.auth.load_auth_file()
        said = self.auth.get_said_list()[0]
        self.ap = Ap(self.auth, said, _do())
        await self.ap.connect()
        self.connected = self.ap.get_online()
    
    def getattrs (self):
        vals = self.ap.get_attr_list(self.attr_list)
        vals["devname"]=self._name
        if (vals["devname"]==None):
            _LOGGER.warn("data not received")
            return        
        self._queue.put(vals)
       
    
    def setattr(self, loop,  attr=None, val=None, dom=None):
        future = asyncio.run_coroutine_threadsafe(self.async_setattr(attr, val, dom), loop, timeout = 30)
        try:  
            result = future.result()
        except:
            _LOGGER.info("Last command had not been set")
            future.cancel()
            result = False
        return result        

    async def async_setattr(self,attr=None, val=None, j=None):
        if (j==None):
            status = await  self.ap.send_attributes({attr: str(val)})
        else:
            status = await self.ap.send_attributes({j})
        self.getattrs()
        return status

    async def disconnect (self):
        await self.ap.disconnect()
        self.auth.cancel_auto_renewal()
        self._queue.put(None)

    async def reload (self):
        _LOGGER.info("reload datas")
        await self.ap.fetch_data()
        return True


