'''
This module contain the functions to build, orient and reorient joint.
'''

'''
大致的思路
骨架的所有数据都是保存在一个数据库里，可能tuple比较好一点，有排序并且不能更改
每个关节都需要以下数据，
父节点（如果为None，就是最高一级），string
translate这是相对父节点的位置，（0,0,0）
rotate order，string 'xyz'
joint orientation 三个数值，(0,0,0)
joint的名字，包含方位，身体部件，后缀和功能名称，string

可以利用odwrigbuild.motion.joint 里面的findJointsInChain()功能来从现存的骨架获得名称列表
然后把列表中所有关节的相关数据获取出来

ab=((None, 'M_head_inf', (0, 0,0), (0,0, 45), 'zyx'),
('M_head_inf', 'M_head_iend', (1.414, 0,0), (-38.291, 67.153, -85.587), 'zyx'))
for node in ab:
  if node[0]==None:
    cmds.select(cl=True)
  else:
    cmds.select(node[0], r=True)
  cmds.joint(p=node[2], r=True, n=node[1], o=node[3], roo=node[4], rad=0.3)
'''

import maya.cmds as cmds
import re
import math

JOINT_ORIENT_THRESHOLD = .0001

