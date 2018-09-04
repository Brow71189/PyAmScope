#   pyAndor - A Python wrapper for Andor's scientific cameras
#   Copyright (C) 2009  Hamid Ohadi
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import platform
from ctypes import WinDLL, cdll, c_int, c_float, c_uint, c_void_p, byref, POINTER, CFUNCTYPE, create_string_buffer, Structure
from PIL import Image
import sys
import time
import numpy as np
import logging
import os
import queue
from pathlib import Path

class Buffer(queue.Queue):
    def __init__(self, maxsize=0):
        super().__init__(maxsize=maxsize)

    def get(self, block=True, timeout=None):
        obj = super().get(block=block, timeout=timeout)
        self.task_done()
        return obj

    def put(self, obj, block=True, timeout=None):
        if self.full():
            self.get()
        super().put(obj, block=block, timeout=None)

class Toupcam:
    def __init__(self, buffer=None):
        # Check operating system and load library
        # for Windows
        self.driver_path = os.path.join(str(Path.home()), 'PyAmScope')
        if platform.system() == "Windows":
            self.is_windows = True
            self.dll = WinDLL(os.path.join(self.driver_path, 'toupcam.dll'))

        # for Linux
        elif platform.system() == "Linux":
            self.is_windows = False
            self.dll = cdll.LoadLibrary(os.path.join(self.driver_path, 'libtoupcam.so'))
            #self.dll = DummyDLL(self)
        else:
            logging.error("Cannot detect operating system, wil now stop")
            raise

        self.verbosity   = False
        #self.dll.Initialize.argtypes = [c_char_p]
        #self.dll.Initialize.restype = c_uint32
        self.buffer = buffer or Buffer(maxsize=10)
        self.cam = None
        #assert error == 'DRV_SUCCESS', str(error)
#        if error != 'DRV_SUCCESS':
#            raise RuntimeError(error)
        self.Toupcam_Open()
        
    def Toupcam_Open(self):
        class myPythonAPI(Structure):
            pass

        PmyPythonAPI = POINTER(myPythonAPI)

        self.dll.Toupcam_Open.restype = PmyPythonAPI
        
        self.cam = self.dll.Toupcam_Open(None)
        if not self.cam:
            logging.warn('Unable to open connection to camera.')
        
    def Toupcam_Close(self):
        if self.cam:
            self.dll.Toupcam_Close(self.cam)
            self.cam = None
    
    def Toupcam_StartPullModeWithCallback(self, callback_function):
        if self.cam:
            self.Toupcam_get_Size()
            prototype = CFUNCTYPE(None, c_uint)
            self.callback_ref = prototype(callback_function)
            self.string_buffer = create_string_buffer(10000)
            res = self.dll.Toupcam_StartPullModeWithCallback(self.cam,
                                                             self.callback_ref,
                                                             self.string_buffer)
    
    def Toupcam_PullImage(self):
        if self.cam:
            # get image heigth and width
            width = c_uint()
            height = c_uint()
#            res = self.dll.Toupcam_PullImage(self.cam,
#                                             None,
#                                             c_int(24),
#                                             c_int(0),
#                                             byref(width),
#                                             byref(height))
#            print('width, height:', width.value, height.value)
            dim = int(self.width * self.height * 3)
            rawimageArray = np.empty(dim, dtype=np.uint8)
            cimage = rawimageArray.ctypes.data_as(POINTER(c_uint))
            res = self.dll.Toupcam_PullImage(self.cam,
                                             cimage,
                                             c_int(24),
                                             c_int(0),
                                             byref(width),
                                             byref(height))
            rawimageArray = rawimageArray.reshape((self.height, self.width, 3))
            #rawimageArray = np.moveaxis(rawimageArray, 1, -1)
            self.buffer.put(rawimageArray)
            
    def Toupcam_Stop(self):
        if self.cam:
            res = self.dll.Toupcam_Stop(self.cam)
            
    def Toupcam_get_Size(self):
        if self.cam:
            width = c_int()
            height = c_int()
            
            self.dll.Toupcam_get_Size(self.cam, byref(width), byref(height))
            self.width = width.value
            self.height = height.value
            
    def callback_function(self, eventID):
        if eventID == TOUPCAM_EVENT_IMAGE:
            self.Toupcam_PullImage()
            
    def start_live(self):
        self.Toupcam_StartPullModeWithCallback(self.callback_function)
    
    def stop_live(self):
        self.Toupcam_Stop()
    
TOUPCAM_EVENT_EXPOSURE = 0x0001    #/* exposure time changed */
TOUPCAM_EVENT_TEMPTINT = 0x0002    #/* white balance changed, Temp/Tint mode */
TOUPCAM_EVENT_CHROME = 0x0003    #/* reversed, do not use it */
TOUPCAM_EVENT_IMAGE = 0x0004    #/* live image arrived, use Toupcam_PullImage to get this image */
TOUPCAM_EVENT_STILLIMAGE = 0x0005    #/* snap (still) frame arrived, use Toupcam_PullStillImage to get this frame */
TOUPCAM_EVENT_WBGAIN = 0x0006    #/* white balance changed, RGB Gain mode */
TOUPCAM_EVENT_ERROR = 0x0080    #/* generic error */
TOUPCAM_EVENT_DISCONNECTED = 0x0081    #/* camera disconnected */
TOUPCAM_EVENT_TIMEOUT = 0x0082    #/* timeout error */