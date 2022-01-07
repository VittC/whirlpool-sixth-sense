import paho.mqtt.client as mqtt
import logging
import ssl
from queue import Queue
_LOGGER = logging.getLogger(__name__)

class Mqtt:
    username = ""
    password = ""
    server = "localhost"
    port = 1883
    ca = None
    tlsvers = None
    prefix = "whirlpool"

    def __init__(self, config):
        if (config == None):
            raise "Config is null"
        mqttConfig = config.get("mqtt", None)
        if (mqttConfig == None):
            raise "Config mqtt section is null"

        self.username = mqttConfig.get("username", "")
        self.password = mqttConfig.get("password", "")
        self.server = mqttConfig.get("server", "localhost")
        self.port = mqttConfig.get("port", 1883)
        self.prefix = mqttConfig.get("prefix", "whirlpool")
        self.ca = mqttConfig.get("ca",None)
        self.tlsvers = self._get_tls_version(
                mqttConfig.get("tls_version","tlsv1.2")
        )
        self._queue = Queue()
        

    def connect(self):
        #_LOGGER.info("Connecting to MQTT server " + self.server + ":" + str(self.port) + " with username (" + self.username + ":" + self.password + ")")
        self._client = mqtt.Client()
        if (self.username != "" and self.password != ""):
            self._client.username_pw_set(self.username, self.password)
        self._client.on_message = self._mqtt_process_message
        self._client.on_connect = self._mqtt_on_connect
        if (self.ca != None):
            self._client.tls_set(
                    ca_certs=self.ca,
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=self.tlsvers
            )

            self._client.tls_insecure_set(False)
        self._client.connect(self.server, self.port, 60)
        self._client.loop_start()

    def subscribe(self, device="+", name="+"):
        topic = self.prefix + "/" + device + "/set/" + name 
        #_LOGGER.info("Subscribing to " + topic + ".")
        self._client.subscribe(topic)

    def publish(self, device, command, status, retain=False):
         PATH_FMT = self.prefix + "/{device}/get/{command}"
         topic = PATH_FMT.format(device=device, command=command)
         self._client.publish(topic, payload=status, qos=0, retain=retain)
     
    def _mqtt_on_connect(self, client, userdata, rc, unk):
        _LOGGER.info("Connected to mqtt server.")
    

    def _mqtt_process_message(self, client, userdata, msg):
         parts = msg.topic.replace(self.prefix+"/","").split("/")
         partlen = len(parts)
         if len(parts) < 3:
             _LOGGER.error("Wrong message")
             return
         device = parts[0]
         command= parts[2] 
         param = msg.payload
         data = {'devname':device, 'attr':command, 'value': param}
         self._queue.put(data)

    def disconnect(self):
        #_LOGGER.info("Disconnecting")
        self._client.disconnect()
        self._client.loop_stop()
        self._queue.put(None)


    def _get_tls_version(self,tlsString):
        switcher = {
            "tlsv1": ssl.PROTOCOL_TLSv1,
            "tlsv1.1": ssl.PROTOCOL_TLSv1_1,
            "tlsv1.2": ssl.PROTOCOL_TLSv1_2
        }
        return switcher.get(tlsString,ssl.PROTOCOL_TLSv1_2)
