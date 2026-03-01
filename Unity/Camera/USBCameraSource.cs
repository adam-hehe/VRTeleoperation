using UnityEngine;

public class USBCameraSource : ICameraSource
{
    private WebCamTexture webcam;

    public void Initialize()
    {
        var devices = WebCamTexture.devices;

        if (devices.Length == 0)
        {
            Debug.LogError("No USB cameras found.");
            return;
        }

        webcam = new WebCamTexture(devices[0].name, 640, 480, 30);
        webcam.Play();
    }

    public Texture GetTexture()
    {
        return webcam;
    }

    public void Shutdown()
    {
        if (webcam != null && webcam.isPlaying)
            webcam.Stop();
    }
}