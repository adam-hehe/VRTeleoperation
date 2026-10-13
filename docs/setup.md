# Setup Guide

This guide takes you from a Meta Quest headset to **normalized finger angles published on a ROS 2 topic** (`/vr_finger_angles`). Any robot hand, simulation or other consumer can subscribe to that topic.

```
Meta Quest ──Link──► Unity (HandToROS) ──/vr_hand_joints──► finger_angles node ──► /vr_finger_angles
```

---

## Prerequisites

**Hardware**
- Meta Quest headset (Quest 2/3/Pro) and a USB-C Link cable
- Windows PC that can run Quest Link

**Software**
- [Meta Horizon Link](https://www.meta.com/help/quest/articles/headsets-and-accessories/oculus-rift-s/install-app-for-link/) (Windows only)
- [Unity Hub](https://unity.com/download) with **Unity 6000.3.10f1** (the version the Unity project uses)
- Ubuntu with ROS 2. This guide assumes **ROS 2 Humble on Ubuntu 22.04**; substitute your distro name if it differs.
- WSL2, if running ROS on the same Windows PC as Unity (the typical setup)

---

## 1. ROS 2 workspace

Run these in your Ubuntu / WSL2 terminal.

### 1.1 Install build tools

```bash
sudo apt update
sudo apt install -y python3-colcon-common-extensions python3-numpy
```

### 1.2 Create a workspace and add the packages

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# Unity's ROS 2 TCP endpoint (bridges Unity ↔ ROS 2)
git clone -b main-ros2 https://github.com/Unity-Technologies/ROS-TCP-Endpoint.git

# This repo's hand_mapper package (symlink so edits in the repo are picked up)
git clone https://github.com/adam-hehe/VRTeleoperation.git ~/VRTeleoperation
ln -s ~/VRTeleoperation/PythonMapper/hand_mapper ~/ros2_ws/src/hand_mapper
```

If the repo is already cloned on the Windows side, you can symlink from `/mnt/c/...` instead of cloning it again.

### 1.3 Build

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Add both `source` lines to `~/.bashrc` so every new terminal is ready:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

Check that the package is installed:

```bash
ros2 pkg executables hand_mapper   # should list finger_angles
```

### 1.4 Find the ROS machine's IP address

```bash
hostname -I
```

Use the first address (for WSL2 this is typically `172.x.x.x`). WSL2 addresses can change after a reboot, so re-check it if Unity stops connecting.

---

## 2. Unity project

The Unity project lives in its own repo, [VRTeleoperation-Unity](https://github.com/adam-hehe/VRTeleoperation-Unity). It comes with the package list, XR settings and scene already configured. Clone it on the Windows PC:

```bash
git clone https://github.com/adam-hehe/VRTeleoperation-Unity.git
```

In Unity Hub, choose **Add → Add project from disk** and select the cloned folder. The first open takes a few minutes while Unity downloads packages and builds its `Library/` folder. Then open `Assets/Scenes/SampleScene.unity`.

Then:

1. **Robotics → ROS Settings**: set **ROS IP Address** to the IP from step 1.4. Keep **Protocol** = `ROS2` and **Port** = `10000`.
2. In **Meta Horizon Link** on Windows, set Link as the active **OpenXR Runtime** (Settings → General). Enable **Developer Runtime Features** (Settings → Beta), which hand tracking over Link requires.

---

## 3. Run it

Open a separate terminal for each ROS command.

1. **Connect the headset.** Open Meta Horizon Link, plug in the Quest, and accept **Enable** on the in-headset prompt.
2. **Start the Unity ↔ ROS endpoint:**
   ```bash
   ros2 run ros_tcp_endpoint default_server_endpoint --ros-args -p ROS_IP:=$(hostname -I | awk '{print $1}')
   ```
3. **Press Play in Unity.** The ROS connection HUD in the top-left of the Game view should show green arrows. Unity must stay in Play Mode for data to be published.
4. **Start the finger angle node:**
   ```bash
   ros2 run hand_mapper finger_angles
   ```
5. **Verify:**
   ```bash
   ros2 topic echo /vr_finger_angles
   ```
   You should see five values between 0 and 1 that change as you open and close your right hand. Every 30 messages, the `finger_angles` terminal also logs the processing time and message rate.

Having trouble? See [troubleshooting.md](troubleshooting.md).

---

## 4. Output format

**Topic:** `/vr_finger_angles`, type `std_msgs/Float32MultiArray`, published once per incoming Unity frame.

| Index | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| Finger | thumb | index | middle | ring | little |

Each value is **openness**: `0.0` = fully closed (fist), `1.0` = fully open. Only the right hand is processed.

**How it's computed** ([angle_functions.py](../PythonMapper/hand_mapper/hand_mapper/angle_functions.py)): for each finger, the node measures the bend at the two outer joints. For the four fingers that's PIP + DIP; for the thumb it's MCP + IP. It adds the two bends and maps the total linearly between a calibrated *open* and *closed* value:

| | `OPEN` (rad) | `CLOSED` (rad) |
|---|---|---|
| Fingers (`finger_openness`) | 0.1 | 3.0 |
| Thumb (`thumb_openness`) | 0.2 | 2.0 |

If your values never reach 0 or 1, uncomment the `print` lines in those functions, open and close your hand, and adjust the constants.

**Raw input**: `/vr_hand_joints` (`std_msgs/String`) carries the JSON that Unity sends: right-hand joint positions for every XR Hands joint, wrist orientation, and a timestamp `t` in ms. Subscribe to it directly if you need more than openness.

---

## Next steps

- **Drive the physical AmazingHand:** see [hardware.md](hardware.md).
- **Camera feed in VR (optional):** `hand_mapper` also includes a `camera_publisher` node that streams a USB webcam to Unity on `/camera/image/compressed`. Install `python3-opencv`, then run:
  ```bash
  ros2 run hand_mapper camera_publisher --ros-args -p device_index:=0
  ```
  In Unity, set `cameraType = ROS` on `CameraDisplayManager`. With WSL2, forward the webcam with `usbipd` (see [hardware.md](hardware.md#2-connect-the-hand)).

  To start the camera and `finger_angles` together, use the launch file instead of running `finger_angles` separately:
  ```bash
  ros2 launch hand_mapper teleoperation.launch.py device_index:=0
  ```

  | Launch argument | Default |
  |---|---|
  | `device_index` | `0` |
  | `jpeg_quality` | `85` |
  | `camera_topic` | `/camera/image/compressed` |
