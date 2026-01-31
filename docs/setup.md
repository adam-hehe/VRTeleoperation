# Project Startup Guide

This guide describes how to start the VR teleoperation pipeline and verify that hand tracking data is correctly flowing from Unity to ROS2.

---

## Prerequisites

- Meta Quest headset
- Meta Horizon Link installed
- Unity project: `VR_Teleoperation`
- ROS2 environment sourced on Ubuntu

---

## Startup Steps

1. Open the **Meta Horizon Link** app and connect the Meta Quest headset to the computer using a USB cable.

2. Put on the headset. When prompted to allow the connection, select **Enable**.

3. Open **Unity** and load the project titled `VR_Teleoperation`.

4. Open an Ubuntu terminal and start the ROS–TCP endpoint:
   ```bash
   ros2 run ros_tcp_endpoint default_server_endpoint --ros-args -p ROS_IP:=172.18.247.80
   ```
5. Press the Play button in Unity to begin streaming hand tracking data.
6. In a separate Ubuntu terminal, run the finger angle mapper:
   ```bash
   ros2 run hand_mapper finger_angles
   ```

## Verifying Data Flow 
- After Step 5, Unity publishes joint and wrist pose data to the ROS2 topic, you can view this with:
  ```bash
  ros2 topic echo /vr_hand_joints
  ```

## Notes
- Ensure that ROS_IP matches the IP address of the machine running ROS2. (Check `Robotics` tab in unity and type `Hostname -I` in Ubuntu terminal) 
- Unity must be in Play Mode for data to be published.
- Both ROS2 nodes must be running simultaneously for the full pipeline to function.
   
