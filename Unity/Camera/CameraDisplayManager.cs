using UnityEngine;
using UnityEngine.UI;

public class CameraDisplayManager : MonoBehaviour
{
    public enum CameraType { USB, ROS }
    public CameraType cameraType;

    public RawImage display;
    public string rosTopic = "/camera/image_raw";

    private ICameraSource cameraSource;

    void Start()
    {
        switch (cameraType)
        {
            case CameraType.USB:
                cameraSource = new USBCameraSource();
                break;

            case CameraType.ROS:
                cameraSource = new ROSCameraSource(rosTopic);
                break;
        }

        cameraSource.Initialize();
    }

    void Update()
    {
        if (cameraSource != null)
            display.texture = cameraSource.GetTexture();
    }

    void OnDestroy()
    {
        cameraSource?.Shutdown();
    }
}