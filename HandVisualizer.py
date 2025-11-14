using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR.Hands;

public class HandVisualizer : MonoBehaviour
{
    XRHandSubsystem handSubsystem;

    Dictionary<string, Transform> jointSpheres = new Dictionary<string, Transform>();

    public float sphereSize = 0.01f;

    void Start()
    {
        // Get XR Hand Subsystem
        var subs = new List<XRHandSubsystem>();
        SubsystemManager.GetInstances(subs);

        if (subs.Count > 0)
            handSubsystem = subs[0];
        else
            Debug.LogError("No XRHandSubsystem found.");
    }

    void Update()
    {
        if (handSubsystem == null) return;

        UpdateHand("Left", handSubsystem.leftHand);
        UpdateHand("Right", handSubsystem.rightHand);
    }

    void UpdateHand(string label, XRHand hand)
    {
        if (!hand.isTracked) return;

        // Loop over all XRHandJointIDs
        foreach (XRHandJointID jointID in System.Enum.GetValues(typeof(XRHandJointID)))
        {
            XRHandJoint joint = hand.GetJoint(jointID);

            if (!joint.TryGetPose(out Pose pose))
                continue;

            string key = $"{label}_{jointID}";
            
            // If sphere doesn’t exist yet, create it
            if (!jointSpheres.ContainsKey(key))
                jointSpheres[key] = CreateSphere(label, jointID);

            // Move sphere to joint
            Transform sphere = jointSpheres[key];
            sphere.position = pose.position;
            sphere.rotation = pose.rotation;
        }
    }

    Transform CreateSphere(string hand, XRHandJointID id)
    {
        GameObject sphere = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        sphere.name = $"{hand}_{id}";
        sphere.transform.localScale = Vector3.one * sphereSize;

        // Optional: different colors for left/right
        var renderer = sphere.GetComponent<MeshRenderer>();
        renderer.material = new Material(Shader.Find("Standard"));
        renderer.material.color = (hand == "Left") ? Color.blue : Color.red;

        return sphere.transform;
    }
}
