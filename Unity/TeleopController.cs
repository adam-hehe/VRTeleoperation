using UnityEngine;
using UnityEngine.UI;

public class TeleopController : MonoBehaviour
{
    public static bool TeleopEnabled = true;

    public Button teleopButton;
    public Text buttonText;

    void Start()
    {
        teleopButton.onClick.AddListener(ToggleTeleop);
        UpdateVisual();
    }

    void ToggleTeleop()
    {
        TeleopEnabled = !TeleopEnabled;
        UpdateVisual();
        Debug.Log("Teleop: " + TeleopEnabled);
    }

    void UpdateVisual()
    {
        if (buttonText != null)
            buttonText.text = TeleopEnabled ? "ON" : "OFF";

        teleopButton.image.color =
            TeleopEnabled ? Color.green : Color.red;
    }
}
