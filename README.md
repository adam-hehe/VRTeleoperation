# VR Hand Tracking → ROS2 Teleoperation Pipeline 🖐️

This repository streams real-time VR hand joint data from Unity (XR Hands) into ROS2, computes finger bending / openness, and makes it available for robotic teleoperation.

**Overview**
- **Unity**: `XR Hands` captures the right hand joint poses and publishes a JSON dictionary to ROS via the Unity `ROS-TCP-Connector`.
- **ROS2 (Python)**: a subscriber parses the `/vr_hand_joints` JSON, computes per-finger openness (normalized 0–1), and (optionally) republishes the result on `/finger_openness` for teleoperation consumers.

This provides a simple end-to-end VR → ROS teleoperation pipeline.

**Key features**
- **Real-time joint streaming** from Unity using `VRTeleoperation/Unity/newHandPublisher.cs`.
- **Finger bending → openness** computation in Python (`VRTeleoperation/PythonMapper/HandMapper.py`).
- **ROS2 subscriber** example in `VRTeleoperation/ROS_Subscriber/finger_angles.py`.

**Architecture (high level)**
- Unity XR Hands → publishes `std_msgs/String` JSON on `/vr_hand_joints`.
- ROS2 Python node subscribes to `/vr_hand_joints`, computes openness, and makes a compact openness object available for robots or logging.

---
data: '{"right_hand":{"Wrist":{"x":0.0776087,"y":0.877211,"z":0.326393932,"qx":0.141008914,"qy":0.421606421,"qz":0.242409468,"qw":-0.86...'
---
data: '{"right_hand":{"Wrist":{"x":0.0776087,"y":0.877211,"z":0.326393932,"qx":0.141008914,"qy":0.421606421,"qz":0.242409468,"qw":-0.86...'
---
data: '{"right_hand":{"Wrist":{"x":0.0776087,"y":0.877211,"z":0.326393932,"qx":0.141008914,"qy":0.421606421,"qz":0.242409468,"qw":-0.86...'
---
