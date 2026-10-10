# Hardware (AmazingHand)

The `ah_hardware_driver` node ([source](../PythonMapper/hand_mapper/hand_mapper/ah_hardware_driver.py)) can replace the simulation. It uses the same topics, but drives the physical AmazingHand instead of MuJoCo.

| | Topic | Type |
|---|---|---|
| Subscribes | `/vr_finger_angles` | `std_msgs/Float32MultiArray`: `[thumb, index, middle, ring, little]` openness, 0 to 1. Little is ignored because the hand has no fifth finger. |
| Publishes | `/amazing_hand/finger_forces` | `std_msgs/Float32MultiArray`: `[F_index, F_middle, F_ring, F_thumb]`, estimated from servo load at 20 Hz. This is approximate, not a calibrated force sensor. |

**Hardware:** 8× Feetech SCS0009 servos (2 per finger), connected through a USB-TTL serial adapter.

| Finger | Servo IDs (motor1, motor2) |
|---|---|
| Index | 1, 2 |
| Middle | 3, 4 |
| Ring | 5, 6 |
| Thumb | 7, 8 |

---

## 1. Install the servo library

In the ROS 2 environment:

```bash
pip install rustypot
```

## 2. Connect the hand

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

## 3. Calibrate

`MIDDLE_POS_DEG` in `ah_hardware_driver.py` holds per-servo zero offsets in degrees. The defaults come from the AmazingHand `r_hand.toml`, but every assembled hand is slightly different. Run the `get_zeros` tool from the [AmazingHand](https://github.com/pollen-robotics/AmazingHand) `AHControl` demo and copy the values in:

```bash
cargo run --bin get_zeros -- --serialport /dev/ttyACM0 \
    --config Demo/AHControl/config/r_hand.toml
```

Other constants you may want to tune:

| Constant | Default | Meaning |
|---|---|---|
| `OPEN_DEG` / `CLOSE_DEG` | −35° / 90° | motor1 angle at fully open / fully closed. motor2 mirrors it. |
| `COMMAND_SPEED` | 5 | Servo speed (1 = slowest) |
| `LOAD_TO_NEWTON` | 0.0005 | Scale from servo load units to approximate Newtons |

With `colcon build --symlink-install`, you don't need to rebuild after editing these.

---

## Running

Do steps 1–3 of [setup.md → Run it](setup.md#3-run-it) (headset, endpoint, Unity Play), then:

```bash
ros2 launch hand_mapper hardware.launch.py serial_port:=/dev/ttyACM0
```

This starts both `finger_angles` and `ah_hardware_driver`, so don't run `finger_angles` separately.

| Launch argument | Default |
|---|---|
| `serial_port` | `/dev/ttyACM0` |
| `baudrate` | `1000000` |
| `torque_off_on_shutdown` | `true` |

Torque is disabled on all servos when you stop with Ctrl+C. If you set `torque_off_on_shutdown:=false`, the servos keep holding their last position after shutdown.
