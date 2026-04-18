using UnityEngine;

public class USBCameraSource : ICameraSource
{
    private WebCamTexture webcam;
    private int deviceIndex;

    public USBCameraSource(int index = 0)
    {
        deviceIndex = index;
    }

    public void Initialize()
    {
        var devices = WebCamTexture.devices;

        if (devices.Length == 0)
        {
            Debug.LogError("No USB cameras found.");
            return;
        }

        // Log all available cameras so you can identify the right index
        for (int i = 0; i < devices.Length; i++)
            Debug.Log($"[USBCamera] index {i}: {devices[i].name}");

        if (deviceIndex >= devices.Length)
        {
            Debug.LogError($"[USBCamera] Device index {deviceIndex} not found. Only {devices.Length} camera(s) available.");
            return;
        }

        webcam = new WebCamTexture(devices[deviceIndex].name, 1280, 720, 30);
        webcam.Play();
        Debug.Log($"[USBCamera] Started: {devices[deviceIndex].name}");
    }

    public Texture GetTexture() => webcam;

    public void Shutdown()
    {
        if (webcam != null && webcam.isPlaying)
            webcam.Stop();
    }
}