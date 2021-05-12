# -*- coding:utf-8 -*-
# Author: HuXiaoMing
# Date: 2021-4-22
# 动作和动作序列

from control.struct.chunk_ import ChunkType, MovingTarget

ACTIONS = {
    "move": ["走", "去", "到", "直走", "前进", "直行", "移动"],
    "turnLeft": ["左转", "向左转"],
    "turnRight": ["右转", "向右转"],
    "wave": ["举手", "招手", "挥手"],
    "back": ["后退", "向后退"],
    "turnBack": ["向后转"]
}


class Action:

    def __init__(self, sentence):
        self.motionSubject = "机器人"
        self.motionControl = ""
        self.movingTarget = None
        self.__generate(sentence)

    # 通过搜索ACTIONS返回action对应的动作
    def __localInACTIONS(self, action) -> str:
        for actionFunc, actions in ACTIONS.items():
            if action in actions:
                return actionFunc

    def __traversal_child_node(self, word):
        if word.chunkType == ChunkType.movingTarget:
            self.movingTarget = MovingTarget(word)
        if word.chunkType == ChunkType.motionSubject:
            self.motionSubject = word.LEMMA
        if word.chunkType == ChunkType.motionControl:
            self.motionControl = self.motionControl if self.__localInACTIONS(word.LEMMA) is None else self.__localInACTIONS(word.LEMMA)
            for dependentWord in word.dependentWords:
                self.__traversal_child_node(dependentWord)

    # 动作生成
    def __generate(self, sentence):
        if sentence.chunkType == ChunkType.motionControl:
            self.motionControl = self.__localInACTIONS(sentence.LEMMA)
        for dependentWord in sentence.dependentWords:
            self.__traversal_child_node(dependentWord)



class ActionSequence:

    def __init__(self, action_number):
        self.actionSequence = []
        self.actionNumber = action_number

    def addAction(self, action: Action):
        self.actionSequence.append(action)