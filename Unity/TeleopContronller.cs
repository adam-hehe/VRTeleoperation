/*
Create the UI in world space
	•	In the Hierarchy: Right-click → UI → Canvas
	•	Select the Canvas and in the Inspector set Render Mode = World Space
	•	Move the Canvas onto your desk and scale it down (world-space UI is huge by default; something like 0.001 / 0.001 / 0.001 is a common starting point)
	•	Ensure the Canvas has Graphic Raycaster (usually added automatically)
Add the button
	•	Right-click the Canvas → UI → Button
	•	Rename it (e.g., TeleopButton)
	•	Resize/position it on the desk
	•	Set the button label text to something initial like ON
Make sure XR can click UI
	•	Confirm there is an EventSystem in the scene (Hierarchy search “EventSystem”)
	•	On the EventSystem:
	•	Remove Standalone Input Module (if present)
	•	Add/ensure XR UI Input Module (this is what makes Button.onClick work in VR)
Make sure you have an XR interactor to actually press it
	•	If you’re using a laser pointer style interaction: ensure your hand/controller has an XR Ray Interactor
	•	If you want to physically “touch” the button: ensure your hand has an XR Poke Interactor
	•	(Either method is fine—just make sure at least one is present and active in your XR rig setup)
Add the Teleop manager script
	•	Create an empty GameObject in the scene: Right-click → Create Empty
	•	Rename it TeleopManager
	•	Attach your TeleopController.cs script to it
Wire up references in the Inspector
	•	Select TeleopManager
	•	Drag the Button object into the script’s teleopButton field
	•	Drag the button’s Text object into buttonText
	•	If you’re using TextMeshPro, you’ll either need to switch the script to TMP types or use the legacy Text component
Gate ROS publishing
	•	In your ROS publishing script (where you call ros.Publish(...)), wrap the publish call:
	•	Only publish when TeleopController.TeleopEnabled is true
Test
	•	Enter Play Mode, run in VR, and click the desk button
	•	Verify the button text changes ON/OFF
	•	Verify robot motion stops immediately when OFF (because publishing stops)
*/

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