"""
MediaPipe Gesture Control - Main Application

v2.0.0: Simplified pure gesture recognition system
Removed: Expression detection, motion detection, visualization
"""

import sys
import os
import time
from collections import deque
from typing import Optional

# CRITICAL: Suppress FFmpeg logs BEFORE importing cv2
import suppress_ffmpeg_logs

import cv2
import logging

import config
from src.gesture_engine import GestureEngine
from src.mqtt_client import MQTTClient

# Additional suppression for OpenCV
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|fflags;nobuffer|flags;low_delay'
os.environ['OPENCV_LOG_LEVEL'] = 'FATAL'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'

# Suppress Python warnings
import warnings
warnings.filterwarnings('ignore')

# Configure logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GestureBuffer:
    """
    Implements state machine logic with debouncing and cooldown mechanism.
    A gesture is only triggered if it remains stable for a specified duration.
    """
    
    def __init__(
        self,
        min_detections: int = config.GESTURE_MIN_DETECTIONS,
        cooldown: float = config.GESTURE_COOLDOWN,
        confidence_threshold: float = config.GESTURE_CONFIDENCE_THRESHOLD
    ):
        self.min_detections = min_detections
        self.cooldown = cooldown
        self.confidence_threshold = confidence_threshold
        
        # Buffer to store recent gesture detections
        self.gesture_history = deque(maxlen=50)
        
        # State tracking
        self.current_stable_gesture: Optional[str] = None
        self.last_triggered_gesture: Optional[str] = None
        self.last_trigger_time: float = 0
    
    def add_detection(self, gesture: Optional[str], confidence: float) -> Optional[str]:
        """
        Add a new gesture detection to the buffer.
        
        Args:
            gesture: Detected gesture name (or None if no hand)
            confidence: Detection confidence
            
        Returns:
            Gesture name if it should be triggered, None otherwise
        """
        current_time = time.time()
        
        # If no hand detected or low confidence, clear history
        if gesture is None or confidence < self.confidence_threshold:
            self.gesture_history.clear()
            self.current_stable_gesture = None
            return None
        
        # If gesture changed, clear history for fast response
        if self.gesture_history and gesture != self.gesture_history[-1]['gesture']:
            logger.debug(f"手势切换: {self.gesture_history[-1]['gesture']} → {gesture}, 清空缓冲区")
            self.gesture_history.clear()
            self.current_stable_gesture = None
        
        # Add to history
        self.gesture_history.append({
            'gesture': gesture,
            'confidence': confidence,
            'timestamp': current_time
        })
        
        # Check if gesture has been stable for required duration
        if self._is_gesture_stable(gesture, current_time):
            # Check cooldown - don't trigger same gesture repeatedly
            if self._can_trigger(gesture, current_time):
                logger.info(f"✓ 手势触发: {gesture} (置信度: {confidence:.2f})")
                self.last_triggered_gesture = gesture
                self.last_trigger_time = current_time
                return gesture
            else:
                logger.debug(f"手势 {gesture} 已稳定但处于冷却期")
        else:
            # Log why not stable (but only occasionally to avoid spam)
            if len(self.gesture_history) % 10 == 0:
                logger.debug(f"手势 {gesture} 已检测但尚未稳定 (历史: {len(self.gesture_history)} 次检测)")
        
        return None
    
    def _is_gesture_stable(self, gesture: str, current_time: float) -> bool:
        """
        Check if a gesture has been consistently detected.
        """
        if len(self.gesture_history) < self.min_detections:
            return False
        
        # Check last N detections - are they all the same gesture?
        recent_detections = list(self.gesture_history)[-self.min_detections:]
        
        all_same_gesture = all(
            d['gesture'] == gesture and d['confidence'] >= self.confidence_threshold
            for d in recent_detections
        )
        
        if not all_same_gesture:
            return False
        
        # Calculate time span for logging
        time_span = recent_detections[-1]['timestamp'] - recent_detections[0]['timestamp']
        
        logger.info(
            f"稳定性检查 {gesture}: "
            f"last_{self.min_detections}={all_same_gesture}, "
            f"time_span={time_span:.2f}s, "
            f"buffer_size={len(self.gesture_history)}"
        )
        
        if all_same_gesture:
            logger.info(f"✓ 手势 {gesture} 已稳定 (最近 {self.min_detections} 次检测一致)")
            self.current_stable_gesture = gesture
            return True
        
        return False
    
    def _can_trigger(self, gesture: str, current_time: float) -> bool:
        """
        Check if a gesture can be triggered based on cooldown.
        """
        # If this is a different gesture, allow immediate trigger
        if gesture != self.last_triggered_gesture:
            return True
        
        # Same gesture: check cooldown period
        time_since_last_trigger = current_time - self.last_trigger_time
        if time_since_last_trigger < self.cooldown:
            logger.debug(
                f"冷却中: {gesture} (距上次触发 {time_since_last_trigger:.2f}s, "
                f"需要 {self.cooldown}s)"
            )
            return False
        
        return True


class VideoStreamProcessor:
    """
    Handles RTSP video stream connection and frame processing.
    """
    
    def __init__(self, rtsp_url: str):
        self.rtsp_url = rtsp_url
        self.cap = None
        self.frame_count = 0
        self.processed_frame_count = 0
        self.skip_frames = config.SKIP_FRAMES
    
    def connect(self) -> bool:
        """
        Connect to RTSP stream with low latency settings.
        """
        try:
            logger.info(f"连接到 RTSP 流: {self.rtsp_url}")
            
            # Release existing connection if any
            if self.cap is not None:
                self.cap.release()
            
            # Set RTSP options for low latency (before opening stream)
            os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp|fflags;nobuffer|flags;low_delay'
            
            # Create new connection
            self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            
            # Set minimal buffer to reduce latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Disable any internal buffering
            self.cap.set(cv2.CAP_PROP_FPS, config.TARGET_FPS)
            
            if not self.cap.isOpened():
                logger.error("无法打开 RTSP 流")
                return False
            
            logger.info("成功连接到 RTSP 流（低延迟模式）")
            logger.info("提示：RTSP 流延迟取决于网络和摄像头设置")
            return True
            
        except Exception as e:
            logger.error(f"连接 RTSP 流失败: {e}")
            return False
    
    def read_frame(self):
        """
        Read and process next frame from stream.
        Uses aggressive frame dropping to minimize latency.
        """
        if not self.cap or not self.cap.isOpened():
            return None
        
        try:
            # Aggressively drop buffered frames to get the latest frame
            # This reduces RTSP stream latency
            for _ in range(3):  # Drop 3 old frames
                self.cap.grab()
            
            # Skip frames if configured (for performance)
            for _ in range(self.skip_frames - 1):
                self.cap.grab()
                self.frame_count += 1
            
            ret, frame = self.cap.read()
            self.frame_count += 1
            
            if not ret or frame is None:
                logger.debug(f"读取帧失败 (帧 #{self.frame_count})")
                return None
            
            # Resize frame if needed
            if config.FRAME_WIDTH and config.FRAME_HEIGHT:
                frame = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))
            
            self.processed_frame_count += 1
            return frame
            
        except Exception as e:
            logger.error(f"处理帧时出错: {e}")
            return None
    
    def release(self):
        """Release video capture resources."""
        if self.cap:
            self.cap.release()
            logger.info("释放视频流资源")


def main():
    """主应用程序循环"""
    logger.info("="*60)
    logger.info("║ MediaPipe 手势识别 v2.1.3")
    logger.info("║ Google Gesture Recognizer (高精度模型)")
    logger.info("║ BUILD: 2025-12-02-OK-GESTURE")  # 版本标识
    logger.info("="*60)
    logger.info("启动手势识别系统")
    logger.info(f"RTSP URL: {config.RTSP_URL}")
    logger.info(f"MQTT Broker: {config.MQTT_BROKER}:{config.MQTT_PORT}")
    logger.info(f"目标 FPS: {config.TARGET_FPS}")
    logger.info(f"画面大小: {config.FRAME_WIDTH}x{config.FRAME_HEIGHT}")
    logger.info(f"跳帧处理: 每 {config.SKIP_FRAMES} 帧处理一次")
    logger.info(f"IMAGE 模式: 实时低延迟 + 主动丢帧")
    logger.info("="*60)
    
    # Initialize components
    gesture_engine = GestureEngine()
    mqtt_client = MQTTClient()
    gesture_buffer = GestureBuffer()
    video_processor = VideoStreamProcessor(config.RTSP_URL)
    
    # Connect to MQTT
    if not mqtt_client.connect():
        logger.error("无法连接到 MQTT broker，退出...")
        return
    
    logger.info("MQTT 连接成功")
    
    # Main loop
    consecutive_failures = 0
    max_consecutive_failures = 10
    last_log_time = time.time()
    
    try:
        while True:
            # Connect to video stream if not connected
            if not video_processor.cap or not video_processor.cap.isOpened():
                logger.info("视频流未连接，尝试连接...")
                if not video_processor.connect():
                    logger.error(f"视频流连接失败，{config.RTSP_RECONNECT_DELAY}秒后重试...")
                    time.sleep(config.RTSP_RECONNECT_DELAY)
                    continue
                consecutive_failures = 0
            
            # Read frame
            frame = video_processor.read_frame()
            
            if frame is None:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"连续失败 {consecutive_failures} 次，重新连接...")
                    video_processor.release()
                    consecutive_failures = 0
                time.sleep(0.1)
                continue
            
            consecutive_failures = 0
            
            # Process gesture recognition (IMAGE mode - no timestamp needed)
            gesture, confidence = gesture_engine.process_frame(frame)
            
            # Check if gesture should be triggered
            # Filter out 'NONE' - treat it as no valid gesture detected
            if gesture and gesture != 'NONE':
                triggered_gesture = gesture_buffer.add_detection(gesture, confidence)
                if triggered_gesture:
                    mqtt_client.publish_gesture(triggered_gesture, confidence)
            else:
                # No valid gesture, clear buffer
                if gesture == 'NONE':
                    logger.debug("检测到 NONE，作为 None 处理，清空 buffer")
                gesture_buffer.add_detection(None, 0.0)
            
            # Periodic logging (every 20 frames or 5 seconds)
            current_time = time.time()
            if (video_processor.processed_frame_count % 20 == 0 or 
                current_time - last_log_time >= 5):
                if gesture:
                    logger.info(
                        f"[已处理 {video_processor.processed_frame_count}] "
                        f"手势: {gesture} ({confidence:.2f})"
                    )
                last_log_time = current_time
            
            # Frame rate control
            time.sleep(1.0 / config.TARGET_FPS if config.TARGET_FPS > 0 else 0.01)
    
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    except Exception as e:
        logger.error(f"主循环出错: {e}", exc_info=True)
    finally:
        logger.info("清理资源...")
        gesture_engine.release()
        video_processor.release()
        mqtt_client.disconnect()
        logger.info("程序已退出")


if __name__ == "__main__":
    main()
