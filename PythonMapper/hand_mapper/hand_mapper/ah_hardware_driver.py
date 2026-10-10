#!/usr/bin/env python3
"""
AmazingHand Hardware Driver
---------------------------
ROS2 node that translates /vr_finger_angles → physical SCS0009 servo commands.

Drop-in replacement for sim_bridge_ws.py — same topics in and out, but sends
commands to the real hand instead of the MuJoCo simulation.

Hardware:
    Feetech SCS0009 servos × 8 (2 per finger)
    Connected via USB TTL serial adapter → /dev/ttyACM0
    Library: rustypot  (pip install rustypot)

Servo IDs (right hand):
    Index  → motor1=1, motor2=2
    Middle → motor1=3, motor2=4
    Ring   → motor1=5, motor2=6
    Thumb  → motor1=7, motor2=8

Calibration:
    MIDDLE_POS_DEG holds a per-motor offset (degrees) so that position=0
    corresponds to the finger's neutral pose. Default values come from
    r_hand.toml in the AmazingHand repo. Re-run the get_zeros calibration
    tool from AHControl and update MIDDLE_POS_DEG to match your physical hand.

    AHControl calibration (run once, then update values below):
        cargo run --bin get_zeros -- --serialport /dev/ttyACM0 \
            --config Demo/AHControl/config/r_hand.toml

Topics:
    Subscribes:  /vr_finger_angles  (std_msgs/Float32MultiArray)
                 5 floats [thumb, index, middle, ring, little] ∈ [0,1]
    Publishes:   /amazing_hand/finger_forces  (std_msgs/Float32MultiArray)
                 4 floats [F_index, F_middle, F_ring, F_thumb] — servo load
                 as a proxy for contact force (Newtons, approximate)
"""

import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray

try:
    from rustypot import Scs0009PyController
except ImportError:
    raise ImportError(
        "rustypot not found. Install with:  pip install rustypot"
    )

# ── Angle calibration ────────────────────────────────────────────────────────
# Degrees added to every commanded angle to compensate for assembly offset.
# Index into this list with (servo_id - 1).
# Source: r_hand.toml from pollen-robotics/AmazingHand (converted to degrees).
# Update after running AHControl get_zeros calibration on your physical hand.
MIDDLE_POS_DEG = [
    7.0,   # ID 1  (index  motor1)
    5.0,   # ID 2  (index  motor2)
    0.0,   # ID 3  (middle motor1)
    7.0,   # ID 4  (middle motor2)
    5.0,   # ID 5  (ring   motor1)
    7.0,   # ID 6  (ring   motor2)
    0.0,   # ID 7  (thumb  motor1)
    7.0,   # ID 8  (thumb  motor2)
]

# ── Motion limits (degrees, relative to MIDDLE_POS_DEG) ─────────────────────
OPEN_DEG  = -35.0   # motor1 position when finger is fully open
CLOSE_DEG =  90.0   # motor1 position when finger is fully closed
# motor2 always mirrors: open=+35°, close=-90°

# ── Servo → finger mapping ───────────────────────────────────────────────────
# (motor1_id, motor2_id) for each finger, keyed by name
FINGER_MOTORS = {
    "index":  (1, 2),
    "middle": (3, 4),
    "ring":   (5, 6),
    "thumb":  (7, 8),
}

# /vr_finger_angles arrives as [thumb, index, middle, ring, little]
# Map array index → finger name (little has no motor, so it is skipped)
ANGLE_INDEX_TO_FINGER = {
    0: "thumb",
    1: "index",
    2: "middle",
    3: "ring",
    # 4: "little" — AmazingHand has no little finger motor
}

# Load-to-force scale factor (empirical — tune per hand)
# SCS0009 load register reports 0–1000 (arbitrary units).
# Rough estimate: 1000 units ≈ 0.5 N fingertip force.
LOAD_TO_NEWTON = 0.0005

COMMAND_SPEED = 5   # servo speed (1=slowest, ~10=fastest for SCS0009)


def _openness_to_pos_rad(openness: float, motor1_id: int, motor2_id: int):
    """
    Convert a normalised openness value [0=closed, 1=open] to a pair of
    goal positions in radians for a finger's two servo motors.
    """
    closedness = 1.0 - float(np.clip(openness, 0.0, 1.0))
    range_deg = CLOSE_DEG - OPEN_DEG  # 125°

    mid1 = MIDDLE_POS_DEG[motor1_id - 1]
    mid2 = MIDDLE_POS_DEG[motor2_id - 1]

    # motor1: from OPEN_DEG (open) to CLOSE_DEG (closed)
    angle1_deg = mid1 + OPEN_DEG + range_deg * closedness
    # motor2: mirrored
    angle2_deg = mid2 - OPEN_DEG - range_deg * closedness

    return np.deg2rad(angle1_deg), np.deg2rad(angle2_deg)


class AHHardwareDriver(Node):
    def __init__(self):
        super().__init__("ah_hardware_driver")

        self.declare_parameter("serial_port", "/dev/ttyACM0")
        self.declare_parameter("baudrate", 1_000_000)
        self.declare_parameter("torque_off_on_shutdown", True)

        port = self.get_parameter("serial_port").value
        baud = self.get_parameter("baudrate").value
        self._torque_off_on_shutdown = self.get_parameter("torque_off_on_shutdown").value

        self.get_logger().info(f"Connecting to AmazingHand on {port} @ {baud} baud …")

        self._ctrl = Scs0009PyController(
            serial_port=port,
            baudrate=baud,
            timeout=0.5,
        )

        # Enable torque on all 8 motors
        for motor_id in range(1, 9):
            self._ctrl.write_torque_enable(motor_id, 1)
        self.get_logger().info("Torque enabled on all 8 motors.")

        self._sub = self.create_subscription(
            Float32MultiArray,
            "/vr_finger_angles",
            self._on_finger_angles,
            10,
        )

        self._forces_pub = self.create_publisher(
            Float32MultiArray,
            "/amazing_hand/finger_forces",
            10,
        )

        # Publish load-derived forces at 20 Hz independently of command rate
        self.create_timer(0.05, self._publish_forces)

        self.get_logger().info("AmazingHand hardware driver ready.")

    # ── Command callback ──────────────────────────────────────────────────────

    def _on_finger_angles(self, msg: Float32MultiArray):
        if len(msg.data) < 4:
            self.get_logger().warn(
                f"Expected ≥4 finger angles, got {len(msg.data)} — skipping.",
                throttle_duration_sec=2.0,
            )
            return

        for idx, finger in ANGLE_INDEX_TO_FINGER.items():
            openness = msg.data[idx]
            m1, m2 = FINGER_MOTORS[finger]
            pos1, pos2 = _openness_to_pos_rad(openness, m1, m2)

            self._ctrl.write_goal_speed(m1, COMMAND_SPEED)
            self._ctrl.write_goal_speed(m2, COMMAND_SPEED)
            self._ctrl.write_goal_position(m1, pos1)
            self._ctrl.write_goal_position(m2, pos2)

    # ── Force feedback ────────────────────────────────────────────────────────

    def _publish_forces(self):
        """
        Read servo load registers and publish as approximate fingertip forces.
        SCS0009 load is a proxy — not a calibrated force sensor — but useful
        for detecting contact. Order: [F_index, F_middle, F_ring, F_thumb].
        """
        forces = []
        for finger in ("index", "middle", "ring", "thumb"):
            m1, m2 = FINGER_MOTORS[finger]
            try:
                load1 = abs(self._ctrl.read_present_load(m1))
                load2 = abs(self._ctrl.read_present_load(m2))
                force_n = ((load1 + load2) / 2.0) * LOAD_TO_NEWTON
            except Exception:
                force_n = 0.0
            forces.append(float(force_n))

        out = Float32MultiArray()
        out.data = forces
        self._forces_pub.publish(out)

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def destroy_node(self):
        if self._torque_off_on_shutdown:
            self.get_logger().info("Disabling torque on all motors …")
            for motor_id in range(1, 9):
                try:
                    self._ctrl.write_torque_enable(motor_id, 2)  # 2 = Off
                except Exception:
                    pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = AHHardwareDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
