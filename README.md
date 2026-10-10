# VR Teleoperation and Haptic Glove

This project explores VR-based teleoperation of a robotic hand using real-time hand tracking and haptic feedback. A Meta Quest headset is used to capture human hand motion in Unity, which is streamed through ROS 2 to control a robotic hand (the Pollen Robotics **AmazingHand**), either in a MuJoCo simulation or on physical hardware. The system is designed to eventually provide force and contact feedback to a wearable haptic glove, enabling closed-loop interaction.

---

## Contents

- [How it fits together](#how-it-fits-together)
- [Repository layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [1. ROS 2 workspace setup](#1-ros-2-workspace-setup)
- [2. Unity project setup](#2-unity-project-setup)
- [3. Simulation setup (MuJoCo)](#3-simulation-setup-mujoco)
- [4. Hardware setup (AmazingHand)](#4-hardware-setup-amazinghand)
- [Running the system](#running-the-system)
- [ROS topics](#ros-topics)
- [Troubleshooting](#troubleshooting)
- [Further documentation](#further-documentation)

---

## How it fits together

```
Meta Quest (XR Hands)
        │  Meta Horizon Link (USB)
        ▼
Unity  ── HandToROS.cs ──►  /vr_hand_joints (JSON string)
        │  ROS-TCP-Connector  →  ros_tcp_endpoint (port 10000)
        ▼
ROS 2  ── hand_mapper/finger_angles ──►  /vr_finger_angles (5 floats, 0–1)
        │
        ├──► Simulation/sim_bridge_ws.py   (MuJoCo, via rosbridge WebSocket)
        └──► hand_mapper/ah_hardware_driver (physical servos, via USB serial)
                       │
                       ▼
               /amazing_hand/finger_forces (4 floats)  →  haptic glove (planned)

Optional: hand_mapper/camera_publisher ──► /camera/image/compressed ──► Unity (CameraDisplayManager)
```

The typical machine layout is:

| Component | Runs on |
|---|---|
| Meta Horizon Link + Unity Editor | Windows PC (Horizon Link is Windows-only) |
| ROS 2 + `ros_tcp_endpoint` + `hand_mapper` | Ubuntu, usually WSL2 on the same Windows PC |
| MuJoCo simulation (`sim_bridge_ws.py`) | Any machine that can reach the ROS machine over the network |

---

## Repository layout

```
VRTeleoperation/
├── PythonMapper/
│   └── hand_mapper/              # ROS 2 ament_python package (build this)
│       ├── hand_mapper/
│       │   ├── finger_angles.py      # /vr_hand_joints → /vr_finger_angles
│       │   ├── angle_functions.py    # finger openness math
│       │   ├── camera_publisher.py   # USB webcam → /camera/image/compressed
│       │   └── ah_hardware_driver.py # /vr_finger_angles → SCS0009 servos
│       └── launch/
│           ├── teleoperation.launch.py  # camera_publisher + finger_angles
│           └── hardware.launch.py       # finger_angles + ah_hardware_driver
├── Simulation/
│   ├── sim_bridge_ws.py          # MuJoCo sim + rosbridge client
│   └── *.xml                     # MuJoCo model (AmazingHand + scene)
├── Unity/                        # C# scripts (reference; full project published separately)
│   ├── Publisher/HandToROS.cs
│   ├── Camera/                   # ROS / USB camera display in VR
│   ├── Visualizer/               # XR Hands joint visualization
│   └── TeleopController.cs       # in-VR ON/OFF button
├── docs/
└── requirements.txt
```

> The loose `PythonMapper/*.py` files are older copies of the modules in `PythonMapper/hand_mapper/hand_mapper/`. Use the package versions.

---

## Prerequisites

**Hardware**
- Meta Quest headset (Quest 2/3/Pro) and a USB-C Link cable
- Windows PC that can run Quest Link
- *(Optional)* USB webcam for the camera feed
- *(Optional)* AmazingHand with 8× Feetech SCS0009 servos and a USB-TTL serial adapter

**Software**
- [Meta Horizon Link](https://www.meta.com/help/quest/articles/headsets-and-accessories/oculus-rift-s/install-app-for-link/) (Windows)
- Unity Editor (the version the published Unity project was made with)
- Ubuntu with ROS 2 installed. These instructions assume **ROS 2 Humble on Ubuntu 22.04**; substitute your distro name if it differs.
- WSL2 (if running ROS on the Windows PC)
- Python 3.10+ with `pip`

---

## 1. ROS 2 workspace setup

Run these in your Ubuntu / WSL2 terminal.

### 1.1 Install ROS 2 dependencies

```bash
sudo apt update
sudo apt install -y python3-colcon-common-extensions python3-opencv \
    ros-humble-rosbridge-suite
```

- `python3-opencv` is needed by `camera_publisher`.
- `rosbridge-suite` is needed only for the MuJoCo simulation.

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

### 1.4 Verify

```bash
ros2 pkg executables hand_mapper
# hand_mapper ah_hardware_driver
# hand_mapper camera_publisher
# hand_mapper finger_angles
```

### 1.5 Find the ROS machine's IP address

Unity and the simulation both need this:

```bash
hostname -I
```

Use the first address (for WSL2 this is typically `172.x.x.x`). WSL2 addresses can change after a reboot, so re-check it if Unity stops connecting.

---

## 2. Unity project setup

> **The complete Unity project will be published separately and can be downloaded directly.** *(Link coming soon.)* It comes with all packages, XR settings and scenes already configured, so you don't need to build it yourself. The `Unity/` folder in this repo holds only the C# scripts, for reference.

After opening the downloaded project:

1. **Robotics → ROS Settings**: set **ROS IP Address** to the IP from step 1.5. Keep **Protocol** = `ROS2` and **Port** = `10000`.
2. In **Meta Horizon Link** on Windows, set Link as the active **OpenXR Runtime** (Settings → General). Enable **Developer Runtime Features** (Settings → Beta), which hand tracking over Link requires.

---

## 3. Simulation setup (MuJoCo)

The simulation subscribes to the finger angles and wrist pose, drives the AmazingHand model, and publishes contact forces.

### 3.1 Python environment

On the machine that will run the simulation:

```bash
cd VRTeleoperation
python3 -m venv .venv
source .venv/bin/activate
pip install numpy mujoco roslibpy
```

`requirements.txt` also lists `rclpy`. `rclpy` comes from your ROS 2 install, not from pip, so the simulation doesn't need it.

### 3.2 Add the AmazingHand meshes

`Simulation/robot.xml` loads meshes from `Simulation/assets/` (`meshdir="assets"`). That folder is **not committed**. Copy the AmazingHand MuJoCo mesh files (`scs0009`, `finger_frame_1`, `finger_frame_2`, `r_hand_plate`, `bushing_0608_04`, …) from the [pollen-robotics/AmazingHand](https://github.com/pollen-robotics/AmazingHand) repo into:

```
Simulation/assets/
```

### 3.3 Configure `sim_bridge_ws.py`

Edit the constants at the top of [Simulation/sim_bridge_ws.py](Simulation/sim_bridge_ws.py):

```python
WSL_IP   = '<ROS machine IP from step 1.5>'
WSL_PORT = 9090   # rosbridge WebSocket port (see note below)
XML_PATH = '/absolute/path/to/VRTeleoperation/Simulation/amazing_hand_wrapper.xml'
```

> **Note:** `sim_bridge_ws.py` uses `roslibpy`, which speaks the **rosbridge** WebSocket protocol. It cannot connect to Unity's `ros_tcp_endpoint`, even though both default to port 10000 in the code comments. Run `rosbridge_websocket` on the ROS machine (see [Running the system](#running-the-system)) and point `WSL_PORT` at its port. Use 9090 so it doesn't clash with `ros_tcp_endpoint` on 10000.

> **WSL2 networking:** If the simulation runs on a *different* machine from WSL2, that machine must be able to reach WSL2's port 9090. Either enable WSL [mirrored networking](https://learn.microsoft.com/en-us/windows/wsl/networking#mirrored-mode-networking) or add a Windows port proxy and use the Windows PC's LAN IP. For a port proxy, run this in an admin PowerShell:
> ```powershell
> netsh interface portproxy add v4tov4 listenport=9090 listenaddress=0.0.0.0 connectport=9090 connectaddress=<WSL IP>
> ```

---

## 4. Hardware setup (AmazingHand)

### 4.1 Install the servo driver library

In the ROS 2 environment:

```bash
pip install rustypot
```

### 4.2 Connect the hand

1. Power the hand and connect the USB-TTL serial adapter.
2. **If using WSL2**, forward the USB device into WSL using [usbipd-win](https://learn.microsoft.com/en-us/windows/wsl/connect-usb). Run this in an admin PowerShell:
   ```powershell
   usbipd list
   usbipd bind --busid <BUSID>
   usbipd attach --wsl --busid <BUSID>
   ```
3. In Ubuntu, confirm the device and grant serial access. Log out and back in after `usermod`.
   ```bash
   ls /dev/ttyACM* /dev/ttyUSB*
   sudo usermod -aG dialout $USER
   ```

### 4.3 Calibrate

`MIDDLE_POS_DEG` in [ah_hardware_driver.py](PythonMapper/hand_mapper/hand_mapper/ah_hardware_driver.py) holds per-servo zero offsets. The defaults come from the AmazingHand `r_hand.toml`. Run the AmazingHand `AHControl` `get_zeros` tool on your hand and update the values:

```bash
cargo run --bin get_zeros -- --serialport /dev/ttyACM0 \
    --config Demo/AHControl/config/r_hand.toml
```

Rebuild is not needed if you used `--symlink-install`.

---

## Running the system

Open a separate terminal for each step. Every Ubuntu terminal must have ROS 2 and the workspace sourced (see 1.3).

### Base pipeline (always required)

1. **Connect the headset.** Open Meta Horizon Link, plug in the Quest, and accept **Enable** on the in-headset prompt to start Link.
2. **Start the Unity ↔ ROS endpoint** (Ubuntu):
   ```bash
   ros2 run ros_tcp_endpoint default_server_endpoint --ros-args -p ROS_IP:=$(hostname -I | awk '{print $1}')
   ```
3. **Press Play in Unity.** The ROS connection HUD in the top-left of the Game view should show green arrows.
4. **Verify hand data is arriving:**
   ```bash
   ros2 topic echo /vr_hand_joints --once
   ```

Then pick a mode.

### Mode A: Simulation

```bash
# Terminal: finger angle mapper
ros2 run hand_mapper finger_angles

# Terminal: rosbridge for the simulation
ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=9090
```

On the simulation machine:

```bash
source .venv/bin/activate
python Simulation/sim_bridge_ws.py      # Linux / Windows
mjpython Simulation/sim_bridge_ws.py    # macOS (the MuJoCo passive viewer requires mjpython)
```

A MuJoCo viewer opens and `System Launch Successful` is printed. The hand should follow your fingers.

### Mode B: Physical hand

```bash
ros2 launch hand_mapper hardware.launch.py serial_port:=/dev/ttyACM0
```

This launches both `finger_angles` and `ah_hardware_driver`, so don't run `finger_angles` separately. Torque is disabled on all servos when you stop the launch with Ctrl+C.

### Mode C: Camera feed in VR (combine with A or B)

```bash
ros2 run hand_mapper camera_publisher --ros-args -p device_index:=0 -p jpeg_quality:=85
```

Set `cameraType = ROS` on `CameraDisplayManager` in Unity. With WSL2, attach the webcam with `usbipd` the same way as the serial adapter in 4.2.

`teleoperation.launch.py` starts `camera_publisher` and `finger_angles` together. Use it instead of the separate commands when you are **not** also running `hardware.launch.py`, which already starts `finger_angles`:

```bash
ros2 launch hand_mapper teleoperation.launch.py device_index:=0
```

---

## ROS topics

| Topic | Type | Publisher → Subscriber | Contents |
|---|---|---|---|
| `/vr_hand_joints` | `std_msgs/String` | Unity → `finger_angles`, sim | JSON: right-hand joint positions, wrist pose, timestamp |
| `/vr_finger_angles` | `std_msgs/Float32MultiArray` | `finger_angles` → sim / hardware | `[thumb, index, middle, ring, little]`, 0 = closed, 1 = open |
| `/amazing_hand/finger_forces` | `std_msgs/Float32MultiArray` | sim / hardware → (haptics) | `[F_index, F_middle, F_ring, F_thumb]` in N (hardware values are approximate) |
| `/camera/image/compressed` | `sensor_msgs/CompressedImage` | `camera_publisher` → Unity | JPEG frames |

---

## Troubleshooting

| Symptom | Check |
|---|---|
| Unity HUD shows red arrows / no connection | `ROS IP Address` in **Robotics → ROS Settings** must match `hostname -I`. Is `ros_tcp_endpoint` running? Is Windows Firewall blocking port 10000? |
| `[HandToROS] No XRHandSubsystem running yet` | Hand tracking isn't active. Check the OpenXR Hand Tracking Subsystem feature, Link's *Developer Runtime Features*, and that the headset is tracking your hands (put controllers down). |
| `/vr_hand_joints` has data but `/vr_finger_angles` doesn't | Is `finger_angles` running? Run `ros2 node list`. |
| Simulation: `Error opening file .../assets/...` | Mesh files are missing. See 3.2. |
| Simulation hangs on connect or exits right away | `WSL_IP`/`WSL_PORT` must point at **rosbridge**, not `ros_tcp_endpoint`, and the port must be reachable from the sim machine. |
| macOS: `launch_passive requires that the Python script be run under mjpython` | Run with `mjpython` instead of `python`. |
| `rustypot not found` | `pip install rustypot` in the same Python environment ROS uses. |
| `could not open port /dev/ttyACM0` | Device not attached to WSL (`usbipd attach`), wrong port name, or user not in `dialout`. |
| Fingers move the wrong direction or are offset | Recalibrate `MIDDLE_POS_DEG` (see 4.3). |

---

## Current status

- VR hand tracking via Meta Quest XR Hands is functional
- Unity publishes joint data to ROS 2; finger openness is computed and published
- MuJoCo simulation of the AmazingHand with contact-force output is working
- Hardware driver for the physical AmazingHand is implemented
- Haptic glove redesign and force-feedback integration are in progress

---

## Further documentation

- [docs/architecture.md](docs/architecture.md): system architecture and data flow
- [docs/setup.md](docs/setup.md): original quick-start notes
- [docs/simulation.md](docs/simulation.md): TBD
- [docs/haptics.md](docs/haptics.md): TBD
