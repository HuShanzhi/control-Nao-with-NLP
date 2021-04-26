# -*- coding:utf-8 -*-
# Author: HuXiaoMing
# Date: 2021-4-22
# 主函数
# 如果提示找不到_controller包，是因为main.py文件的Environments Variables未配置
from control.controller.naoController import Nao


if __name__ == "__main__":
    nao = Nao()
    nao.run()