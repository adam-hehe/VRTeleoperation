using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Sensor;

public class ROSCameraSource : ICameraSource
{
    private ROSConnection ros;
    private Texture2D texture;
    private string topic;

    public ROSCameraSource(string topicName)
    {
        topic = topicName;
    }

    public void Initialize()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<ImageMsg>(topic, ImageCallback);
    }

    private void ImageCallback(ImageMsg msg)
    {
        if (texture == null)
            texture = new Texture2D((int)msg.width, (int)msg.height, TextureFormat.RGB24, false);

        texture.LoadRawTextureData(msg.data);
        texture.Apply();
    }

    public Texture GetTexture()
    {
        return texture;
    }

    public void Shutdown()
    {
        // Optional: Unsubscribe if needed
    }
}