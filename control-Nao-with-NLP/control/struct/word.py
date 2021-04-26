# -*- coding:utf-8 -*-
# Author: HuXiaoming
# Date: 2021-4-12
# =================================== #

from control.struct.chunk_ import ChunkType
import sys


class Word:
    # Word类用于存储词语的信息
    # Word类仿写自CoNLLWord类
    # CoNLLWord类详见：https://github.com/hankcs/HanLP/blob/6b60684f447d4c9f4ad68016fd1b443ef50e9bb4/src/main/java/com/hankcs/hanlp/corpus/dependency/CoNll/CoNLLWord.java#L17
    def __init__(self, CoNNLLWord, isCoreWord = False) -> None:
        # 当前词在句子中的序号，从１开始
        self.ID = CoNNLLWord.ID
        # 当前词语（或标点）的原型或词干，在中文中，此列与FORM相同
        self.LEMMA = CoNNLLWord.LEMMA
        # 当前词语的词性（粗粒度）
        self.CPOSTAG = CoNNLLWord.CPOSTAG
        # 当前词语的词性（细粒度）
        self.POSTAG = CoNNLLWord.POSTAG

        # HEAD 需要保证为Word类的对象
        # 当前词语的中心词
        # if CoNNLLWord.HEAD != None:
        #     self.HEAD = Word(CoNNLLWord.HEAD)
        self.HEAD_ID = CoNNLLWord.HEAD.ID
        self.HEAD = None

        # 当前词语与中心词的依存关系
        self.DEPREL = CoNNLLWord.DEPREL
        # 等效字符串
        self.NAME = CoNNLLWord.NAME

        # 是否为核心词
        self.isCoreWord = isCoreWord

        # 从属词数目
        self.dependentWordsNumber = 0
        # 从属词表
        self.dependentWords = []

        # 语块类型
        self.chunkType = None

    def __str__(self):
        return "{}".format(self.__class__.__name__)

    def setHEAD(self, HEAD):
        self.HEAD = HEAD

    def setCoreWordIsTrue(self):
        self.isCoreWord = True

    def setDependentWords(self, words: list, number: int):
        self.dependentWords = words
        self.dependentWordsNumber = number

    def addDependentWords(self, word):
        self.dependentWords.append(word)
        self.dependentWordsNumber += 1

    def traversal_child_node(self):
        print(self.LEMMA)
        if self.dependentWordsNumber > 0:
            for dependentWord in self.dependentWords:
                dependentWord.traversal_child_node()

    def traversal_child_node_(self):
        self.setChunkType()
        if self.dependentWordsNumber > 0:
            for dependentWord in self.dependentWords:
                dependentWord.traversal_child_node_()

    def setChunkType(self):
        if self.DEPREL == "主谓关系":
            if self.HEAD.isCoreWord:
                self.chunkType = ChunkType.motionSubject
        elif self.DEPREL == "动宾关系":
            if self.HEAD.chunkType == ChunkType.motionControl:
                if self.POSTAG == 'n':
                    self.chunkType = ChunkType.movingTarget
                elif self.POSTAG == 'v':
                    # 例如：请（核心关系）前进（动宾关系）
                    self.chunkType = ChunkType.motionControl
                elif self.POSTAG == 'q':
                    self.chunkType = ChunkType.movingTarget

        elif self.DEPREL == "间宾关系":
            pass
        elif self.DEPREL == "前置宾语":
            pass
        elif self.DEPREL == "兼语":
            pass
        elif self.DEPREL == "定中关系":
            if self.HEAD.chunkType == ChunkType.movingTarget:
                self.chunkType = ChunkType.movingTarget
        elif self.DEPREL == "状中结构":
            pass
        elif self.DEPREL == "动补结构":
            if self.HEAD.chunkType == ChunkType.motionControl:
                if self.POSTAG == 'v':
                    self.chunkType = ChunkType.motionControl
        elif self.DEPREL == "并列关系":
            if self.isCoreWord:
                if self.POSTAG in ["v", "vf"]:
                    self.chunkType = ChunkType.motionControl
            else:
                # 如果不是准核心关系词，则语块类型等于其父的类型
                self.chunkType = self.HEAD.chunkType

        elif self.DEPREL == "介宾关系":
            if self.HEAD.chunkType == ChunkType.motionControl:
                if self.POSTAG in ['n', 'f']:
                    self.chunkType = ChunkType.movingTarget

        elif self.DEPREL == "左附加关系":
            pass
        elif self.DEPREL == "右附加关系":
            pass
        elif self.DEPREL == "独立结构":
            pass
        elif self.DEPREL == "标点符号":
            pass
        elif self.DEPREL == "核心关系":
            if self.POSTAG in ['v', 'vf', 'vn']:
                self.chunkType = ChunkType.motionControl
        else:
            print("！警告：超出预定义依存句法关系范围，即将终止程序...")
            sys.exit(1)

    def printWordInfo(self, **kwargs):
        briefList = [str(x) for x in [self.ID, self.LEMMA, self.POSTAG, self.HEAD_ID, self.DEPREL]]
        spaceList = [6] * 5
        if kwargs["addr"]:
            briefList[0] +=  ':' + str(self) + ':' + str(id(self))
            spaceList[0] = 28
            briefList[3] +=  ':' + str(self.HEAD) + ':' + str(id(self.HEAD))
            spaceList[3] = 28
        for i in range(len(briefList)):
            print("{}".format(briefList[i]).ljust(spaceList[i]), end='')

        try:
            if kwargs["relationship"]:
                print("{}".format(self.dependentWordsNumber).ljust(5), end='')
                print("[", end=' ')
                for dependentWord in self.dependentWords:
                    print('{}'.format(dependentWord.LEMMA), end=' ')
                print("]", end='')
            if kwargs["chunkInfo"]:
                print("\t\t{}".format(self.chunkType), end='')
        except KeyError:
            pass
        else:
            print('')



# 句子树
class Sentence(Word):
    # 将Sentence句子树可以作为一个根结点
    # 用于存储“核心关系”的支配词或者“准核心关系”的支配词
    # 准核心关系词: 与“核心关系”的支配词有“并列关系”的词
    def __init__(self, CoNNLLWord, isCoreWord, sentenceID) -> None:
        super().__init__(CoNNLLWord, isCoreWord)

        # 若指令由多个句子组成（有多个谓语或者有与“核心关系”的支配词成“并列关系”的）
        # 需要标明句子号
        # 从1开始计数
        # ？会不会出现属于1号句子的词与2号句子有关系(除了与“核心关系”的支配词有关的“准核心关系”的支配词)...
        self.sentenceID = sentenceID

    def traversal(self):
        print(self.LEMMA)
        if self.dependentWordsNumber > 0:
            for dependentWord in self.dependentWords:
                dependentWord.traversal_child_node()

    def traversal_(self):
        self.setChunkType()
        if self.dependentWordsNumber > 0:
            for dependentWord in self.dependentWords:
                dependentWord.traversal_child_node_()
