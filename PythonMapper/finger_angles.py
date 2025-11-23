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
   the `/vr_finger_angles` topic as a JSON string.

Topics:
    Subscribes to:
        - /vr_hand_joints    (std_msgs/String)
            Raw XR hand joint data from Unity.

    Publishes to:
        - /vr_finger_angles  (std_msgs/String)
            Processed finger bend metrics (angles or normalized openness).

Notes:
    - This node does NOT directly control any robot hardware.
      It only computes joint angles or openness values for later mapping 
      to servo commands.
    - The openness/angle logic lives in `angle_functions.py`.
    - Only the right hand is processed.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
from angle_funcions import compute_hand_openness

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
            String,
            '/vr_finger_angles',
            10
        )

        self.get_logger().info("VRHand Angle Publisher started.")

    def callback(self, msg):
        try:
            # Convert JSON string → Python dict
            data = json.loads(msg.data)

            # Compute openness
            angles = compute_hand_openness(data)

            out_msg = String()
            out_msg.data = json.dumps(angles)
            self.publisher.publish(out_msg)

            self.get_logger().info(f"Joint Angles: {angles}")

        except Exception as e:
            self.get_logger().error(f"Error parsing hand JSON: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = VRHandSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
