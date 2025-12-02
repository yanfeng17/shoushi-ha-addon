import paho.mqtt.client as mqtt
import json
import time
import logging
import config

logger = logging.getLogger(__name__)


class MQTTClient:
    """
    Handles MQTT connection, Home Assistant Auto Discovery, and state publishing.
    
    v2.0.0: Simplified to single gesture sensor only
    """
    
    def __init__(self):
        self.client = mqtt.Client(client_id=config.MQTT_CLIENT_ID)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        
        # Set authentication if provided
        if config.MQTT_USERNAME and config.MQTT_PASSWORD:
            self.client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
        
        self.connected = False
        self.discovery_sent = False
    
    def connect(self) -> bool:
        """
        Connect to MQTT broker with retry logic.
        
        Returns:
            True if connected successfully
        """
        try:
            logger.info(f"连接到 MQTT broker: {config.MQTT_BROKER}:{config.MQTT_PORT}")
            self.client.connect(config.MQTT_BROKER, config.MQTT_PORT, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            for _ in range(10):
                if self.connected:
                    return True
                time.sleep(0.5)
            
            return self.connected
        except Exception as e:
            logger.error(f"连接 MQTT broker 失败: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            logger.info("成功连接到 MQTT broker")
            self.connected = True
            # Send Home Assistant discovery config
            self._send_discovery_config()
        else:
            logger.error(f"连接 MQTT broker 失败，错误代码: {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        logger.warning(f"从 MQTT broker 断开连接，代码: {rc}")
        self.connected = False
        self.discovery_sent = False
    
    def _send_discovery_config(self):
        """
        Send Home Assistant MQTT Discovery configuration.
        Creates single gesture sensor entity.
        """
        if self.discovery_sent:
            return
        
        discovery_topic = f"{config.MQTT_DISCOVERY_PREFIX}/sensor/gesture_control/config"
        
        discovery_payload = {
            "name": "手势控制",
            "unique_id": "gesture_control_sensor",
            "state_topic": config.MQTT_STATE_TOPIC,
            "value_template": "{{ value_json.state }}",
            "json_attributes_topic": config.MQTT_STATE_TOPIC,
            "icon": "mdi:hand-back-right",
            "device": {
                "identifiers": [config.MQTT_DEVICE_NAME],
                "name": "MediaPipe 手势识别",
                "model": "手势检测器 v2.0.0",
                "manufacturer": "Custom",
                "sw_version": "2.0.0"
            }
        }
        
        result = self.client.publish(
            discovery_topic,
            json.dumps(discovery_payload),
            qos=1,
            retain=True
        )
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"手势传感器自动发现配置已发送到 {discovery_topic}")
            self.discovery_sent = True
        else:
            logger.error(f"发送自动发现配置失败: {result.rc}")
    
    def publish_gesture(self, gesture: str, confidence: float):
        """
        Publish gesture state to MQTT.
        
        Args:
            gesture: Gesture name (e.g., "OPEN_PALM", "THUMBS_UP")
            confidence: Detection confidence (0.0 to 1.0)
        """
        if not self.connected:
            logger.warning("未连接到 MQTT broker，跳过发布")
            return
        
        payload = {
            "state": gesture,
            "confidence": round(confidence, 3),
            "timestamp": time.time()
        }
        
        result = self.client.publish(
            config.MQTT_STATE_TOPIC,
            json.dumps(payload),
            qos=1,
            retain=False
        )
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.debug(f"已发布手势: {gesture} (置信度: {confidence:.2f})")
        else:
            logger.error(f"发布手势失败: {result.rc}")
    
    def disconnect(self):
        """Disconnect from MQTT broker and clean up."""
        logger.info("断开 MQTT broker 连接")
        self.client.loop_stop()
        self.client.disconnect()
