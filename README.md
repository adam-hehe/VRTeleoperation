# VR Teleoperation and Haptic Glove

This project explores VR-based teleoperation of a robotic hand using real-time hand tracking and haptic feedback. A Meta Quest headset is used to capture human hand motion in Unity, which is streamed through ROS2 to control a physical robotic hand. The system is designed to eventually provide force and contact feedback to a wearable haptic glove, enabling closed-loop interaction.

---

## Documentation

Detailed documentation is located in the `docs/` directory:

- **architecture.md** — System architecture and data flow  
- **setup.md** — Startup and runtime instructions  
- **simulation.md** — TBD
- **haptics.md** - TBD

---

## Current Status

- VR hand tracking via Meta Quest XR Hands is functional  
- Unity publishes joint and finger data to ROS2  
- Finger bend angles are computed and published in ROS2  
- Haptic glove redesign and force-feedback integration are in progress  

---

## Technologies Used

- Meta Quest / XR Hands  
- Unity  
- ROS2  
- Python  
- Custom robotic hand hardware  
