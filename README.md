# VR Teleoperation with Haptic Feedback

This project implements a **VR-based teleoperation pipeline** that allows a human operator to control a robotic hand using natural hand motions captured in VR, while receiving **force-based haptic feedback** through a wearable glove.

The system is designed to explore **human–robot interaction (HRI)**, **teleoperation**, and **haptic feedback**, using a modular architecture built on **Unity, ROS 2, and custom hardware drivers**.

---

## System Overview

The teleoperation pipeline is structured as a closed-loop system:

Human Hand
↓
VR Headset (Meta Quest + XR Hands)
↓
Unity (Hand Tracking & Visualization)
↓
ROS 2 (Hand Mapping & Control)
↓
Robotic Hand / Simulation
↓
Contact & Force Feedback
↓
ROS 2
↓
Haptic Glove (Force Feedback)
↓
Human Hand


This bidirectional loop enables the operator to both **control** the robot and **feel interactions** with the environment.

---

## Key Features

- **Natural Hand Tracking**
  - Uses Unity XR Hands (OpenXR) to capture per-joint hand pose data.
  - Visualizes tracked joints and hand meshes in real time.

- **ROS 2 Integration**
  - Publishes hand joint data from Unity to ROS 2.
  - Computes finger bend metrics and contact forces.
  - Designed for clean separation between perception, control, and hardware.

- **Haptic Glove Feedback**
  - Provides per-finger resistance based on robot contact forces.
  - Implements a *virtual hard-stop* model: fingers move freely until contact is detected.
  - Force magnitude is mapped to motor resistance rather than absolute position.

- **Hardware-Agnostic Design**
  - Initial prototypes use micro servos for tendon-based resistance.
  - Architecture supports future upgrades to current-controlled motors for true force feedback.

---

## Design Philosophy

- **Separation of Concerns**
  - Unity handles perception and visualization.
  - ROS 2 handles computation, mapping, and control logic.
  - The glove acts purely as a haptic output device.

- **Safety First**
  - All haptic actuation is bounded by software limits.
  - Resistance is controlled via force mapping, not rigid position enforcement.

- **Research-Oriented**
  - Emphasizes explainability, modularity, and extensibility.
  - Intended as a platform for experimenting with teleoperation and haptics.

---

## Current Status

- XR hand tracking and visualization implemented in Unity.
- ROS 2 pipeline for joint data and finger metrics in progress.
- Haptic glove driver supports per-finger force-based resistance via serial control.
- Ongoing work on force tuning, safety limits, and hardware refinement.

---

## Future Work

- Upgrade glove actuators to current-controlled motors for smoother force feedback.
- Integrate physics-based contact forces from simulation environments.
- Add calibration routines for different hand sizes.
- Explore bilateral control stability and latency effects.


