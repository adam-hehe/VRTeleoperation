# System Architecture

This document describes the high-level architecture of the VR Teleoperation and Haptic Glove project, including data flow, core components, and planned feedback loops.

## Overview

The system is designed as a bidirectional teleoperation pipeline that allows a user to control a robotic hand using VR hand tracking while eventually receiving haptic feedback from the robot’s interactions with the environment. 
At a high level, the system follows this flow:

1. Unity (Hand Tracking & Processing) 

2. ROS2 (Networking and Control Logic) 

3. Robotic Hand / Simulation (Servos & Contacts) 

4. ROS2 (Force / Contact Data) 

5. Haptic Glove (Feedback)

--- 

## Core Components

### 1. VR Hand Tracking (Meta Quest)

- Uses Meta Quest’s XR Hands system to track hand pose and joint transforms in real time
- Provides per-joint position and orientation data for the wrist and fingers
- Runs fully on the headset and streams data into Unity

---

### 2. Unity Layer

Unity acts as the central integration layer between VR input and the robotics stack.

Responsibilities:
- Receive XR Hands joint data
- Compute higher-level representations such as per-finger bend angles
- Perform visualization and simulation
- Publish hand state data to ROS2

Key outputs:
- Joint poses (positions and orientations)
- Derived finger bend / openness values
- Simulated contact and force data (in simulation mode)

Unity communicates with ROS2 using the ROS–TCP–Connector.

---

### 3. ROS2 Middleware

ROS2 serves as the communication backbone and control layer.

Responsibilities:
- Receive hand state data from Unity
- Convert hand pose data into robot-specific commands
- Manage topics and message types for teleoperation
- Route force and contact data back toward the haptic system

Topics:

| Topic | Type | Publisher → Subscriber | Contents |
|---|---|---|---|
| `/vr_hand_joints` | `std_msgs/String` | Unity → `finger_angles`, sim | JSON: right-hand joint positions, wrist pose, timestamp |
| `/vr_finger_angles` | `std_msgs/Float32MultiArray` | `finger_angles` → sim / hardware | `[thumb, index, middle, ring, little]`, 0 = closed, 1 = open |
| `/amazing_hand/finger_forces` | `std_msgs/Float32MultiArray` | sim / hardware → (haptics) | `[F_index, F_middle, F_ring, F_thumb]` in N (hardware values are approximate) |
| `/camera/image/compressed` | `sensor_msgs/CompressedImage` | `camera_publisher` → Unity | JPEG frames |

ROS2 enables modular development and allows simulation, hardware control, and haptics to evolve independently.

---

### 4. Robotic Hand

The robotic hand executes motion commands generated from VR input.

Responsibilities:
- Receive finger or joint commands from ROS2
- Drive servos to match user hand motion
- Detect contact or infer force during interaction

Planned sensing sources:
- Servo load or current draw
- Limit switches or contact sensors
- Simulation-derived force signals

The robotic hand is treated as a replaceable module, allowing the same pipeline to be used with different hardware implementations.

---

### 5. Simulation Environment

Simulation is used as an intermediate step before full hardware integration.

Responsibilities:
- Model object interaction and contact forces
- Generate clean, repeatable force and contact signals
- Prototype force-to-haptic mappings without risking hardware

Simulation outputs mirror planned hardware signals so that the same ROS2 interfaces can be reused.

---

### 6. Haptic Glove (Planned)

The haptic glove provides feedback to the user based on robot interaction.

Responsibilities:
- Receive force or contact data from ROS2
- Convert forces into tactile feedback (e.g., braking, vibration)
- Apply feedback per finger or joint

Initial focus:
- Binary contact feedback (contact vs. no contact)
- Simple force scaling

Later iterations may include:
- Continuous force feedback
- Directional or impedance-based cues

---

## Repository Layout

```
VRTeleoperation/
├── PythonMapper/
│   └── hand_mapper/              # ROS 2 ament_python package
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
└── docs/
```

The Unity project is in a separate repo, [VRTeleoperation-Unity](https://github.com/adam-hehe/VRTeleoperation-Unity). Its main scripts are in `Assets/Scripts/`:

| Script | Purpose |
|---|---|
| `HandToROS.cs` | XR Hands → `/vr_hand_joints` |
| `CameraDisplayManager.cs`, `ROSCameraSource.cs`, `USBCameraSource.cs`, `ICameraSource.cs` | ROS / USB camera display in VR |
| `TeleopController.cs` | In-VR ON/OFF button |

Joint visualization comes from the XR Hands `HandVisualizer` sample (`Assets/Samples/XR Hands/`).

The loose `PythonMapper/*.py` files are older copies of the modules in `PythonMapper/hand_mapper/hand_mapper/`. Use the package versions.
