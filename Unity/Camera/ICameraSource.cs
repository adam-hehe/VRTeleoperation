using UnityEngine;

public interface ICameraSource
{
    void Initialize();
    Texture GetTexture();
    void Shutdown();
}