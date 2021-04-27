# -*- coding:utf-8 -*-
# Author: HuXiaoMing
# Date: 2021-4-12
# 对自然语言命令进行分析

import os
from pyhanlp import *
from control.struct.word import Word, Sentence
from control.struct.action import ActionSequence, Action


class InstructionAnalyzer:
    # 指令分析基类
    # 所有的指令分析类都继承自此类
    def __init__(self, instruction: str = "") -> None:
        self.instruction = instruction

    # 用于传入自然语言指令
    def setInstruction(self, instruction: str) -> None:
        self.instruction = instruction


    # 用于获取自然语言指令
    def getInstruction(self) -> str:
        return self.instruction


# 分词和标注器
class SegmentationAndTagging(InstructionAnalyzer):

    def __init__(self, instruction: str = "") -> None:
        super().__init__(instruction)

        self.resultWordsListForSegmentAndTagging = []
        self.resultsOfWordSegmentationAndPosTagging = []

    def analysis(self):
        pass

    def __setResultsOfWordSegmentationAndPosTagging(self, result_hanlp):
        self.resultsOfWordSegmentationAndPosTagging.clear()
        for wordAndTag in result_hanlp:
            word = str(wordAndTag).split('/')[0]
            tag = str(wordAndTag).split('/')[1]
            self.resultsOfWordSegmentationAndPosTagging.append((word, tag))

    # 对当前指令进行分词和词性标注
    def posTagging(self):
        """"""
        """
        self.instruction <= "向左转"
        result = HanLP.segment(self.instruction)
        result:
            格式:ArrayList: [向/p, 左转/nz]
        """
        self.__setResultsOfWordSegmentationAndPosTagging(HanLP.segment(self.instruction))

    # CRF词法分析器
    def posTaggingCRF(self):
        # 基于CRF词法分析器对当前指令进行分词和词性标注
        CRFLexicalAnalyzer = JClass("com.hankcs.hanlp.model.crf.CRFLexicalAnalyzer")
        analyzer = CRFLexicalAnalyzer()
        """
        self.instruction <= "向左转"
        resultSentenece = analyzer.analyze(self.instruction)
        resultSentenece： 
            格式：Sentenece:向/p 左转/nr
            .wordList：
                格式：ArrayList:[向/p, 左转/nr]
                其中每项的格式为word，没有提供.word和.nature来分割，需要手动分割。
        """
        self.__setResultsOfWordSegmentationAndPosTagging(analyzer.analyze(self.instruction).wordList)
        self.displayByColumn()

    # 按列展示
    def displayByColumn(self):
        print("-----------------------------")
        for wordAndTag in self.resultsOfWordSegmentationAndPosTagging:
            print("{:\u3000<10} {:>10}".format(wordAndTag[0], wordAndTag[1]))


# 依存句法分析器
class DependencyParser(InstructionAnalyzer):

    def __init__(self, instruction: str = ""):
        super().__init__(instruction=instruction)

        self.sentenceTrees = []

    # 调用HanLP提供的依存句法分析方法
    def dependencyParser(self):
        """"""
        """
        analysisResult = HanLP.parseDependency():
        analysisResult:
            类型: CoNLLSentence
            详见: https://github.com/hankcs/HanLP/blob/6b60684f447d4c9f4ad68016fd1b443ef50e9bb4/src/main/java/com/hankcs/hanlp/corpus/dependency/CoNll/CoNLLSentence.java#L22
            analysisResult.word:
                类型: CoNLLWord[]; 该数组里面存有很多行，每一个分词的信息占用其中一行。
                详见: https://github.com/hankcs/HanLP/blob/6b60684f447d4c9f4ad68016fd1b443ef50e9bb4/src/main/java/com/hankcs/hanlp/corpus/dependency/CoNll/CoNLLWord.java#L17
                备注: 本工程Word类便是仿写CoNLLword类
        """
        return HanLP.parseDependency(self.instruction).word

    # 建立支配词与从属词之间的关系
    def establishTheRelationshipBetweenDominantWordAndDependenceWord(self, words) -> list:
        # ================================================================================== #
        # ====================   建立支配词与被支配词关系    =================================== #
        # 这个地方需简化，可不可以让word类用JClass继承CoNNLLWord类
        # 1. 传入每个词汇的支配词
        for word in words:
            # 非核心支配词
            if word.HEAD_ID != 0:
                word.setHEAD(words[word.HEAD_ID - 1])
        # 2. 传入每个词汇的从属词
        for word in words:
            if not word.isCoreWord:
                # 剔除标点符号
                if word.POSTAG != 'w':
                    words[word.HEAD.ID - 1].addDependentWords(word)
        # ================================================================================== #
        return words

    # word是否为准核心词
    def __isQuasiCoreWord(self, word):
        # 目前定义的准核心关系词为：
        # （1）与核心词有并列关系的单词；
        # （2）虽然与核心词之间相隔其他的词（一个或多个），但这些词之间始终是并列关系。
        if word.DEPREL != "并列关系":
            return False
        else:
            if word.HEAD.DEPREL == "核心关系":
                return True
            else:
                return self.__isQuasiCoreWord(word.HEAD)

    # 构建句子树
    def createSentenceTree(self):
        # 以”核心关系“词或“准核心关系”词为根，创建句子树。
        words = []
        sentence_index = 1
        # 清空句子树，不然会记录上一次的指令
        self.sentenceTrees = []
        for word in self.dependencyParser():
            if word.HEAD.ID == 0 or self.__isQuasiCoreWord(word) :
                coreWord = Sentence(CoNNLLWord=word, isCoreWord=True, sentenceID=sentence_index)
                words.append(coreWord)
                self.sentenceTrees.append(coreWord)
                sentence_index += 1
            else:
                words.append(Word(word))

        words = self.establishTheRelationshipBetweenDominantWordAndDependenceWord(words)

        for coreWord in self.sentenceTrees:
            coreWord.traversal_()

        for item in words:
            # print(item, end=': ')
            # item.printWordInfo()
            item.printWordInfo(relationship=True, chunkInfo=True , addr=False)


        # for coreWord in self.sentenceTrees:
        #     coreWord.traversal()

    # 生成动作序列
    def generateActionSequence(self):
        actionSequence = ActionSequence(action_number=len(self.sentenceTrees))
        for coreWord in self.sentenceTrees:
            actionSequence.addAction(Action(coreWord))

        return actionSequence


def test1():
    d = SegmentationAndTagging()
    d.setInstruction("机器人前进")
    d.posTaggingCRF()


def test2():
    d = DependencyParser()

    with open('../data/instruction.txt', 'r', encoding='utf-8') as fread:
        instructions = fread.readlines()
        for instruction in instructions:
            d.setInstruction(instruction.strip())
            d.createSentenceTree()
            print("=================================================================================================")


def test3():
    d = DependencyParser()
    # d.setInstruction("机器人前进到桌子的前面，然后左转，然后直走，然后右转，然后直行，然后左转，然后直走，然后右转，然后直行")
    # d.setInstruction("机器人前进到桌子的前面，然后左转，然后直走")
    d.setInstruction("机器人前进到桌子旁，然后左转90度，然后向前走2米")
    # d.setInstruction("机器人前进到桌子旁，然后左转90度，然后向前走2米")
    d.createSentenceTree()
    d.generateActionSequence()


if __name__ == "__main__":
    test2()
    # test1()
    # test3()
