"""
VRHand Angle Publisher Node
---------------------------

This ROS2 node subscribes to the Unity XR Hands data published on the 
`/vr_hand_joints` topic. Unity sends a JSON string containing right-hand 
joint positions (and wrist orientation) for every XRHand joint.

This node:

1. Receives the JSON-formatted hand joint data.
2. Converts the string into a Python dictionary.
3. Passes the joint positions into `compute_hand_openness()` 
   (or compute_hand_angles, depending on the function implemented) 
   to extract per-finger bending information.
4. Publishes the processed finger angles/openness values on 
   the `/vr_finger_angles` topic as a Float32MultiArray.

Topics:
    Subscribes to:
        - /vr_hand_joints    (std_msgs/String)
            Raw XR hand joint data from Unity.

    Publishes to:
        - /vr_finger_angles  (std_msgs/Float32MultiArray)
            Processed finger bend metrics (angles or normalized openness).

Notes:
    - This node does NOT directly control any robot hardware.
      It only computes joint angles or openness values for later mapping 
      to servo commands.
    - The openness/angle logic lives in `angle_functions.py`.
    - Only the right hand is processed.
"""

import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32MultiArray

from hand_mapper.angle_functions import compute_hand_openness

_LOG_INTERVAL = 30  # print latency stats every N messages


class VRHandSubscriber(Node):
    def __init__(self):
        super().__init__('vr_hand_angle_publisher')

        self.subscription = self.create_subscription(
            String,
            '/vr_hand_joints',
            self.callback,
            10
        )

        self.publisher = self.create_publisher(
            Float32MultiArray,
            '/vr_finger_angles',
            10
        )

        self._msg_count = 0
        self._processing_sum = 0.0   # ms
        self._unity_ros_sum = 0.0    # ms — only valid with NTP clock sync
        self._unity_ros_count = 0
        self._last_recv_wall = None
        self._interval_sum = 0.0     # ms between consecutive messages

        self.get_logger().info("VRHand Angle Publisher started.")

    def callback(self, msg):
        t_recv_wall = time.time()           # wall clock for cross-machine delta
        t_recv_perf = time.perf_counter()   # high-res for processing time

        try:
            data = json.loads(msg.data)

            # --- Unity→ROS latency (requires NTP sync between PC and ROS machine) ---
            t_unity_ms = data.get("t")
            if t_unity_ms is not None:
                unity_to_ros_ms = t_recv_wall * 1000.0 - t_unity_ms
                self._unity_ros_sum += unity_to_ros_ms
                self._unity_ros_count += 1

            # --- Inter-message interval ---
            if self._last_recv_wall is not None:
                self._interval_sum += (t_recv_wall - self._last_recv_wall) * 1000.0
            self._last_recv_wall = t_recv_wall

            # --- Compute and publish ---
            angles = compute_hand_openness(data)
            angles = [float(x) for x in angles]

            out_msg = Float32MultiArray()
            out_msg.data = angles
            self.publisher.publish(out_msg)

            # --- Processing time ---
            processing_ms = (time.perf_counter() - t_recv_perf) * 1000.0
            self._processing_sum += processing_ms
            self._msg_count += 1

            # --- Periodic latency log ---
            if self._msg_count % _LOG_INTERVAL == 0:
                avg_processing = self._processing_sum / _LOG_INTERVAL
                intervals = self._msg_count - 1
                avg_rate = (1000.0 / (self._interval_sum / intervals)) if intervals > 0 else 0.0

                if self._unity_ros_count > 0:
                    avg_unity_ros = self._unity_ros_sum / self._unity_ros_count
                    self.get_logger().info(
                        f"[latency] Unity→ROS: {avg_unity_ros:.1f}ms | "
                        f"processing: {avg_processing:.2f}ms | "
                        f"rate: {avg_rate:.1f}Hz"
                    )
                else:
                    self.get_logger().info(
                        f"[latency] processing: {avg_processing:.2f}ms | "
                        f"rate: {avg_rate:.1f}Hz  (add 't' field to Unity JSON for cross-machine latency)"
                    )

                # Reset accumulators each window
                self._processing_sum = 0.0
                self._unity_ros_sum = 0.0
                self._unity_ros_count = 0
                self._interval_sum = 0.0

        except Exception as e:
            self.get_logger().error(f"Error processing hand data: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = VRHandSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
