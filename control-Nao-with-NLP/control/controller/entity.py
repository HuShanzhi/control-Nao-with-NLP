# -*- coding:utf-8 -*-
# Author: HuXiaoMing
# Date: 2021-4-26
# 存储Webots仿真环境world中实体（如桌子）的信息

# 多扩充的范围，以免碰撞
EXTENT = 0.25


class Entity:

    def __init__(self, x=0.0, y=0.0, z=0.0, y_length=0.0, x_length=0.0, height=0.0, name="实体"):
        # 实体坐标（x, y, z）
        self.x = x
        self.y = y
        self.z = z
        # 实体大小 (长，宽，高)
        self.x_length = x_length
        self.y_length = y_length
        self.height = height
        # 实体名称
        self.name = name
        self.setPosition()

    def setPosition(self):

        self.front = (self.x - self.x_length/2 - EXTENT, self.y)
        self.behind = (self.x + self.x_length/2 + EXTENT, self.y)
        self.left = (self.x, self.y - self.y_length - EXTENT)
        self.right = (self.x, self.y + self.y_length + EXTENT)



class Desk(Entity):
    pass


class Light(Entity):
    pass


desk = Entity(x=-0.8, y=-2.5, z=0, x_length=1.2, y_length=0.8, height=0.53, name="桌子")

light = Entity(x=-3.8, y=-4.1, z=0, x_length=0.25, y_length=0.25, name="落地灯")

entities = (desk, light)


def getEntityObject(entityName, position = "前面"):

    if entityName is None:
        return None

    for item in entities:
        if item.name == entityName:
            if position in ["前面", "前方", "前边"]:
                return item.front
            elif position in ["后面", "后方", "后边"]:
                return item.behind
            elif position in ["左面", "左方", "左边"]:
                return item.left
            elif position in ["右面", "右方", "右边"]:
                return  item.right
            else:
                return item.front

    return None
