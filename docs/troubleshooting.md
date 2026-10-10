# Troubleshooting

## Unity → ROS → finger angles

| Symptom | Check |
|---|---|
| Unity HUD shows red arrows / no connection | `ROS IP Address` in **Robotics → ROS Settings** must match `hostname -I` on the ROS machine. Is `ros_tcp_endpoint` running? Is Windows Firewall blocking port 10000? |
| Worked yesterday, not today (WSL2) | The WSL2 IP changes on reboot. Re-check `hostname -I` and update Unity. |
| `[HandToROS] No XRHandSubsystem running yet` | Hand tracking isn't active. Check that Link is the active OpenXR runtime, *Developer Runtime Features* is enabled, and the headset is tracking your hands (put the controllers down). |
| `/vr_hand_joints` is empty | Unity must be in Play Mode, with the headset connected over Link. |
| `/vr_hand_joints` has data but `/vr_finger_angles` doesn't | Is `finger_angles` running? Run `ros2 node list`. Look for `Error processing hand data` in its terminal. |
| `JSON has no 'right_hand' field` | Your right hand isn't being tracked. Only the right hand is processed. |
| Values stuck near 0 or 1, or never reach the extremes | Retune the `OPEN` and `CLOSED` constants. See [setup.md](setup.md#4-output-format). |

## Hardware

| Symptom | Check |
|---|---|
| `rustypot not found` | `pip install rustypot` in the same Python environment ROS uses. |
| `could not open port /dev/ttyACM0` | The device isn't attached to WSL (`usbipd attach`), the port name is wrong, or the user isn't in the `dialout` group. |
| Fingers move the wrong direction or are offset | Recalibrate `MIDDLE_POS_DEG`. See [hardware.md](hardware.md#3-calibrate). |
