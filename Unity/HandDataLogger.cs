using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR.Hands;

public class HandDataLogger : MonoBehaviour
{
    XRHandSubsystem handSubsystem;

    // Store logs if needed
    public bool logToConsole = true;

    void Start()
    {
        // Get the XRHandSubsystem (the provider)
        List<XRHandSubsystem> subsystems = new List<XRHandSubsystem>();
        SubsystemManager.GetInstances(subsystems);

        if (subsystems.Count > 0)
        {
            handSubsystem = subsystems[0];
            Debug.Log("XRHandSubsystem found.");
        }
        else
        {
            Debug.LogError("No XRHandSubsystem found. Ensure XR Hands + OpenXR are enabled.");
        }
    }

    void Update()
    {
        if (handSubsystem == null) return;

        var left = handSubsystem.leftHand;
        var right = handSubsystem.rightHand;

        LogHand("Left", left);
        LogHand("Right", right);
    }

    void LogHand(string label, XRHand hand)
    {
        if (!hand.isTracked) return;

        // Wrist joint
        XRHandJoint wrist = hand.GetJoint(XRHandJointID.Wrist);

        if (logToConsole)
        {
            Debug.Log($"{label} Wrist: {wrist.pose.position}");
        }

        // Loop through all valid XRHandJointID values
        foreach (XRHandJointID jointID in System.Enum.GetValues(typeof(XRHandJointID)))
        {
            XRHandJoint joint = hand.GetJoint(jointID);

            if (joint.TryGetPose(out Pose pose))
            {
                if (logToConsole)
                    Debug.Log($"{label} {jointID}: {pose.position}");
            }
        }
    }
}
