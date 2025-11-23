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
