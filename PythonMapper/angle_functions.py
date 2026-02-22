'''
angle_functions.py
----------------

This module processes Unity XR Hands joint data (received as JSON) and computes
a normalized openness value (0-1) for each finger of the right hand.

Assuming data is a JSON Object like this:
"right_hand": {
    "Wrist": {
      "x": 0.215,
      "y": 1.015,
      "z": 0.520,
      "qx": 0.15,
      "qy": 0.22,
      "qz": -0.01,
      "qw": 0.96
    },
    "IndexProximal": {
      "x": 0.255,
      "y": 1.072,
      "z": 0.548,
    },
    "... all other joints ...": {}
  }
}
'''

import numpy as np
from math import acos 


def vec(joint_json):
    """
    Helper: convert JSON joint entry to numpy vector
    """
    return np.array([joint_json['x'], joint_json['y'], joint_json['z']])

def joint_angle(A, B, C):
    """
    Compute angle ABC (at point B) given three joint positions A, B, C
    """
    A = vec(A)
    B = vec(B)
    C = vec(C)

    v1 = A - B
    v2 = C - B

    cosang = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    cosang = np.clip(cosang, -1.0, 1.0)

    return acos(cosang)


def normalize(angle, min_angle, max_angle):
    """
    Normalize angle → 0-1 openness
    "min_angle" = closed → returns 0
    "max_angle" = open  → returns 1 
    """
    angle = np.clip(angle, min_angle, max_angle)
    return (angle - min_angle) / (max_angle - min_angle)


def finger_openness(hand, names):
    """
    Compute the openness of a single finger given it's joint data

    names = tuple of joint names for (proximal, intermediate, distal, tip)
    """

    prox = hand[names[0]]
    inter = hand[names[1]]
    dist = hand[names[2]]
    tip = hand[names[3]]

    # Compute PIP + DIP flexion (sum of two joint bends)
    pip = joint_angle(prox, inter, dist)
    dip = joint_angle(inter, dist, tip)

    pip_bend = abs(np.pi - pip)
    dip_bend = abs(np.pi - dip)

    total_bend = pip_bend + dip_bend  # closed finger = large bend

    # Calibrate finger:
    # print("pip", pip, "dip", dip, "sum", total_bend)

    # Calibrated these values
    CLOSED = 3.0
    OPEN   = 0.1

    openness = 1 - normalize(total_bend, OPEN, CLOSED)
    return float(np.clip(openness, 0.0, 1.0))
    
def thumb_openness(hand):
    wrist = vec(hand["Wrist"])
    thumb_tip = vec(hand["ThumbTip"])

    # Distance from thumb tip to palm/wrist
    dist = np.linalg.norm(thumb_tip - wrist)

    # Calibrate thumb:
    # print("thumb dist", dist)

    # NOTE: OPEN_DIST 0.138 may be more accurate
    OPEN_DIST = 0.14
    CLOSED_DIST = 0.1 

    openness = normalize(dist, CLOSED_DIST, OPEN_DIST)
    return float(np.clip(openness, 0.0, 1.0))

def compute_hand_openness(json_data):
    """
    Returns: [thumb, index, middle, ring, little] ∈ [0,1]^5
    """
    if "right_hand" not in json_data:
        raise ValueError("JSON has no 'right_hand' field")

    hand = json_data["right_hand"]

    INDEX  = ("IndexProximal", "IndexIntermediate", "IndexDistal", "IndexTip")
    MIDDLE = ("MiddleProximal", "MiddleIntermediate", "MiddleDistal", "MiddleTip")
    RING   = ("RingProximal", "RingIntermediate", "RingDistal", "RingTip")
    LITTLE = ("LittleProximal", "LittleIntermediate", "LittleDistal", "LittleTip")

    return np.array([
        thumb_openness(hand),
        finger_openness(hand, INDEX),
        finger_openness(hand, MIDDLE),
        finger_openness(hand, RING),
        finger_openness(hand, LITTLE),
    ], dtype=float)

