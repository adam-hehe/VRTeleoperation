'''
hand_openness.py
----------------

This module processes Unity XR Hands joint data (received as JSON) and computes
a normalized openness value (0-1) for each finger of the right hand.

NOTE: Ignores wrist data for now; focus is on finger openness.

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

import json
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

    total_bend = pip + dip  # closed finger = large bend

    # TODO: calibrate these values
    CLOSED = 1.0
    OPEN   = 0.0   

    openness = normalize((CLOSED - total_bend), (CLOSED - OPEN), (CLOSED - CLOSED))
    return float(openness)

def compute_hand_openness(json_data):
    """
    Main function: extract openness of all fingers
    """
    if "right_hand" not in json_data:
        raise ValueError("JSON has no 'right_hand' field")

    hand = json_data["right_hand"]

    # Finger joint names in XRHands ordering
    INDEX = ("IndexProximal", "IndexIntermediate", "IndexDistal", "IndexTip")
    MIDDLE = ("MiddleProximal", "MiddleIntermediate", "MiddleDistal", "MiddleTip")
    RING = ("RingProximal", "RingIntermediate", "RingDistal", "RingTip")
    LITTLE = ("LittleProximal", "LittleIntermediate", "LittleDistal", "LittleTip")

    # Thumb is special (only 3 joints)
    THUMB = ("ThumbProximal", "ThumbDistal", "ThumbTip")
    
    # Approximate thumb openness using angle between proximal–distal–tip
    thumb_angle = joint_angle(hand[THUMB[0]], hand[THUMB[1]], hand[THUMB[2]])
    thumb_open = normalize(thumb_angle, 0.2, 1.2)  # tunable

    return {
        "thumb":  thumb_open,
        "index":  finger_openness(hand, INDEX),
        "middle": finger_openness(hand, MIDDLE),
        "ring":   finger_openness(hand, RING),
        "little": finger_openness(hand, LITTLE)
    }