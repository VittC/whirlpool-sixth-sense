import asyncio
import logging
import signal
import threading
import time
from typing import final
import nest_asyncio
import yamlparser
from bridge import Bridge
from mqtt import Mqtt
#from dev import device
from alldevs import devices
import json 

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

def mqtt_thread (mqtt_client, br, list, stop_event, sublist=None):
    sub = True
    while not stop_event.is_set():
        try:
            packet = br._queue.get()
            if packet is not None:
                devname = packet["devname"]
                for i in list:
                    mqtt_client.publish(devname,i,packet[str(i)])
                if (sub and sublist != None):
                    for s in sublist:
                        mqtt_client.subscribe (devname, s)
                    mqtt_client.subscribe (devname, "json")
                    sub = False
            br._queue.task_done()
        except Exception as e:
            _LOGGER.error("publish_thread exited with error: "+str(e))
    #_LOGGER.info("Leaving mttq loop")

def whirlpool_thread(br, list, mloop, stop_event,s):
        t = 0
        while not stop_event.is_set():
            try:
                if(time.time()-t > s):
                    t = time.time()
                    try: 
                        _a = asyncio.run_coroutine_threadsafe(br.reload(), mloop).result(timeout=s)
                    except TimeoutError:
                        _LOGGER.warning("br.reload() timed out")
                    br.getattrs(list)
            except Exception as e:
                _LOGGER.error("whirlpool_thread exited with error: "+str(e))
        #_LOGGER.info("Leaving whirlpool loop")

def whirlpool_recv_thread (br, mloop, mqtt_client, d, stop_event):
    while not stop_event.is_set():
        try:
            packet = mqtt_client._queue.get()
            if packet is not None:
                _LOGGER.info("Processing mqtt message")
                devname=packet["devname"]
                attr = str(packet["attr"])
                val = str(packet["value"].decode("utf-8"))
                if ( attr!="json" and not check_range(d, attr, val)):
                    _LOGGER.warning("Value " + str(val) + " not in range")
                if (attr == "json"):
                    j = json.loads(val) 
                    attr = None
                    val = None
                else:
                    j = None               
                try: 
                    _result = asyncio.run_coroutine_threadsafe(br.async_setattr(attr,val,j), mloop).result(timeout=30)
                except TimeoutError:
                    _LOGGER.warning("br.settattr() timed out")         
                    _result = False                    
                if not _result:
                    _LOGGER.warning("br.settattr() failed")
                else:
                    mqtt_client._queue.task_done()
        except Exception as e:
            _LOGGER.error("whirlpool_recv_thread exited with error: "+str(e))
    #_LOGGER.info("Leaving whirlpool recv loop")

def check_range(d, attr, val):  
    try: 
        if (d[str(attr)]["type"]=="char"):
            #print (str(attr)+"is of type char")
            for i in d[str(attr)]["options"]:
                if (i["name"]==val):
                    return True
        else:
            #print ("value:" + val + "Range: " + d[str(attr)]["min"] + "-" + d[str(attr)]["max"])
            if (d[str(attr)]["max"]!='' and d[str(attr)]["min"]!=''):
                return (int(val)<int(d[str(attr)]["max"]) and int(val)>int(d[str(attr)]["min"]))
            else:
                return True
    except Exception as e:
        _LOGGER.error("check_range failed with exception " + str(e))
        pass
    return False

if __name__ == "__main__":
    config = yamlparser.load_yaml('config.yaml')
    Config = config.get("whirlpool", None)
    if (Config == None):
        raise "Config whirlpool section is null"
        
    username = Config.get("username", None)
    password = Config.get("password", None)
    polling = Config.get("polling", 30)
    channels = Config.get("channels",None)
   
    br = Bridge(username,password)
    mqtt_client = Mqtt(config)
    mqtt_client.connect()
    def exit_handler(s,a):
       
        stop_event.set()
        mqtt_client.disconnect()
        loop.run_until_complete(br.disconnect())
        t1.join()
        t2.join()
        t3.join()
        loop.stop()
        mqtt_client.loop_stop()
        
       
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)
    stop_event = threading.Event()
    loop = asyncio.new_event_loop() 
    asyncio.set_event_loop(loop)
    nest_asyncio.apply(loop)
    br.start(loop)
    
    device = devices.get(str(br._model),None)
    if device is None:
        _LOGGER.error("Device configuration not found.")
        signal.raise_signal( signal.SIGINT )
        

    list = []
    sublist = []
    if channels == None:
        for d in device:
            list.append(d["name"])
            if d["has_command"]:
                sublist.append(d["name"])
    else:
        for c in channels:
            if (device[str(c)] != None):
                list.append(c)
                if (device[str(c)]["has_command"]):
                    sublist.append(c)
    
    t1 = threading.Thread(target=mqtt_thread, args=[mqtt_client, br, list, stop_event, sublist])
    t1.daemon = True
    t1.start()

    t2 = threading.Thread(target=whirlpool_thread, args=[br, list, loop, stop_event, polling])
    t2.daemon = True
    t2.start()

    t3 = threading.Thread(target=whirlpool_recv_thread, args=[br, loop, mqtt_client, device, stop_event])
    t3.daemon = True
    t3.start()
   

try:
    loop.run_forever()         
except:
    _LOGGER.info("Quit")
    loop.close()
   
        
        

   
