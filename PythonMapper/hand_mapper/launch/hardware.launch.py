from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        # ── Tunable arguments ─────────────────────────────────────────────────
        DeclareLaunchArgument(
            'serial_port',
            default_value='/dev/ttyACM0',
            description='USB serial port for the AmazingHand (e.g. /dev/ttyACM0)',
        ),
        DeclareLaunchArgument(
            'baudrate',
            default_value='1000000',
            description='Serial baud rate (SCS0009 default: 1000000)',
        ),
        DeclareLaunchArgument(
            'torque_off_on_shutdown',
            default_value='true',
            description='Disable servo torque when the node exits (recommended)',
        ),

        # ── Nodes ─────────────────────────────────────────────────────────────

        # Converts raw XR Hand joint data → normalised finger openness [0,1]
        Node(
            package='hand_mapper',
            executable='finger_angles',
            name='vr_hand_angle_publisher',
            output='screen',
        ),

        # Sends openness values to physical SCS0009 servos via serial
        Node(
            package='hand_mapper',
            executable='ah_hardware_driver',
            name='ah_hardware_driver',
            output='screen',
            parameters=[{
                'serial_port':           LaunchConfiguration('serial_port'),
                'baudrate':              LaunchConfiguration('baudrate'),
                'torque_off_on_shutdown': LaunchConfiguration('torque_off_on_shutdown'),
            }],
        ),

    ])
