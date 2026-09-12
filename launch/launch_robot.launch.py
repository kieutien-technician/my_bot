import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.actions import RegisterEventHandler
from launch.actions import TimerAction
from launch.event_handlers import OnProcessStart
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    package_name = 'my_bot'

    # Robot State Publisher
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory(package_name),
                'launch',
                'rsp.launch.py'
            )
        ),
        launch_arguments={
            'use_sim_time': 'false',
            'use_ros2_control': 'true'
        }.items()
    )

    # Xacro file
    xacro_file = os.path.join(
        get_package_share_directory(package_name),
        'description',
        'robot.urdf.xacro'
    )

    # Robot description
    robot_description = ParameterValue(
        Command([
            'xacro ',
            xacro_file,
            ' use_ros2_control:=true'
        ]),
        value_type=str
    )

    # Controller configuration
    controller_params_file = os.path.join(
        get_package_share_directory(package_name),
        'config',
        'my_controllers.yaml'
    )

    # Controller Manager
    controller_manager_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            {
                'robot_description': robot_description
            },
            controller_params_file
        ],
        output='screen'
    )

    # Start controller manager after 3 seconds
    delayed_controller_manager = TimerAction(
        period=3.0,
        actions=[controller_manager_node]
    )

    # Diff drive controller spawner
    diff_drive_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_cont'],
        output='screen'
    )

    delayed_diff_drive_spawner = RegisterEventHandler(
        OnProcessStart(
            target_action=controller_manager_node,
            on_start=[diff_drive_spawner]
        )
    )

    # Joint state broadcaster spawner
    joint_broad_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_broad'],
        output='screen'
    )

    delayed_joint_broad_spawner = RegisterEventHandler(
        OnProcessStart(
            target_action=controller_manager_node,
            on_start=[joint_broad_spawner]
        )
    )

    return LaunchDescription([
        rsp,
        delayed_controller_manager,
        delayed_diff_drive_spawner,
        delayed_joint_broad_spawner
    ])