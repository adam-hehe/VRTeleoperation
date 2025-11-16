/*
 * HandToROS.cs
 * --------------------
 * This component publishes right-hand joint data from Unity’s XR Hands system 
 * to ROS2 using the ROS-TCP-Connector. The script streams joint positions 
 * (x, y, z) for every tracked joint in the right hand, and optionally publishes 
 * wrist orientation if needed by downstream ROS nodes.
 *
 * PURPOSE:
 *   - Capture real-time VR hand tracking data from the Meta Quest (XR Hands)
 *   - Format joint positions into a JSON dictionary
 *   - Publish the JSON string to a ROS2 topic for teleoperation or analysis
 *
 * PUBLISHED TOPIC: (TBD)
 *   /vr_hand_joints   (std_msgs/String)
 *
 * MESSAGE FORMAT:
 *   {
 *     "right_hand": {
 *         "Wrist":  { "x":..., "y":..., "z":..., ["qx":..., "qy":..., "qz":..., "qw":...] },
 *         "Palm":   { "x":..., "y":..., "z":... },
 *         "ThumbProximal":   { "x":..., "y":..., "z":... },
 *         "ThumbDistal":     { "x":..., "y":..., "z":... },
 *         "ThumbTip":        { "x":..., "y":..., "z":... },
 *         "IndexProximal":   { "x":..., "y":..., "z":... },
 *         "IndexIntermediate": { ... },
 *         "IndexDistal":     { ... },
 *         "IndexTip":        { ... },
 *         ...
 *         (All remaining XR hand joints)
 *     }
 *   }
 *
 * NOTES:
 *   - Only the right hand is published.
 *   - Joint rotations ignored; only wrist rotation is usually needed.
 *   - Assumes the ROS-TCP-Endpoint server is running in ROS2.
 */

 using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

public class HandToROS : MonoBehaviour
{
    public HandVisualizer visualizer;
    ROSConnection ros;
    public string topicName = "/vr_hand_joints"; // Topic name TBD

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<StringMsg>(topicName);
    }

    void Update()
    {

        if (!visualizer.rightHandTracked)
          return;

        var rootJson = new JSONObject();
        var rightJson = new JSONObject();

        // Loop through all joint IDs once
        foreach (XRHandJointID id in System.Enum.GetValues(typeof(XRHandJointID)))
        {
            if (id == XRHandJointID.Invalid || id == XRHandJointID.EndMarker)
                continue;

            Pose poseRight;
            if (visualizer.TryGetJointPose(Handedness.Right, id, out poseRight))
            {
                JSONObject jointObj = new JSONObject();

                jointObj.AddField("x", poseRight.position.x);
                jointObj.AddField("y", poseRight.position.y);
                jointObj.AddField("z", poseRight.position.z);

                if(id == XRHandJointID.Wrist)
                {
                    jointObj.AddField("qx", poseRight.rotation.x);
                    jointObj.AddField("qy", poseRight.rotation.y);
                    jointObj.AddField("qz", poseRight.rotation.z);
                    jointObj.AddField("qw", poseRight.rotation.w);
                }

                rightJson.AddField(id.ToString(), jointObj);
            }
        }

        // Build final JSON structure
        rootJson.AddField("right_hand", rightJson);

        ros.Publish(topicName, new StringMsg(rootJson.Print()));
    }
}
