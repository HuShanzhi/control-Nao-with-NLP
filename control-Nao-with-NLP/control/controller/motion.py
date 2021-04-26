# -*- coding:utf-8 -*-
# Author: HuXiaoMing
# Date: 2021-4-22
# 加载motion文件

from controller import Motion

# motions_parent_path = "E:/Webots/projects/robots/softbank/nao/motions/" # motions文件的父路径
motions_parent_path = "../data/nao/motions/"

class Motion_:
    def __init__(self, motion, time: int=3):
        self.action = motion
        self.time = time
        try:
            self.motion = Motion(motions_parent_path + motion + '.motion')
        except:
            print("motion加载失败")
            self.motion = Motion(motions_parent_path + 'HandWave.motion')
