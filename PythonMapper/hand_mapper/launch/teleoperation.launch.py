from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        # ── Tunable arguments (override from CLI with arg:=value) ────────────
        DeclareLaunchArgument(
            'device_index',
            default_value='0',
            description='USB camera device index (0 = first camera, 1 = second, …)',
        ),
        DeclareLaunchArgument(
            'jpeg_quality',
            default_value='85',
            description='JPEG compression quality 0–100',
        ),
        DeclareLaunchArgument(
            'camera_topic',
            default_value='/camera/image/compressed',
            description='ROS topic to publish compressed camera frames on',
        ),

        # ── Nodes ─────────────────────────────────────────────────────────────
        Node(
            package='hand_mapper',
            executable='camera_publisher',
            name='camera_publisher',
            output='screen',
            parameters=[{
                'device_index': LaunchConfiguration('device_index'),
                'jpeg_quality':  LaunchConfiguration('jpeg_quality'),
                'topic':         LaunchConfiguration('camera_topic'),
            }],
        ),

        Node(
            package='hand_mapper',
            executable='finger_angles',
            name='vr_hand_angle_publisher',
            output='screen',
        ),

    ])
