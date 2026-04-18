using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Sensor;

public class ROSCameraSource : ICameraSource
{
    private ROSConnection ros;
    private Texture2D texture;
    private string topic;

    public bool IsReceiving { get; private set; }

    public ROSCameraSource(string topicName)
    {
        topic = topicName;
    }

    public void Initialize()
    {
        texture = new Texture2D(2, 2); // LoadImage resizes automatically
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<CompressedImageMsg>(topic, OnImageReceived);
    }

    private void OnImageReceived(CompressedImageMsg msg)
    {
        // Decodes JPEG in-place; resizes texture to match image dimensions
        texture.LoadImage(msg.data);
        IsReceiving = true;
    }

    public Texture GetTexture() => texture;

    public void Shutdown() { }
}