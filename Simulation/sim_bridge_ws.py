#!/usr/bin/env python3
'''
1) This file represents a rosbridge client talking to ROS from the outside over a WebScoket (it is not a node)
2) Subscribes to:
- /vr_hand_joints (std_msgs/String, JSON format) = contains wrist mocap pose
-- data in the format of data: '{"right_hand": {"Wrist": {"x": 0.077, "y": 0.077, "z": 0.077, "qx": 0.077, "qy": 0.077, "qz": 0.077, "qw": 0.077}}}'
- vr_finger_angles (std_msgs/Float32MultiArray, 5 floats) = contains 5 finger bend percentages
-- data in format of [thumb, index, middle, ring, pinky] with each value between 0 and 1
3) Publishes to:
- /amazing_hand/finger_forces (stds_msgs/Float32MultiArray, 4 floats) = contains 4 total force magnitudes
-- data in format of [F_index, F_middle, F_ring, F_thumb] in Newtons
4) Purpose of this script:
- to render a simulation containing the Amazing Hand and other object to interact with
- update simulation based on real-time data of wrist pose and finger bend percentage values
- simulate contacts and forces between the Amazing Hand and other objects
'''

import time
import math
import json
import signal
from typing import List
import numpy as np
import mujoco
import mujoco.viewer as mjv
import roslibpy

# --- Configuration of Parameters --- #
WSL_IP = '172.25.52.251' # Put your WSL2/ros_tcp_endpoint IP
WSL_PORT = 10000 # Put your ros_tcp_endpoint port
XML_PATH = "/Users/adamconnor/Desktop/Projects/VRTeleoperation/Simulation/amazing_hand_wrapper.xml" # Put your path of XML file location

VR_HAND_POSES_TOPIC = '/vr_hand_joints' # std_msgs/String(JSON) = contains wrist pose, along with other raw joint poses that are not directly used
FINGER_BEND_PERC_TOPIC = '/vr_finger_angles' # std_msgs/Float32MultiArray = 5 floats in [0,1] in order of [thumb, index, middle, ring, pinky]
FORCES_TOPIC = '/amazing_hand/finger_forces'  # std_msgs/Float32MultiArray = 4 floats in order of [F_index, F_middle, F_ring, F_thumb]

FORCES_PUB_HZ = 50.0 # freq of publishing fingertip forces
FORCE_ALPHA = 0.2 # low-pass filter smoothing tuning parameter (0.0 disables filter)

def quat_mult(q1, q2):
    """
    Hamilton product of two quaternions (both q1 and q2 are in [w, x, y, z] format)
    Returns: q = q1 x q2 (rotation q2 applied, then q1)
    """
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2

    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2
    ], dtype=float)

def rot_mat_to_quat(R):
    """
    Convert a 3x3 rotation matrix to a quaternion (w, x, y, z).
    """
    r11, r12, r13 = R[0, 0], R[0, 1], R[0, 2]
    r21, r22, r23 = R[1, 0], R[1, 1], R[1, 2]
    r31, r32, r33 = R[2, 0], R[2, 1], R[2, 2]

    trace = r11 + r22 + r33

    if trace > 0.0:
        r = math.sqrt(1.0 + trace)
        s = 0.5 * (1/r)
        w = 0.5 * r
        x = (r32 - r23) * s
        y = (r13 - r31) * s
        z = (r21 - r12) * s
    elif (r11 > r22) and (r11 > r33):
        r = math.sqrt(1.0 + r11 - r22 - r33)
        s = 0.5 * (1/r)
        w = (r32 - r23) * s
        x = 0.5 * r
        y = (r12 + r21) * s
        z = (r13 + r31) * s
    elif r22 > r33:
        r = math.sqrt(1.0 + r22 - r11 - r33)
        s = 0.5 * (1/r)
        w = (r13 - r31) * s
        x = (r12 + r21) * s
        y = 0.5 * r
        z = (r23 + r32) * s
    else:
        r = math.sqrt(1.0 + r33 - r11 - r22)
        s = 0.5 * (1/r)
        w = (r21 - r12) * s
        x = (r13 + r31) * s
        y = (r23 + r32) * s
        z = 0.5 * r

    q = np.array([w, x, y, z], dtype=float)
    q /= np.linalg.norm(q)
    return q

# Rotation matrix R for coordinate frame mapping between Unity and Mujoco
R = np.array([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ], dtype=float)
q_rot = rot_mat_to_quat(R)

# --- Shutdown Flag Using OS Signal Handlers --- #
_running = True
def _handle_shutdown_signal(signum, frame):
    global _running
    _running = False
signal.signal(signal.SIGINT, _handle_shutdown_signal)
signal.signal(signal.SIGTERM, _handle_shutdown_signal)

# --- MuJoCo Configuration --- #
m = mujoco.MjModel.from_xml_path(XML_PATH)
d = mujoco.MjData(m)
DELTA_T = m.opt.timestep

MOTOR_JOINT_NAMES = [
    "finger1_motor1","finger1_motor2", # index
    "finger2_motor1","finger2_motor2", # middle
    "finger3_motor1","finger3_motor2", # ring
    "finger4_motor1","finger4_motor2", # thumb
]
assert m.nu == len(MOTOR_JOINT_NAMES), f"ERROR: model has {m.nu} actuators, but expected {len(MOTOR_JOINT_NAMES)}"

motor_joint_ids = [m.joint(name).id for name in MOTOR_JOINT_NAMES]
motor_joint_qpos_adrs = [m.jnt_qposadr[id] for id in motor_joint_ids]

MOTOR_CLOSE_SIGNS = np.array([+1, -1, +1, -1, +1, -1, +1, -1], dtype=float)
MOTOR_CLOSE_MAX_ANGLE = 1.57

# --- Wrist Pose --- #
try:
    wrist_body_id = m.body("r_wrist_interface").id
    wrist_mocap_id = m.body_mocapid[wrist_body_id]
    if wrist_mocap_id < 0:
        print("WARNING: r_wrist_interface has mocap=false --> wrist pose cannot be controlled")
        wrist_mocap_id = None
    else:
       print(f"Wrist mocap id = {wrist_mocap_id}")
except Exception:
    print("WARNING: r_wrist_interface body not found --> wrist pose cannot be controlled")
    wrist_mocap_id = None

def update_wrist_pose(payload: str):
    # Extract wrist pose data 
    if wrist_mocap_id is None:
        return
    try: 
        joints_pose_data_json = json.loads(payload)
        wrist_pose = joints_pose_data_json["right_hand"]["Wrist"]
    except Exception:
        print("WARNING: unexpected wrist pose data format --> wrist pose cannot be controlled")
        return
            
    # Update wrist position
    try:
        wrist_pos_raw = np.array([
            float(wrist_pose.get("x", d.mocap_pos[wrist_mocap_id][0])),
            float(wrist_pose.get("y", d.mocap_pos[wrist_mocap_id][1])),
            float(wrist_pose.get("z", d.mocap_pos[wrist_mocap_id][2])),
        ])
        wrist_pos_rotated = R @ wrist_pos_raw # wrist_pos_rotated = pivot + R @ (wrist_pos_raw - pivot)
        d.mocap_pos[wrist_mocap_id][:] = wrist_pos_rotated.tolist()
    except Exception:
        # print("WARNING: unexpected wrist pose data format --> wrist pose cannot be controlled")
        pass

    # Update wrist orientation
    try:
        qx = float(wrist_pose.get("qx", 0.0))
        qy = float(wrist_pose.get("qy", 0.0))
        qz = float(wrist_pose.get("qz", 0.0))
        qw = float(wrist_pose.get("qw", 1.0))
        q_unity = np.array([qw, qx, qy, qz], dtype=float)
        q_unity /= np.linalg.norm(q_unity) + 1e-12
        q_mujoco = quat_mult(q_rot, q_unity)
        d.mocap_quat[wrist_mocap_id][:] = q_mujoco.tolist()
    except Exception:
        # print("WARNING: unexpected wrist pose data format --> wrist pose cannot be controlled")
        pass

# --- Commanding Finger Motors --- #
cmd_target = np.zeros(m.nu, dtype=float)

def command_finger_motors(finger_bend_perc: List[float]):
    global cmd_target
    if len(finger_bend_perc) != 5:
        print("WARNING: unexpected finger bend percentage data format --> finger motors cannot be controlled")
        return
    
    for n in range(4):
        finger_bend_perc[n] = min(1.0, max(finger_bend_perc[n], 0.0))
        motor_angle_mag = float(finger_bend_perc[n]) * MOTOR_CLOSE_MAX_ANGLE
        index_0, index_1 = 2*n, 2*n+1
        cmd_target[index_0] = MOTOR_CLOSE_SIGNS[index_0] * motor_angle_mag
        cmd_target[index_1] = MOTOR_CLOSE_SIGNS[index_1] * motor_angle_mag

    cmd_target = np.roll(cmd_target, -2)

# --- Fingertip Forces --- #
FINGERTIP_SITES = ["tip1","tip2","tip3","tip4"] # tip1 = index, tip2 = middle, tip3 = ring, tip4 = thumb
fingertip_site_ids = [m.site(site).id for site in FINGERTIP_SITES]
fingertip_bodies = [m.site_bodyid[id] for id in fingertip_site_ids]

# For each fingertip body, collect all of its collidable geoms
fingertip_geom_ids = [[] for _ in range(len(FINGERTIP_SITES))]
for geom_id in range(m.ngeom):
    geom_body_id = m.geom_bodyid[geom_id]
    if geom_body_id in fingertip_bodies:
        contype, conaffinity = m.geom_contype[geom_id], m.geom_conaffinity[geom_id]
        if contype > 0 and conaffinity > 0:
            finger_index = fingertip_bodies.index(geom_body_id)
            fingertip_geom_ids[finger_index].append(geom_id)

print("Fingertip collidable geom counts per finger:", [len(geoms) for geoms in fingertip_geom_ids])

# Create map for fast lookup of geom_id to corresponding finger_index
_geom_id_to_finger_index = -np.ones(m.ngeom, dtype=int)
for finger_index, list_geom_id in enumerate(fingertip_geom_ids):
    for geom_id in list_geom_id:
        _geom_id_to_finger_index[geom_id] = finger_index

def get_fingertip_forces_raw() -> np.ndarray:
    forces = np.zeros(4, dtype=float)
    if d.ncon == 0:
        return forces
    contact_forces_torques = np.zeros(6, dtype=float)
    for contact_index in range(d.ncon):
        mujoco.mj_contactForce(m, d, contact_index, contact_forces_torques)
        F_mag = float(np.linalg.norm(contact_forces_torques[:3]))
        contact_obj = d.contact[contact_index]
        contact_obj_index_1 = _geom_id_to_finger_index[contact_obj.geom1]
        if contact_obj_index_1 >= 0:
            forces[contact_obj_index_1] += F_mag
        contact_obj_index_2 = _geom_id_to_finger_index[contact_obj.geom2]
        if contact_obj_index_2 >= 0:
            forces[contact_obj_index_2] += F_mag
    return forces

# --- ROS Bridge and Callbacks --- #
client = roslibpy.Ros(host=WSL_IP, port=WSL_PORT)

vr_hand_poses_sub  = roslibpy.Topic(client, VR_HAND_POSES_TOPIC, 'std_msgs/String')
finger_bend_perc_sub  = roslibpy.Topic(client, FINGER_BEND_PERC_TOPIC, 'std_msgs/Float32MultiArray')
forces_pub = roslibpy.Topic(client, FORCES_TOPIC, 'std_msgs/Float32MultiArray')

_fingertip_forces_filtered = np.zeros(4, dtype=float)

def update_wrist_pose_callback(msg):
    data_poses_json_str = msg.get('data', '')
    if isinstance(data_poses_json_str, str):
        update_wrist_pose(data_poses_json_str)

def update_motor_cmds_callback(msg):
    data_finger_bend_perc_list = msg.get('data', [])
    if isinstance(data_finger_bend_perc_list, list):
        command_finger_motors(data_finger_bend_perc_list)

def publish_forces_callback():
    global _fingertip_forces_filtered
    fingertip_forces_raw = get_fingertip_forces_raw()
    if FORCE_ALPHA > 0.0:
        _fingertip_forces_filtered = FORCE_ALPHA * fingertip_forces_raw + (1.0 - FORCE_ALPHA) * _fingertip_forces_filtered
        output_forces = _fingertip_forces_filtered
    else:
        output_forces = fingertip_forces_raw
    forces_pub.publish(roslibpy.Message({'data': [float(x) for x in output_forces]}))

# --- Main --- #
def main():
    mujoco.mj_forward(m, d)

    client.run()
    vr_hand_poses_sub.subscribe(update_wrist_pose_callback)
    finger_bend_perc_sub.subscribe(update_motor_cmds_callback)

    next_pub_time = 0.0

    with mjv.launch_passive(m, d) as viewer:
        print("System Launch Successful")
        while _running and client.is_connected and viewer.is_running():
            now = time.time()

            d.ctrl[:] = cmd_target
            mujoco.mj_step(m, d)
            if now >= next_pub_time:
                publish_forces_callback()
                next_pub_time = now + 1.0 / FORCES_PUB_HZ
            viewer.sync()
            time.sleep(0.001)
    
    try:
        vr_hand_poses_sub.unsubscribe()
    except Exception:
        pass
    try:
        finger_bend_perc_sub.unsubscribe()
    except Exception:
        pass
    try:
        forces_pub.unadvertise()
    except Exception:
        pass
    try:
        client.terminate()
    except Exception:
        pass
    print("System Shutdown Complete")

if __name__ == "__main__":
    main()
