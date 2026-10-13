# Simulation (Experimental)

[`Simulation/sim_bridge_ws.py`](../Simulation/sim_bridge_ws.py) is a MuJoCo model of the AmazingHand that follows the VR hand. It was used to prototype the pipeline before the hardware was ready.

- It subscribes to `/vr_finger_angles` (finger openness) and `/vr_hand_joints` (wrist pose).
- It publishes simulated fingertip contact forces on `/amazing_hand/finger_forces` (`[F_index, F_middle, F_ring, F_thumb]`, in N).
- It connects to ROS from outside, as a `roslibpy` client of a **rosbridge** WebSocket server (`rosbridge_suite`), not as a ROS node.
- Its Python dependencies (`mujoco`, `roslibpy`, `numpy`) are listed in [`requirements.txt`](../requirements.txt). That file is only for the simulation; the main pipeline doesn't need it.

> **Note:** The simulation can't be fully reproduced from this repo. The AmazingHand mesh files (`Simulation/assets/`) aren't committed, and the connection settings and model path are hard-coded at the top of the script. Use it as a reference, not as a supported setup.
