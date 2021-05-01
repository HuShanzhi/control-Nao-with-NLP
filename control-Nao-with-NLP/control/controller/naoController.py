# -*- coding:utf-8 -*-
# Author: HuXiaoMing
# Date: 2021-4-22
# 仿写Webots提供的demo

from controller import Robot
from control.controller.motion import Motion_
from control.analyzer.instructionAnalyzer import DependencyParser
from control.controller.entity import getEntityObject
from queue import Queue
from threading import Thread, Lock
import time

# OBJECT_TABLE = {
# "桌子": (-1.6, -2.06),
# "落地灯": (-4, -3.9)
# }

# 机器人的朝向共4种
# 0：左； 1：下； 2：右； 3：上
DIRECTION = 0
# 机器人运动精确度
ACCURACY = 0.055

# ========================================================================= #
# ========================================================================= #
# 两个互斥信号量和一个同步信号量
# ========================================================================= #
# mutex1用于大动作及输入之间的huc
# mutex2用于带目标的大动作创建的小动作之间的互斥
mutex1 = Lock()
mutex2 = Lock()
# ========================================================================= #
# synchro用于动作与NAO坐标获取之间的同步
synchro = Lock()
# ========================================================================= #
# ========================================================================= #

# ========================================================================= #
# ====================  为什么引入类ControllerThread  ======================== #
# 由于webots中主控制器的并发问题，
# 在给定动作序列[walk, turnLeft, walk]下，
# 程序将会并发执行这三个动作（这点在动作序列[handWave, walk]更加明显，NAO会边走边挥手，但由于动作优化问题可能会倒），
# 但由于这三个动作都是需要控制腿部关节，因此，最终执行的是第三个动作walk。
# 最终，本工程采用多线程和线程锁来解决这些问题。
# =============  多线程  =============== #
# 见博客：https://hu-xiaoming.github.io/2021/04/09/%E5%A4%9A%E7%BA%BF%E7%A8%8B/
# ========================================================================= #
class ControllerThread(Thread):

    def __init__(self, name, mutex, func, motion, target=None):
        super().__init__()
        self.action = motion.action
        self.motion = motion.motion
        self.time = motion.time
        self.func = func
        self.mutex = mutex
        self.target = target
        print("{}线程创建了".format(name))

    def run(self):
        self.mutex.acquire()
        print("======  " + self.action + "开始执行" + "  ======")
        if self.target is None :
            self.func(self.motion)
        else:
            self.func(self.motion, self.target)
        time.sleep(self.time)
        print("======  " + self.action + "执行结束" + "  ======")
        self.mutex.release()
        if synchro.locked():
            synchro.release()
# ========================================================================= #
# ========================================================================= #
class InputThread(Thread):

    def __init__(self, mutex, func):
        super().__init__()
        self.mutex = mutex
        self.func = func
        print("输入线程创建了")

    def run(self) -> None:
        self.mutex.acquire()
        self.func()
        self.mutex.release()



class Nao(Robot):
    PHALANX_MAX = 8

    def __init__(self):
        Robot.__init__(self)
        self.currentlyPlaying = False

        self.findAndEnableDevices()
        self.setMotion()

        # 创建一个依存句法分析器对象
        self.analyer = DependencyParser()

        # 动作线程队列
        self.actionQueue = Queue(10)

        self.instruction = None

    # 获得Nao当前的坐标(x, y)
    def getNaoGps(self):
        return self.gps.getValues()[2], self.gps.getValues()[0]

    # 获取距离传感器的距离
    def getDistance(self):
        print(self.SonarLeft.getType(), self.SonarRight.getType())
        print(self.SonarLeft.getMaxValue(), self.SonarLeft.getMinValue())
        print("左距离传感器的值为：{}".format(self.SonarLeft.getValue()))
        print("右距离传感器的值为：{}".format(self.SonarRight.getValue()))
        return self.SonarLeft.getValue(), self.SonarRight.getValue()

    # 加载仿真nao上的装置
    def findAndEnableDevices(self):
        # 来自webots官方demo
        # get the time step of the current world.
        self.timeStep = int(self.getBasicTimeStep())

        # camera
        self.cameraTop = self.getDevice("CameraTop")
        self.cameraBottom = self.getDevice("CameraBottom")
        self.cameraTop.enable(4 * self.timeStep)
        self.cameraBottom.enable(4 * self.timeStep)

        # ========================================================== #
        # 距离传感器
        self.SonarLeft = self.getDevice("Sonar/Left")
        self.SonarRight = self.getDevice("Sonar/Right")
        self.SonarLeft.enable(4 * self.timeStep)
        self.SonarRight.enable(4 * self.timeStep)
        # ========================================================== #

        # accelerometer
        self.accelerometer = self.getDevice('accelerometer')
        self.accelerometer.enable(4 * self.timeStep)

        # gyro
        self.gyro = self.getDevice('gyro')
        self.gyro.enable(4 * self.timeStep)

        # gps
        self.gps = self.getDevice('gps')
        self.gps.enable(4 * self.timeStep)

        # inertial unit
        self.inertialUnit = self.getDevice('inertial unit')
        self.inertialUnit.enable(self.timeStep)

        # ultrasound sensors
        self.us = []
        usNames = ['Sonar/Left', 'Sonar/Right']
        for i in range(0, len(usNames)):
            self.us.append(self.getDevice(usNames[i]))
            self.us[i].enable(self.timeStep)

        # foot sensors
        self.fsr = []
        fsrNames = ['LFsr', 'RFsr']
        for i in range(0, len(fsrNames)):
            self.fsr.append(self.getDevice(fsrNames[i]))
            self.fsr[i].enable(self.timeStep)

        # foot bumpers
        self.lfootlbumper = self.getDevice('LFoot/Bumper/Left')
        self.lfootrbumper = self.getDevice('LFoot/Bumper/Right')
        self.rfootlbumper = self.getDevice('RFoot/Bumper/Left')
        self.rfootrbumper = self.getDevice('RFoot/Bumper/Right')
        self.lfootlbumper.enable(self.timeStep)
        self.lfootrbumper.enable(self.timeStep)
        self.rfootlbumper.enable(self.timeStep)
        self.rfootrbumper.enable(self.timeStep)

        # there are 7 controlable LED groups in Webots
        self.leds = []
        self.leds.append(self.getDevice('ChestBoard/Led'))
        self.leds.append(self.getDevice('RFoot/Led'))
        self.leds.append(self.getDevice('LFoot/Led'))
        self.leds.append(self.getDevice('Face/Led/Right'))
        self.leds.append(self.getDevice('Face/Led/Left'))
        self.leds.append(self.getDevice('Ears/Led/Right'))
        self.leds.append(self.getDevice('Ears/Led/Left'))

        # get phalanx motor tags
        # the real Nao has only 2 motors for RHand/LHand
        # but in Webots we must implement RHand/LHand with 2x8 motors
        self.lphalanx = []
        self.rphalanx = []
        self.maxPhalanxMotorPosition = []
        self.minPhalanxMotorPosition = []
        for i in range(0, self.PHALANX_MAX):
            self.lphalanx.append(self.getDevice("LPhalanx%d" % (i + 1)))
            self.rphalanx.append(self.getDevice("RPhalanx%d" % (i + 1)))

            # assume right and left hands have the same motor position bounds
            self.maxPhalanxMotorPosition.append(self.rphalanx[i].getMaxPosition())
            self.minPhalanxMotorPosition.append(self.rphalanx[i].getMinPosition())

        # shoulder pitch motors
        self.RShoulderPitch = self.getDevice("RShoulderPitch")
        self.LShoulderPitch = self.getDevice("LShoulderPitch")

        # keyboard
        self.keyboard = self.getKeyboard()
        self.keyboard.enable(10 * self.timeStep)

    # 加载Motion文件
    def setMotion(self):
        self.move = Motion_('Forwards', 8)
        self.handWave = Motion_('HandWave', 5)
        self.forwards = Motion_('Forwards', 4)
        self.forwards50 = Motion_('Forwards50', 8)
        self.backwards = Motion_('Backwards', 2)
        self.sideStepLeft = Motion_('SideStepLeft', 6)
        self.sideStepRight = Motion_('SideStepRight', 6)
        self.standUpFromFront = Motion_('StandUpFromFront', 2)
        self.turnLeft40 = Motion_('TurnLeft40', 4)
        self.turnLeft60 = Motion_('TurnLeft60', 6)
        self.turnLeft90 = Motion_('TurnLeft90', 9)
        self.turnLeft180 = Motion_('TurnLeft180', 18)
        self.turnRight40 = Motion_('TurnRight40', 4)
        self.turnRight60 = Motion_('TurnRight60', 6)
        self.turnRight90 = Motion_('TurnRight90', 9)

    def startMotion(self, motion):
        global DIRECTION
        # interrupt current motion
        if self.currentlyPlaying:
            self.currentlyPlaying.stop()

        # start new motion
        motion.play()
        self.currentlyPlaying = motion
        # =============== 修改方向 ================= #
        if motion == self.turnRight90.motion:
            DIRECTION = (DIRECTION - 1) % 4
        elif motion == self.turnLeft90.motion:
            DIRECTION = (DIRECTION + 1) % 4
        elif motion == self.turnLeft180.motion:
            DIRECTION = (DIRECTION + 2) % 4
        print("DIRECTION = {}".format(DIRECTION))
        # ========================================= #

    # 通过左右移动进行避障
    def avoidObstacles(self):
        # 获取左右距离传感器的距离
        distanceLeft, distanceRight = self.getDistance()
        while distanceLeft < 0.26 or distanceRight < 0.26:
            # 距离过小，进行避障，开始左右移动

            if distanceLeft > distanceRight:
                t_ = ControllerThread("SideStepLeft", mutex2, self.startMotion, self.sideStepLeft)
                t_.start()
            else:
                t_ = ControllerThread("SideStepRight", mutex2, self.startMotion, self.sideStepRight)
                t_.start()
            time.sleep(8)
            distanceLeft, distanceRight = self.getDistance()

    def _move(self, target, motion=None):
        """
        :param target: 移动目标点的坐标
        :return:
        """
        # 方向
        global DIRECTION
        # 坐标信息获取与机器人运动同步问题
        synchro.acquire()
        if target.entity is not None:
            # Nao当前坐标
            Nao_x, Nao_y = self.getNaoGps()
            # self.getDistance()
            print("Nao的坐标（{},{}）".format(Nao_x, Nao_y))
            print("Target的坐标（{},{}）".format(target.entity[0], target.entity[1]))
            target_x, target_y = target.entity[0], target.entity[1]

            # 避障
            self.avoidObstacles()
            '''
            if abs(Nao_x - target_x) < ACCURACY and abs(Nao_y - target_y) < ACCURACY:
                print("到达目标附近")
                return

            # 考虑机器人的朝向，总共有16种组合
            # ============================================================================================= #
            # ===================================  目标在前面  ============================================== #
            # ============================================================================================= #
            if (target_x - Nao_x) > ACCURACY and DIRECTION == 0:
                print("目标在我的前面")
                t_ = ControllerThread("forwards", mutex2, self.startMotion, self.forwards)
                t_.start()
                self._move(target)

            elif (target_y - Nao_y) > ACCURACY and DIRECTION == 1:
                print("目标在我的前面")
                t_ = ControllerThread("forwards", mutex2, self.startMotion, self.forwards)
                t_.start()
                self._move(target)

            elif (Nao_x - target_x) > ACCURACY and DIRECTION == 2:
                print("目标在我的前面")
                t_ = ControllerThread("forwards", mutex2, self.startMotion, self.forwards)
                t_.start()
                self._move(target)

            elif (Nao_y - target_y) > ACCURACY and DIRECTION == 3:
                # 目标在我的前边
                print("目标在我的前边")
                t_ = ControllerThread("forwards", mutex2, self.startMotion, self.forwards)
                t_.start()
                self._move(target)
            # ============================================================================================= #
            # ===================================  目标在左边  ============================================== #
            # ============================================================================================= #
            elif (target_y - Nao_y) > ACCURACY and DIRECTION == 0:
                print("目标在我的左边")
                t_ = ControllerThread("turn left", mutex2, self.startMotion, self.turnLeft90)
                t_.start()
                self._move(target)

            elif (Nao_x - target_x) > ACCURACY and DIRECTION == 1:
                print("目标在我的左边")
                t_ = ControllerThread("turn left", mutex2, self.startMotion, self.turnLeft90)
                t_.start()
                self._move(target)

            elif (Nao_y - target_y) > ACCURACY and DIRECTION == 2:
                print("目标在我的左边")
                t_ = ControllerThread("turn left", mutex2, self.startMotion, self.turnLeft90)
                t_.start()
                self._move(target)

            elif (target_x - Nao_x) > ACCURACY and DIRECTION == 3:
                print("目标在我的左边")
                t_ = ControllerThread("turn left", mutex2, self.startMotion, self.turnLeft90)
                t_.start()
                self._move(target)
            # ============================================================================================= #
            # ===================================  目标在右边  ============================================== #
            # ============================================================================================= #
            elif (Nao_y - target_y) > ACCURACY and DIRECTION == 0:
                print("目标在我的右边")
                t_ = ControllerThread("turn right", mutex2, self.startMotion, self.turnRight90)
                t_.start()
                self._move(target)

            elif (target_x - Nao_x) > ACCURACY and DIRECTION == 1:
                print("目标在我的右面")
                t_ = ControllerThread("turn right", mutex2, self.startMotion, self.turnRight90)
                t_.start()
                self._move(target)

            elif (target_y - Nao_y) > ACCURACY and DIRECTION == 2:
                print("目标在我的右边")
                t_ = ControllerThread("turn right", mutex2, self.startMotion, self.turnRight90)
                t_.start()
                self._move(target)

            elif (Nao_x - target_x) > ACCURACY and DIRECTION == 3:
                print("目标在我的右面")
                t_ = ControllerThread("turn right", mutex2, self.startMotion, self.turnRight90)
                t_.start()
                self._move(target)
            # ============================================================================================= #
            # ===================================  目标在后面  ============================================== #
            # ============================================================================================= #
            elif (Nao_x - target_x) > ACCURACY and DIRECTION == 0:
                print("目标在我的后面")
                t_ = ControllerThread("backwards", mutex2, self.startMotion, self.turnLeft180)
                t_.start()
                self._move(target)

            elif (Nao_y - target_y) > ACCURACY and DIRECTION == 1:
                print("目标在我的后面")
                t_ = ControllerThread("backwards", mutex2, self.startMotion, self.turnLeft180)
                t_.start()
                self._move(target)

            elif (target_x - Nao_x) > ACCURACY and DIRECTION == 2:
                print("目标在我的后面")
                t_ = ControllerThread("backwards", mutex2, self.startMotion, self.turnLeft180)
                t_.start()
                self._move(target)

            elif (target_y - Nao_y) > ACCURACY and DIRECTION == 3:
                print("目标在我的后面")
                t_ = ControllerThread("backwards", mutex2, self.startMotion, self.turnLeft180)
                t_.start()
                self._move(target)
            '''

            while True:

                if abs(Nao_x - target_x) < ACCURACY and abs(Nao_y - target_y) < ACCURACY:
                    print("到达目标附近")
                    break

                # 考虑机器人的朝向，总共有16种组合
                # ============================================================================================= #
                # ===================================  目标在前面  ============================================== #
                # ============================================================================================= #
                if (target_x - Nao_x) > ACCURACY and DIRECTION == 0:
                    print("目标在我的前面")
                    t_ = ControllerThread("forwards", mutex2, self.startMotion, self.forwards)
                    t_.start()

                elif (target_y - Nao_y) > ACCURACY and DIRECTION == 1:
                    print("目标在我的前面")
                    t_ = ControllerThread("forwards", mutex2, self.startMotion, self.forwards)
                    t_.start()

                elif (Nao_x - target_x) > ACCURACY and DIRECTION == 2:
                    print("目标在我的前面")
                    t_ = ControllerThread("forwards", mutex2, self.startMotion, self.forwards)
                    t_.start()

                elif (Nao_y - target_y) > ACCURACY and DIRECTION == 3:
                    # 目标在我的前边
                    print("目标在我的前边")
                    t_ = ControllerThread("forwards", mutex2, self.startMotion, self.forwards)
                    t_.start()
                # ============================================================================================= #
                # ===================================  目标在左边  ============================================== #
                # ============================================================================================= #
                elif (target_y - Nao_y) > ACCURACY and DIRECTION == 0:
                    print("目标在我的左边")
                    t_ = ControllerThread("turn left", mutex2, self.startMotion, self.turnLeft90)
                    t_.start()

                elif (Nao_x - target_x) > ACCURACY and DIRECTION == 1:
                    print("目标在我的左边")
                    t_ = ControllerThread("turn left", mutex2, self.startMotion, self.turnLeft90)
                    t_.start()

                elif (Nao_y - target_y) > ACCURACY and DIRECTION == 2:
                    print("目标在我的左边")
                    t_ = ControllerThread("turn left", mutex2, self.startMotion, self.turnLeft90)
                    t_.start()

                elif (target_x - Nao_x) > ACCURACY and DIRECTION == 3:
                    print("目标在我的左边")
                    t_ = ControllerThread("turn left", mutex2, self.startMotion, self.turnLeft90)
                    t_.start()
                # ============================================================================================= #
                # ===================================  目标在右边  ============================================== #
                # ============================================================================================= #
                elif (Nao_y - target_y) > ACCURACY and DIRECTION == 0:
                    print("目标在我的右边")
                    t_ = ControllerThread("turn right", mutex2, self.startMotion, self.turnRight90)
                    t_.start()

                elif (target_x - Nao_x) > ACCURACY and DIRECTION == 1:
                    print("目标在我的右面")
                    t_ = ControllerThread("turn right", mutex2, self.startMotion, self.turnRight90)
                    t_.start()

                elif (target_y - Nao_y) > ACCURACY and DIRECTION == 2:
                    print("目标在我的右边")
                    t_ = ControllerThread("turn right", mutex2, self.startMotion, self.turnRight90)
                    t_.start()

                elif (Nao_x - target_x) > ACCURACY and DIRECTION == 3:
                    print("目标在我的右面")
                    t_ = ControllerThread("turn right", mutex2, self.startMotion, self.turnRight90)
                    t_.start()
                # ============================================================================================= #
                # ===================================  目标在后面  ============================================== #
                # ============================================================================================= #
                elif (Nao_x - target_x) > ACCURACY and DIRECTION == 0:
                    print("目标在我的后面")
                    t_ = ControllerThread("backwards", mutex2, self.startMotion, self.turnLeft180)
                    t_.start()

                elif (Nao_y - target_y) > ACCURACY and DIRECTION == 1:
                    print("目标在我的后面")
                    t_ = ControllerThread("backwards", mutex2, self.startMotion, self.turnLeft180)
                    t_.start()

                elif (target_x - Nao_x) > ACCURACY and DIRECTION == 2:
                    print("目标在我的后面")
                    t_ = ControllerThread("backwards", mutex2, self.startMotion, self.turnLeft180)
                    t_.start()

                elif (target_y - Nao_y) > ACCURACY and DIRECTION == 3:
                    print("目标在我的后面")
                    t_ = ControllerThread("backwards", mutex2, self.startMotion, self.turnLeft180)
                    t_.start()

                time.sleep(8)
                # Nao当前坐标
                Nao_x, Nao_y = self.getNaoGps()
                # self.getDistance()
                print("Nao的坐标（{},{}）".format(Nao_x, Nao_y))
                print("Target的坐标（{},{}）".format(target.entity[0], target.entity[1]))
                target_x, target_y = target.entity[0], target.entity[1]

                self.avoidObstacles()

        elif target.measureWord is not None and target.numeral is not None:
            if target.measureWord in ['米', 'm', 'M']:
                try:
                    distance = int(target.numeral) / 10
                except:
                    distance = 1/10
                Nao_x, Nao_y = self.getNaoGps()
                coordinate = [Nao_x, Nao_y]
                if motion == self.turnLeft180.motion:
                    t = ControllerThread("turnLeft180", mutex2, self.startMotion, self.turnLeft180)
                    t.start()
                else:
                    t = ControllerThread("handWave", mutex2, self.startMotion, self.handWave)
                    t.start()
                self._move_distance(motion, distance, coordinate)

    # 通过距离控制移动
    def _move_distance(self, motion, distance, coordinate):
        synchro.acquire()
        # Nao当前坐标
        Nao_x, Nao_y = self.getNaoGps()
        print("Nao的坐标（{},{}）".format(Nao_x, Nao_y))
        print("distance = {}".format(distance))
        if motion in [self.move.motion, self.forwards50.motion, self.forwards.motion, self.turnLeft180.motion]:
            if DIRECTION in [0, 2]:
                # x 方向
                distance -= abs(Nao_x - coordinate[0])
                t = ControllerThread("forwards", mutex2, self.startMotion, self.forwards)
                t.start()
                coordinate[0] = Nao_x
            else:
                distance -= abs(Nao_y - coordinate[1])
                t = ControllerThread("forwards", mutex2, self.startMotion, self.forwards)
                t.start()
                coordinate[1] = Nao_y
        elif motion == self.backwards.motion:
            if DIRECTION in [0, 2]:
                # x 方向
                distance -= abs(Nao_x - coordinate[0])
                t = ControllerThread("backwards", mutex2, self.startMotion, self.backwards)
                t.start()
                coordinate[0] = Nao_x
            else:
                distance -= abs(Nao_y - coordinate[1])
                t = ControllerThread("backwards", mutex2, self.startMotion, self.backwards)
                t.start()
                coordinate[1] = Nao_y

        if distance > 0:
            self._move_distance(motion, distance, coordinate)

    def startMotionWithTarget(self, motion, target):

        if target.measureWord == "度":
            if str(target.numeral) in ["40", "四十"]:
                # 将左转(右转)90度的motion换为左转(右转)40
                # 纯属无奈之举，因为动作是motion固定的
                if motion == self.turnLeft90.motion:
                    motion = self.turnLeft40.motion
                elif motion == self.turnRight90.motion:
                    motion = self.turnRight40.motion
            elif str(target.numeral) in ["60", "六十"]:
                # 将左转(右转)90度的motion换为左转(右转)60
                if motion == self.turnLeft90.motion:
                    motion = self.turnLeft60.motion
                elif motion == self.turnRight90.motion:
                    motion = self.turnRight60.motion
            self.startMotion(motion)
        else:
            self._move(target, motion)

    # 获取指令并传给分析器
    def setInstruction(self):
        self.instruction = input("请输入指令：")
        # self.instruction = "机器人前进到桌子，然后左转"
        self.analyer.setInstruction(self.instruction)
        self.generateActionQueue()

    # 动作预处理
    def actionPreprocessing(self, action):
        '''
        （1）将motionControl 转化为 Motion_对象。
        （2）如果有目标模块，提取转化信息。
        :param action: Action类型
        :return:
        '''
        turn_flag = False
        motion = self.handWave
        if action.motionControl == "move":
            if action.movingTarget is None:
                motion = self.forwards50
            else:
                motion = self.move
        elif action.motionControl == "turnLeft":
            motion = self.turnLeft90
        elif action.motionControl == "turnRight":
            motion = self.turnRight90
        elif action.motionControl == "wave":
            motion = self.handWave
        elif action.motionControl == "back":
            motion = self.backwards
        else:
            pass
        if action.movingTarget is not None and not turn_flag:
            # 暂时用OBJECT_TABLE代替，
            # 以后可以用Entity对象，那样不但可以保存坐标信息（还可以不止一个坐标），
            # 还可以保存物体名称，如”桌子“
            # action.movingTarget.entity = OBJECT_TABLE.get(action.movingTarget.entity, None)

            # 获取（实体+方位）的坐标，如果它们不为空的话
            # 如 （“桌子” + “左边”）=> (x,y)
            action.movingTarget.entity = getEntityObject(action.movingTarget.entity, action.movingTarget.position)
            func = self.startMotionWithTarget
        else:
            func = self.startMotion
        return action, motion, func

    # 生成一个动作序列
    # 每个动作是一个线程
    def generateActionQueue(self):
        while self.instruction is None:
             pass

        self.analyer.createSentenceTree()
        actionSequeue = self.analyer.generateActionSequence()
        for action in actionSequeue.actionSequence:
            action, motion, func = self.actionPreprocessing(action)
            try:
                actionThread = ControllerThread(action.motionControl + "动作", mutex1, func, motion, action.movingTarget)
            except TypeError:
                print("NAO动作库中没有该动作，NAO挥挥手吧")
                actionThread = ControllerThread("handWave" + "动作", mutex1, func, motion, action.movingTarget)
            self.actionQueue.put(actionThread)
        self.instruction = None
        inputThread = InputThread(mutex1, self.setInstruction)
        self.actionQueue.put(inputThread)

    def run(self):
        self.setInstruction()
        handWaveThread = ControllerThread("hand wave", mutex1, self.startMotion, self.handWave)
        handWaveThread.start()

        while True:

            while not self.actionQueue.empty():
                t = self.actionQueue.get()
                t.start()

            if self.step(self.timeStep) == -1:
                break


if __name__ == "__main__":
    nao = Nao()
    nao.run()
