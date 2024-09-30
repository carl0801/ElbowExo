from setuptools import setup
from glob import glob

package_name = 'emg_launch'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (f'share/{package_name}/launch', glob('emg_launch/launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@example.com',
    description='Launch files for EMG listener and sensor',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [],
    },
)