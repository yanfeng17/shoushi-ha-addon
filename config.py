"""
Configuration module for MediaPipe Gesture Control.

v2.0.0: Simplified to pure gesture recognition system.
Removed: Expression detection, motion detection, visualization.
"""

import os

# ============================================================================
# RTSP Configuration
# ============================================================================
RTSP_URL = os.getenv('RTSP_URL', 'rtsp://admin:password@192.168.1.100:554/stream1')
RTSP_RECONNECT_DELAY = int(os.getenv('RTSP_RECONNECT_DELAY', '5'))

# ============================================================================
# MQTT Configuration
# ============================================================================
MQTT_BROKER = os.getenv('MQTT_BROKER', 'core-mosquitto')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
MQTT_CLIENT_ID = 'gesture_control'

# MQTT Topics
MQTT_DISCOVERY_PREFIX = 'homeassistant'
MQTT_STATE_TOPIC = 'mediapipe/gesture/state'
MQTT_DEVICE_NAME = 'gesture_control'

# ============================================================================
# Video Processing Configuration
# ============================================================================
FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', '320'))
FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', '240'))
TARGET_FPS = int(os.getenv('TARGET_FPS', '15'))
SKIP_FRAMES = int(os.getenv('SKIP_FRAMES', '1'))

# ============================================================================
# Gesture Recognition Configuration
# ============================================================================
GESTURE_CONFIDENCE_THRESHOLD = float(os.getenv('GESTURE_CONFIDENCE_THRESHOLD', '0.5'))
GESTURE_MIN_DETECTIONS = int(os.getenv('GESTURE_MIN_DETECTIONS', '2'))
GESTURE_COOLDOWN = float(os.getenv('GESTURE_COOLDOWN', '1.5'))

# ============================================================================
# MediaPipe Gesture Recognizer Configuration (v2.1.2)
# ============================================================================
MAX_NUM_HANDS = 1
MIN_DETECTION_CONFIDENCE = float(os.getenv('MIN_DETECTION_CONFIDENCE', '0.5'))  # Google default
MIN_TRACKING_CONFIDENCE = float(os.getenv('MIN_TRACKING_CONFIDENCE', '0.5'))    # Google default

# ============================================================================
# Gesture Toggles (8 gestures: 7 built-in + 1 custom)
# v2.1.0: Google Gesture Recognizer (7 built-in gestures)
# v2.1.3: Added custom OK_SIGN gesture
# ============================================================================
ENABLED_GESTURES = {
    # 7 built-in gestures from Google Gesture Recognizer
    'CLOSED_FIST': os.getenv('ENABLE_CLOSED_FIST', 'true').lower() == 'true',
    'OPEN_PALM': os.getenv('ENABLE_OPEN_PALM', 'true').lower() == 'true',
    'POINTING_UP': os.getenv('ENABLE_POINTING_UP', 'true').lower() == 'true',
    'THUMBS_DOWN': os.getenv('ENABLE_THUMBS_DOWN', 'true').lower() == 'true',
    'THUMBS_UP': os.getenv('ENABLE_THUMBS_UP', 'true').lower() == 'true',
    'PEACE': os.getenv('ENABLE_PEACE', 'true').lower() == 'true',
    'I_LOVE_YOU': os.getenv('ENABLE_I_LOVE_YOU', 'true').lower() == 'true',
    # Custom gesture
    'OK_SIGN': os.getenv('ENABLE_OK_SIGN', 'true').lower() == 'true',
}

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
