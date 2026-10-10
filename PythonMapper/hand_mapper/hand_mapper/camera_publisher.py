#!/usr/bin/env python3
"""
Captures frames from a USB webcam and publishes them as JPEG-compressed
ROS2 images on /camera/image/compressed.

Run:
    python3 camera_publisher.py
    ros2 run <package> camera_publisher  (if installed as a ROS2 node)

Parameters (set via ros2 param or edit defaults below):
    device_index  : int   - OpenCV camera index (default 0)
    width         : int   - Capture width  (default 1280)
    height        : int   - Capture height (default 720)
    fps           : int   - Target framerate (default 30)
    jpeg_quality  : int   - JPEG quality 0-100 (default 85)
    topic         : str   - Publish topic (default /camera/image/compressed)
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from sensor_msgs.msg import CompressedImage
import cv2


# QoS: best-effort, depth 1 — drop stale frames rather than queue them
_CAMERA_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
)


class CameraPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')

        self.declare_parameter('device_index', 0)
        self.declare_parameter('width', 1280)
        self.declare_parameter('height', 720)
        self.declare_parameter('fps', 30)
        self.declare_parameter('jpeg_quality', 85)
        self.declare_parameter('topic', '/camera/image/compressed')

        device       = self.get_parameter('device_index').value
        width        = self.get_parameter('width').value
        height       = self.get_parameter('height').value
        fps          = self.get_parameter('fps').value
        self._quality = self.get_parameter('jpeg_quality').value
        topic        = self.get_parameter('topic').value

        self._pub = self.create_publisher(CompressedImage, topic, _CAMERA_QOS)

        self._cap = cv2.VideoCapture(device)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._cap.set(cv2.CAP_PROP_FPS, fps)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # discard stale frames

        if not self._cap.isOpened():
            self.get_logger().error(f'Cannot open camera device {device}')
            return

        actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.get_logger().info(
            f'Camera opened: {actual_w}x{actual_h} @ {fps}fps  →  {topic}'
        )

        self._encode_params = [cv2.IMWRITE_JPEG_QUALITY, self._quality]
        self.create_timer(1.0 / fps, self._publish_frame)

    def _publish_frame(self):
        ret, frame = self._cap.read()
        if not ret:
            self.get_logger().warn('Failed to read frame from camera', throttle_duration_sec=2.0)
            return

        ok, buffer = cv2.imencode('.jpg', frame, self._encode_params)
        if not ok:
            return

        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_optical_frame'
        msg.format = 'jpeg'
        msg.data = buffer.tobytes()

        self._pub.publish(msg)

    def destroy_node(self):
        if self._cap.isOpened():
            self._cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
