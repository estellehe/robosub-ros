#!/usr/bin/env python

import serial
import serial.tools.list_ports as list_ports
import rospy
import tf.transformations as transform

from std_msgs.msg import String
from underwater_sensor_msgs.msg import DVL
from data_pub.msg import DVLRaw

class DvlRawPublisher:

    FTDI_STR = 'FT232R'
    BAUDRATE = 9600
    TOPIC_NAME = 'dvl_raw'
    NODE_NAME = 'dvl_raw_publisher'
    LINE_DELIM = ','

    def __init__(self):
        self._pub = rospy.Publisher(self.TOPIC_NAME, DVLRaw, queue_size=10)
        
        self._current_msg = DVLRaw()

        self._serial_port = None
        self._serial = None

        self._dvl_line_parsers = {
            'SA': self._parse_SA,
            'TS': self._parse_TS,
            'BI': self._parse_BI,
            'BS': self._parse_BS,
            'BE': self._parse_BE,
            'BD': self._parse_BD
        }


    def run(self):
        rospy.init_node(self.NODE_NAME)

        self._serial_port = next(list_ports.grep(self.FTDI_STR)).device
        self._serial = serial.Serial(self._serial_port, self.BAUDRATE, 
                timeout=0.1, write_timeout=1.0,
                bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE)

        while not rospy.is_shutdown():
            line = self._serial.readline()
            if line.strip() and line[0] == ':':
                self._parse_line(line)

    def _parse_line(self, line):
        data_type = line[1:3]
        self._dvl_line_parsers[data_type](self._clean_line(line))

    def _clean_line(self, line):
        return line[4:].replace('\r\n', '')

    def _parse_SA(self, line):
        fields = self._extract_floats(line, 0, None)
        quat = transform.quaternion_from_euler(fields[1], 
                fields[0], 
                fields[2])
        self._current_msg.orientation.x = quat[0]
        self._current_msg.orientation.y = quat[1]
        self._current_msg.orientation.z = quat[2]
        self._current_msg.orientation.w = quat[3]

    def _parse_TS(self, line):
        fields = self._extract_floats(line, 1, None)
        self._current_msg.dvl.salinity = fields[0]
        self._current_msg.dvl.temperature = fields[1]
        self._current_msg.dvl.depth = fields[2]
        self._current_msg.dvl.sound_speed = fields[3]
        self._current_msg.dvl.test = int(fields[4])

    def _parse_BI(self, line):
        fields = self._extract_floats(line, 0, 4)
        self._current_msg.dvl.bi_x_axis = fields[0]
        self._current_msg.dvl.bi_y_axis = fields[1]
        self._current_msg.dvl.bi_z_axis = fields[2]
        self._current_msg.dvl.bi_error = fields[3]
        self._current_msg.dvl.bi_status = line.split(self.LINE_DELIM)[4]
        self._publish_current_msg()

    def _parse_BS(self, line):
        pass

    def _parse_BE(self, line):
        pass

    def _parse_BD(self, line):
        pass

    def _extract_floats(self, num_string, start, stop):
        return [float(num) 
            for num 
            in num_string.split(self.LINE_DELIM)[start:stop]]
    
    def _publish_current_msg(self):
        """Publish the current DVL message and set the message to empty
        """
        self._pub.publish(self._current_msg)
        self._current_msg = DVLRaw()



if __name__ == '__main__':
    try:
    	DvlRawPublisher().run()
    except rospy.ROSInterruptException:
    	pass
