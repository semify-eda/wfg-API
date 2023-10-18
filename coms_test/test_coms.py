"""
Initial test script of the SmartWave debugging API

Engineer: Adam Horvath
"""
import os
import pandas as pd
import numpy as np
import pytest
import logging
import time

from Arduino import Arduino


class TestRegComs:
    """
    Base Class for testing register access
    """

    def test_arduino_coms(self):
        """
        This method is only intended to test the communications with an Arduino, by toggling its LED
        :return: none
        """
        logger = logging.getLogger('test_arduino_coms')
        logger.info("Setup communication to Arduino MKR Vidor 4000")
        board = Arduino('9600', port="COM12")
        logger.info("Connection was successful")
        board.pinMode(9, "OUTPUT")

        for _ in range(10):
            logger.info("LED TOGGLE")
            board.digitalWrite(9, "LOW")
            time.sleep(1)
            board.digitalWrite(9, "HIGH")
            time.sleep(1)

        logger.info("Arduino coms test finished")


