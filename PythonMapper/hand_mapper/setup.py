import os
from glob import glob
from setuptools import setup

package_name = 'hand_mapper'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='adam',
    maintainer_email='adconnor@ucsd.edu',
    description='VR teleoperation hand mapper and camera publisher',
    license='MIT',
    entry_points={
        'console_scripts': [
            'finger_angles      = hand_mapper.finger_angles:main',
            'camera_publisher   = hand_mapper.camera_publisher:main',
            'ah_hardware_driver = hand_mapper.ah_hardware_driver:main',
        ],
    },
)
