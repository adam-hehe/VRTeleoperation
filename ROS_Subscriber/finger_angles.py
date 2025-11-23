import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
from hand_openness import compute_hand_openness

class VRHandSubscriber(Node):
    def __init__(self):
        super().__init__('vr_hand_subscriber')
        self.subscription = self.create_subscription(
            String,
            '/vr_hand_joints',
            self.callback,
            10)

    def callback(self, msg):
        try:
            # Convert JSON string → Python dict
            data = json.loads(msg.data)

            # Compute openness
            openness = compute_hand_openness(data)

            self.get_logger().info(f"Openess: {openness}")

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
