using UnityEngine;
using UnityEngine.UI;

public class CameraDisplayManager : MonoBehaviour
{
    public enum CameraType { USB, ROS }
    public CameraType cameraType;

    public RawImage display;
    [Tooltip("0 = built-in webcam, 1+ = external USB cameras")]
    public int usbDeviceIndex = 0;
    public string rosTopic = "/camera/image/compressed";

    private ICameraSource cameraSource;

    void Start()
    {
        switch (cameraType)
        {
            case CameraType.USB:
                cameraSource = new USBCameraSource(usbDeviceIndex);
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