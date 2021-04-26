# -*- coding:utf-8 -*-
# Author: HuXiaoMing
# Date: 2021-4-12

from enum import Enum


# 枚举类
class ChunkType(Enum):

    motionSubject = 1
    movementDirection = 2
    motionControl = 3
    movingTarget = 4


class Chunk:

    def __init__(self, chunkType):
        # 4种类别的一种
        self.chunkType = chunkType


class MovingTarget(Chunk):
    # 运动目标语块
    def __init__(self, word):
        super().__init__(chunkType=ChunkType.movingTarget)
        # 实体，如桌子
        self.target = word
        self.entity = None
        # 方位，如前面、左边
        self.position = None
        # 数词，如米
        self.measureWord = None
        # 量词，如1、2
        self.numeral = None
        self.__generate(word)

    def __generate(self, word):
        if word.POSTAG == 'f':
            self.position = word.LEMMA
        if word.POSTAG == 'n':
            self.entity = word.LEMMA
        if word.POSTAG == 'q':
            self.measureWord = word.LEMMA
        if word.POSTAG == 'm':
            self.numeral = word.LEMMA
        for item in word.dependentWords:
            self.__generate(item)





class Sentence:
    pass
