#!/usr/bin/env python3
"""
Quick startup test to verify all components load correctly.
Run this to diagnose startup issues.
"""
import sys
import os

print("="*60)
print("STARTUP DIAGNOSTIC TEST")
print("="*60)

# Test 1: Environment variables
print("\n1. Checking environment variables...")
print(f"   RTSP_URL: {os.getenv('RTSP_URL', 'NOT SET')[:50]}...")
print(f"   MQTT_BROKER: {os.getenv('MQTT_BROKER', 'NOT SET')}")
print(f"   MQTT_PORT: {os.getenv('MQTT_PORT', 'NOT SET')}")
print(f"   LOG_LEVEL: {os.getenv('LOG_LEVEL', 'NOT SET')}")

# Test 2: Import modules
print("\n2. Testing imports...")
try:
    import suppress_ffmpeg_logs
    print("   ✓ suppress_ffmpeg_logs imported")
except Exception as e:
    print(f"   ✗ suppress_ffmpeg_logs failed: {e}")

try:
    import cv2
    print(f"   ✓ OpenCV imported (version: {cv2.__version__})")
except Exception as e:
    print(f"   ✗ OpenCV failed: {e}")

try:
    import mediapipe as mp
    print(f"   ✓ MediaPipe imported")
except Exception as e:
    print(f"   ✗ MediaPipe failed: {e}")

try:
    import config
    print(f"   ✓ Config imported")
    print(f"      - FRAME_WIDTH: {config.FRAME_WIDTH}")
    print(f"      - FRAME_HEIGHT: {config.FRAME_HEIGHT}")
    print(f"      - TARGET_FPS: {config.TARGET_FPS}")
except Exception as e:
    print(f"   ✗ Config failed: {e}")

# Test 3: Test MQTT connection
print("\n3. Testing MQTT connection...")
try:
    from src.mqtt_client import MQTTClient
    mqtt = MQTTClient()
    if mqtt.connect():
        print("   ✓ MQTT connected successfully")
        mqtt.disconnect()
    else:
        print("   ✗ MQTT connection failed")
except Exception as e:
    print(f"   ✗ MQTT error: {e}")

# Test 4: Test RTSP connection
print("\n4. Testing RTSP connection...")
try:
    import cv2
    cap = cv2.VideoCapture(config.RTSP_URL, cv2.CAP_FFMPEG)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            print(f"   ✓ RTSP connected and frame captured")
            print(f"      - Frame shape: {frame.shape}")
        else:
            print("   ✗ RTSP opened but cannot read frame")
        cap.release()
    else:
        print("   ✗ Cannot open RTSP stream")
except Exception as e:
    print(f"   ✗ RTSP error: {e}")

# Test 5: Test MediaPipe
print("\n5. Testing MediaPipe initialization...")
try:
    from src.gesture_engine import GestureEngine
    engine = GestureEngine()
    print("   ✓ GestureEngine initialized")
    engine.release()
except Exception as e:
    print(f"   ✗ GestureEngine error: {e}")

print("\n" + "="*60)
print("DIAGNOSTIC COMPLETE")
print("="*60)
