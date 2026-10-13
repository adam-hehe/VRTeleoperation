# VR Teleoperation and Haptic Glove

This project explores VR-based teleoperation of a robotic hand using real-time hand tracking and haptic feedback. A Meta Quest headset is used to capture human hand motion in Unity, which is streamed through ROS 2 as normalized finger angles to control a robotic hand (the Pollen Robotics **AmazingHand**). The system is designed to eventually provide force and contact feedback to a wearable haptic glove, enabling closed-loop interaction.

```
Meta Quest (XR Hands) ──Link──► Unity ──/vr_hand_joints──► ROS 2 finger_angles ──/vr_finger_angles──► robot hand
```

`/vr_finger_angles` is a `Float32MultiArray` of `[thumb, index, middle, ring, little]`, where `0` = closed and `1` = open.

---

## Quick start

Full instructions are in [docs/setup.md](docs/setup.md). In short:

1. **Build a ROS 2 workspace** (Ubuntu / WSL2) with `ROS-TCP-Endpoint` and this repo's `PythonMapper/hand_mapper` package.
2. **Clone the Unity project** from [VRTeleoperation-Unity](https://github.com/adam-hehe/VRTeleoperation-Unity), open it in Unity 6000.3.10f1, and set **Robotics → ROS Settings → ROS IP Address** to your ROS machine's IP.
3. **Run:**
   ```bash
   ros2 run ros_tcp_endpoint default_server_endpoint --ros-args -p ROS_IP:=<ROS machine IP>
   # press Play in Unity
   ros2 run hand_mapper finger_angles
   ros2 topic echo /vr_finger_angles
   ```

---

## Documentation

| Doc | Contents |
|---|---|
| [setup.md](docs/setup.md) | Unity + ROS 2 setup, running the pipeline, output format |
| [hardware.md](docs/hardware.md) | Driving the physical AmazingHand from `/vr_finger_angles` |
| [architecture.md](docs/architecture.md) | System design, ROS topics, repository layout |
| [troubleshooting.md](docs/troubleshooting.md) | Common problems and fixes |
| [simulation.md](docs/simulation.md) | MuJoCo prototype (experimental) |
| [haptics.md](docs/haptics.md) | Haptic glove (TBD) |

---

## Current status

- VR hand tracking via Meta Quest XR Hands is functional
- Unity publishes joint data to ROS 2; finger openness is computed and published
- Hardware driver for the physical AmazingHand is implemented
- A MuJoCo simulation was used for prototyping
- Haptic glove redesign and force-feedback integration are in progress
