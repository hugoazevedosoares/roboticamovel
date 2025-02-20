#!/usr/bin/env python
# pylint: disable=C0321, C0103, C0111, E1101, W0621, I0011
# encoding: UTF-8

import math
import numpy as np
import rospy
import tf
from std_msgs.msg import Float64
from nav_msgs.msg import Odometry

# variáveis globais


class Odometer():

    def __init__(self):
        self.rate = rospy.get_param("~RATE", 3)
        self.__sample_time = 1 / self.rate
        self.__wheel_radius = rospy.get_param("~RAIO_DAS_RODAS", 3.3)
        self.__wheels_dist = rospy.get_param("~DIST_ENTRE_RODAS", 14.6)
        self.linear_desloc = 0
        self.right_wheel_speed = 0
        self.left_wheel_speed = 0
        self.current_angle = 0
        self.current_position = []

    def right_encoder_callback(msg):
        self.right_wheel_speed = msg.data

    def left_encoder_callback(msg):
        self.left_wheel_speed = msg.data

    def get_current_angle():
        return self.current_angle

    def get_current_position():
        return self.current_position

    # w = (right_wheel_speed + left_wheel_speed) * wheel_radius /
    # wheels_distance
    def get_angular_speed():
        return (self.right_wheel_speed + self.left_wheel_speed) * self.__wheel_radius / self.__wheels_dist

    # v = (right_wheel_speed + left_wheel_speed) * wheel_radius / 2
    def get_linear_speed():
        return (self.right_wheel_speed + self.left_wheel_speed) * self.__wheel_radius / 2.0

    def angular_integration(old_angular_speed):
        self.current_angle = (self.get_angular_speed()
                              + old_angular_speed) * self.__sample_time / 2.0

        return self.current_angle

    def linear_speed_integration(old_x_speed, old_y_speed):
        x_speed = self.get_linear_speed() * math.cos(self.current_angle)
        y_speed = self.get_linear_speed() * math.sin(self.current_angle)

        x_position = (x_speed + old_x_speed) * self.__sample_time / 2.0
        y_position = (y_speed + old_y_speed) * self.__sample_time / 2.0

        self.current_position = [x_position, y_position]

        return self.current_position


if __name__ == '__main__':
    try:
        rospy.init_node('odometry_node')
        odometer = Odometer()

        publisher = rospy.Publisher('odometry_topic', Odometry, queue_size=1)

        rospy.Subscriber('left_wheel_speed', Float64,
                         odometer.right_encoder_callback)

        rospy.Subscriber('right_wheel_speed', Float64,
                         odometer.left_encoder_callback)

        rate = rospy.Rate(odometer.rate)

        speed = odometer.get_linear_speed()
        angle = odometer.get_current_angle()
        angular_speed = odometer.get_angular_speed()
        current_position = odometer.get_current_position()

        x_speed = speed * math.cos(angle)
        y_speed = speed * math.sin(angle)

        while not rospy.is_shutdown():

            rate.sleep()

            odom = Odometry()
            odom.header.stamp = rospy.Time.now()
            odom.header.frame_id = "odom"

            odom_quat = tf.transformations.quaternion_from_euler(0, 0, angle)

            # set the position
            odom.pose.pose = Pose(
                Point(current_position[0], current_position[1], 0.), Quaternion(*odom_quat))

            # set the velocity
            odom.child_frame_id = "base_link"
            odom.twist.twist = Twist(
                Vector3(x_speed, y_speed, 0), Vector3(0, 0, angular_speed))

            speed = odometer.get_linear_speed()
            angle = odometer.get_current_angle()
            angular_speed = odometer.get_angular_speed()
            current_position = odometer.get_current_position()
            x_speed = speed * math.cos(angle)
            y_speed = speed * math.sin(angle)

            publisher.publish(odom)

            rate.sleep()

    except rospy.ROSInterruptException()
        pass
