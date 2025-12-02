#!/bin/bash
set -e

echo "[INFO] 启动 MediaPipe 手势识别插件..."

# Read configuration from Home Assistant options.json
CONFIG_PATH=/data/options.json

# ============================================================================
# RTSP Configuration
# ============================================================================
export RTSP_URL=$(jq -r '.rtsp_url' $CONFIG_PATH)
export RTSP_RECONNECT_DELAY=$(jq -r '.rtsp_reconnect_delay // 5' $CONFIG_PATH)

# ============================================================================
# MQTT Configuration
# ============================================================================
export MQTT_BROKER=$(jq -r '.mqtt_broker' $CONFIG_PATH)
export MQTT_PORT=$(jq -r '.mqtt_port' $CONFIG_PATH)
export MQTT_USERNAME=$(jq -r '.mqtt_username // ""' $CONFIG_PATH)
export MQTT_PASSWORD=$(jq -r '.mqtt_password // ""' $CONFIG_PATH)

# ============================================================================
# Video Processing Configuration
# ============================================================================
export FRAME_WIDTH=$(jq -r '.frame_width // 320' $CONFIG_PATH)
export FRAME_HEIGHT=$(jq -r '.frame_height // 240' $CONFIG_PATH)
export TARGET_FPS=$(jq -r '.target_fps // 15' $CONFIG_PATH)
export SKIP_FRAMES=$(jq -r '.skip_frames // 1' $CONFIG_PATH)

# ============================================================================
# Gesture Recognition Configuration
# ============================================================================
export GESTURE_CONFIDENCE_THRESHOLD=$(jq -r '.gesture_confidence_threshold // 0.65' $CONFIG_PATH)
export GESTURE_MIN_DETECTIONS=$(jq -r '.gesture_min_detections // 2' $CONFIG_PATH)
export GESTURE_COOLDOWN=$(jq -r '.gesture_cooldown // 1.5' $CONFIG_PATH)

# ============================================================================
# MediaPipe Model Configuration
# ============================================================================
# ============================================================================
# Gesture Toggles (v2.1.0 - Google Gesture Recognizer: 7 built-in gestures)
# ============================================================================
export ENABLE_CLOSED_FIST=$(jq -r '.enable_closed_fist // true' $CONFIG_PATH)
export ENABLE_OPEN_PALM=$(jq -r '.enable_open_palm // true' $CONFIG_PATH)
export ENABLE_POINTING_UP=$(jq -r '.enable_pointing_up // true' $CONFIG_PATH)
export ENABLE_THUMBS_DOWN=$(jq -r '.enable_thumbs_down // true' $CONFIG_PATH)
export ENABLE_THUMBS_UP=$(jq -r '.enable_thumbs_up // true' $CONFIG_PATH)
export ENABLE_PEACE=$(jq -r '.enable_peace // true' $CONFIG_PATH)
export ENABLE_I_LOVE_YOU=$(jq -r '.enable_i_love_you // true' $CONFIG_PATH)

# ============================================================================
# Logging Configuration
# ============================================================================
export LOG_LEVEL=$(jq -r '.log_level // "INFO"' $CONFIG_PATH)

# ============================================================================
# Display Configuration Summary
# ============================================================================
echo "[INFO] 配置加载完成:"
echo "[INFO]   MQTT Broker: ${MQTT_BROKER}:${MQTT_PORT}"
echo "[INFO]   画面大小: ${FRAME_WIDTH}x${FRAME_HEIGHT}"
echo "[INFO]   目标 FPS: ${TARGET_FPS}"
echo "[INFO]   跳帧处理: 每 ${SKIP_FRAMES} 帧"
echo "[INFO]   置信度阈值: ${GESTURE_CONFIDENCE_THRESHOLD}"
echo "[INFO]   最少检测次数: ${GESTURE_MIN_DETECTIONS}"
echo "[INFO]   冷却时间: ${GESTURE_COOLDOWN}秒"

# ============================================================================
# Suppress FFmpeg and libav error messages
# ============================================================================
export FFREPORT=0
export AV_LOG_FORCE_NOCOLOR=1
export OPENCV_FFMPEG_LOGLEVEL=-8
export PYTHONWARNINGS="ignore"

# ============================================================================
# Start the Python application
# ============================================================================
cd /app

# Use unbuffered output to ensure logs appear immediately
export PYTHONUNBUFFERED=1

echo "[INFO] 启动 Python 应用程序..."

# Run Python with unbuffered output
python3 -u main.py
