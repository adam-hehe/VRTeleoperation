using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

public class HandToROS : MonoBehaviour
{
    public HandVisualizer visualizer;
    ROSConnection ros;
    public string topicName = "/vr_hand_joints";

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
        //var leftJson = new JSONObject();
        var rightJson = new JSONObject();

        // Loop through all joint IDs once
        foreach (XRHandJointID id in System.Enum.GetValues(typeof(XRHandJointID)))
        {
            if (id == XRHandJointID.Invalid || id == XRHandJointID.EndMarker)
                continue;

            /* LEFT HAND
            Pose poseLeft;
            if (visualizer.TryGetJointPose(Handedness.Left, id, out poseLeft))
            {
                JSONObject jointObj = new JSONObject();
                jointObj.AddField("x", poseLeft.position.x);
                jointObj.AddField("y", poseLeft.position.y);
                jointObj.AddField("z", poseLeft.position.z);

                leftJson.AddField(id.ToString(), jointObj);
            }
            */

            // RIGHT HAND
            Pose poseRight;
            if (visualizer.TryGetJointPose(Handedness.Right, id, out poseRight))
            {
                JSONObject jointObj = new JSONObject();
                jointObj.AddField("x", poseRight.position.x);
                jointObj.AddField("y", poseRight.position.y);
                jointObj.AddField("z", poseRight.position.z);

                jointObj.AddField("qx", poseRight.rotation.x);
                jointObj.AddField("qy", poseRight.rotation.y);
                jointObj.AddField("qz", poseRight.rotation.z);
                jointObj.AddField("qw", poseRight.rotation.w);

                rightJson.AddField(id.ToString(), jointObj);
            }
        }

        // Build final JSON structure
        //rootJson.AddField("left_hand", leftJson);
        rootJson.AddField("right_hand", rightJson);

        ros.Publish(topicName, new StringMsg(rootJson.Print()));
    }
}
