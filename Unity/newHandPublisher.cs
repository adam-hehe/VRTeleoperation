/*
 * HandToROS.cs
 * --------------------
 * This component publishes right-hand joint data from Unity’s XR Hands system 
 * to ROS2 using the ROS-TCP-Connector. The script streams joint positions 
 * (x, y, z) for every tracked joint in the right hand, and optionally publishes 
 * wrist orientation if needed by downstream ROS nodes.
 */

using System;
using System.Collections.Generic;
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

using UnityEngine.XR;
using UnityEngine.XR.Hands;
using UnityEngine.XR.Management;   // <— important

// Minimal JSONObject helper to avoid external dependencies.
class JSONObject
{
    private Dictionary<string, string> fields = new Dictionary<string, string>();

    public JSONObject() { }

    public void AddField(string name, float value)
    {
        fields[name] = value.ToString("R", System.Globalization.CultureInfo.InvariantCulture);
    }

    public void AddField(string name, JSONObject obj)
    {
        fields[name] = obj.Print();
    }

    public string Print()
    {
        var sb = new System.Text.StringBuilder();
        sb.Append("{");
        bool first = true;
        foreach (var kv in fields)
        {
            if (!first) sb.Append(",");
            first = false;
            sb.Append("\"");
            sb.Append(kv.Key);
            sb.Append("\":");
            sb.Append(kv.Value);
        }
        sb.Append("}");
        return sb.ToString();
    }
}

public class HandToROS : MonoBehaviour
{
    ROSConnection ros;
    public string topicName = "/vr_hand_joints";

    XRHandSubsystem handSubsystem;
    static readonly List<XRHandSubsystem> s_SubsystemsReuse = new List<XRHandSubsystem>();
    bool loggedSubsystemFound = false;

    void Awake()
    {
        TryFindHandSubsystem();
    }

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<StringMsg>(topicName);
    }

    void TryFindHandSubsystem()
    {
        // First, try via XR Management active loader (most reliable)
        var loader = XRGeneralSettings.Instance?.Manager?.activeLoader;
        if (loader != null)
        {
            handSubsystem = loader.GetLoadedSubsystem<XRHandSubsystem>();
        }

        // Fallback: query all XRHandSubsystems
        if (handSubsystem == null)
        {
            s_SubsystemsReuse.Clear();
            SubsystemManager.GetSubsystems(s_SubsystemsReuse);
            for (int i = 0; i < s_SubsystemsReuse.Count; ++i)
            {
                var sub = s_SubsystemsReuse[i];
                if (sub != null && sub.running)
                {
                    handSubsystem = sub;
                    break;
                }
            }
        }

        if (handSubsystem == null)
        {
            // Soft warning, because XR might not be fully started yet
            Debug.LogWarning("[HandToROS] No XRHandSubsystem running yet. Will keep trying.");
        }
        else if (!loggedSubsystemFound)
        {
            loggedSubsystemFound = true;
            Debug.Log("[HandToROS] XRHandSubsystem found. Hand data will be published.");
        }
    }

    void Update()
    {
        // Keep trying until we find a running subsystem
        if (handSubsystem == null || !handSubsystem.running)
        {
            TryFindHandSubsystem();
            if (handSubsystem == null || !handSubsystem.running)
                return;
        }

        // Only right hand, as per your design
        XRHand rightHand = handSubsystem.rightHand;
        if (!rightHand.isTracked)
            return;

        var rootJson = new JSONObject();
        var rightJson = new JSONObject();

        foreach (XRHandJointID id in Enum.GetValues(typeof(XRHandJointID)))
        {
            if (id == XRHandJointID.Invalid || id == XRHandJointID.EndMarker)
                continue;

            XRHandJoint joint = rightHand.GetJoint(id);

            Pose poseRight;
            if (!joint.TryGetPose(out poseRight))
                continue;

            JSONObject jointObj = new JSONObject();
            jointObj.AddField("x", poseRight.position.x);
            jointObj.AddField("y", poseRight.position.y);
            jointObj.AddField("z", poseRight.position.z);

            if (id == XRHandJointID.Wrist)
            {
                jointObj.AddField("qx", poseRight.rotation.x);
                jointObj.AddField("qy", poseRight.rotation.y);
                jointObj.AddField("qz", poseRight.rotation.z);
                jointObj.AddField("qw", poseRight.rotation.w);
            }

            rightJson.AddField(id.ToString(), jointObj);
        }

        rootJson.AddField("right_hand", rightJson);
        ros.Publish(topicName, new StringMsg(rootJson.Print()));
    }
}
