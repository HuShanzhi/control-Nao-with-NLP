# -*- coding:utf-8 -*-
# Author: HuXiaoMing
# Date: 2021-5-2
# 相对方向枚举类

from enum import Enum


class RelativeDirection(Enum):

    front = 1
    back = 2
    left = 3
    right = 4
    nearby = 5