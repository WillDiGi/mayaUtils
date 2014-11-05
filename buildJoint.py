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

JOINT_ORIENT_THRESHOLD = .0001

import maya.cmds as cmds
import odwrigbuild.motion.joint as odwJoint
import json

def getherJntData(jnt):
  jointList = []
  jointList.extend(odwJoint.findJointsInChain(jnt))
  jointData = []
  for jnt in jointList:
    jntPar = cmds.listRelatives(jnt, parent=True)
    jntName = jnt
    jntTrans = cmds.getAttr('%s.translate' % jnt)[0]
    jntOrt = cmds.getAttr('%s.jointOrient' % jnt)[0]
    jntRoo = cmds.getAttr('%s.rotateOrder' % jnt)
    jntRad = cmds.getAttr('%s.radius' %  jnt)
    jointData.append([jntPar, jntName, jntTrans, jntOrt, jntRoo])
  return jointData

def exportJntData(jntData):
  dataFileExtension='.data'
  startDir = cmds.workspace(q=True, rootDirectory=True)
  filePath = cmds.fileDialog2(dialogStyle=2, fileMode=0, startingDirectory=startDir,
                              fileFilter='Data Files (*%s)' % dataFileExtension)[0]
  if not filePath.endswith(dataFileExtension):
    filePath += dataFileExtension
  fh = open(filePath, 'wb')
  data = json.dumps(jntData, indent=2)
  fh.write(data)
  fh.close()
  print 'Exporting attribute data successed!'

def importJntData():
  dataFileExtension='.data'
  startDir = cmds.workspace(q=True, rootDirectory=True)
  filePath = cmds.fileDialog2(dialogStyle=2, fileMode=1, startingDirectory=startDir,
              fileFilter='Data Files (*%s)' % dataFileExtension)
  if not isinstance(filePath, basestring):
    filePath = filePath[0]
  fh = open(filePath, 'rb')
  data = json.loads(fh.read())
  fh.close()
  return data

def createJntFromData(jntData, nameSpace='temp'):
  for jnt in jointData:
    if jnt[0]==None:
      cmds.select(cl=True)
    else:
      cmds.select(jnt[0], r=True)
    newJnt = cmds.joint(p=jnt[2], r=True, n=jnt[1], o=jnt[3], rad=0.3)
    cmds.setAttr('%s.rotateOrder' % jnt[1], jnt[4])
