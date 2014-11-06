# Rigging Utilits.
#2014.10.30.
#weihe@willdigi.com

import maya.cmds as cmds
import maya.mel as mel

gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')

def matchTrans(source, target):
    dummyConstraint = cmds.parentConstraint(source, target, mo=False)[0]
    cmds.delete(dummyConstraint)

def insertGrp(node, extension, addon = False):
    if addon:
        grpNode = cmds.createNode('transform', n=node+'_'+extension)
    else:
        grpNode = cmds.createNode('transform', n=('_'.join(node.split('_')[:-1]+[extension])))
    matchTrans(node, grpNode)
    parentNode = cmds.listRelatives(node, p=True)
    if parentNode != None:
        cmds.parent(grpNode, parentNode)
    cmds.parent(node, grpNode)
    return grpNode

def insertSDK(source, target):
    '''
    Create extra sdk group on top of a controller and driven by another node.
    :Parameters:
        source : 'str'
            the node which will drive the sdk group.
        target : 'str'
            the node which will be parent to the sdk group and driven by source node.
    :Return:
        None
    '''
    locGrp = cmds.createNode('transform', name=target+'_'+source+'_loc')
    sdkGrp = cmds.createNode('transform', name=target+'_'+source+'_sdk')
    cmds.parent(sdkGrp, locGrp)
    matchTrans(source, locGrp)
    parentNode = cmds.listRelatives(target, p=True)[0]
    if parentNode.split('_')[-1] != 'off':
        offsetGrp = insertGrp(target, 'off', True)
        #cmds.setAttr('%s.scale' % offsetGrp, cmds.getAttr('%s.scale' % parentNode)[0])
        #cmds.setAttr('%s.scale' % offsetGrp, (1.0,1.0,1.0))
    else:
        offsetGrp = parentNode
        parentNode = cmds.listRelatives(offsetGrp, p=True)
    cmds.parent(locGrp, parentNode)
    cmds.parent(offsetGrp, sdkGrp)
    cmds.connectAttr(source+'.rotate', sdkGrp+'.rotate')
    cmds.connectAttr(source+'.translate', sdkGrp+'.translate')

def  matchAttr(attrList=['input2X', 'input2Y', 'input2Z'], nodeType='multiplyDivide', LtoR=True):
    selectList = cmds.ls(sl=True, type = nodeType)
    side = ['L', 'R'] if LtoR else ['R', 'L']
    for node in selectList:
        tempName = node.split('_')
        if tempName[0] == side[0]:
            targetNode = '_'.join(side[1:]+tempName[1:])
            if cmds.objExists(targetNode):
                for attr in attrList:
                    try:
                         cmds.setAttr('%s.%s' %(targetNode, attr), cmds.getAttr('%s.%s' %(node, attr)))
                    except:
                        print "%s.%s can't be changed." %(targetNode, attr)
            else:
                print '%s not exists.' %targetNode
        else:
            print '%s is not a %s object' %(node, side[0])

def mirrorTrans():
    selectList=cmds.ls(sl=True)
    side = ['L', 'R']
    reMatrix = [-1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    for node in selectList:
        tempName = node.split('_')
        if tempName[0] in side:
            opSide = 'R' if tempName[0] == 'L' else 'L'
            targetNode = '_'.join([opSide]+tempName[1:])
            if cmds.objExists(targetNode):
                mmNode = cmds.createNode('multMatrix', n='_'.join([opSide]+tempName[1:]+['mmat']))
                dmNode = cmds.createNode('decomposeMatrix', n='_'.join([opSide]+tempName[1:]+['dmat']))
                cmds.connectAttr('%s.matrix' %node, '%s.matrixIn[0]' %mmNode, f=True)
                cmds.setAttr('%s.matrixIn[1]' %mmNode, reMatrix, type = 'matrix')
                cmds.connectAttr('%s.matrixSum' %mmNode, '%s.inputMatrix' %dmNode)
                cmds.connectAttr('%s.outputTranslate' %dmNode, '%s.translate' %targetNode)
                cmds.connectAttr('%s.outputRotate' %dmNode, '%s.rotate' %targetNode)
                cmds.connectAttr('%s.outputScale' %dmNode, '%s.scale' %targetNode)
            else:
                print '%s not exists.' % targetNode
        else:
            print "%s doesn't have mirror node." % node

def addMd():
    pass

def freeTrans(objList = [], attList = ['translate', 'tx', 'ty', 'tz', 'rotate', 'rx', 'ry', 'rz']):
    if len(objList) == 0:
        objList = cmds.ls(sl=True)
    if len(objList) != 0:
        for obj in objList:
            for att in attList:
                cmds.setAttr('%s.%s' %(obj, att), cb = True)
                cmds.setAttr('%s.%s' %(obj, att), lock = False)
                cmds.setAttr('%s.%s' %(obj, att), keyable = True)
    else:
        print 'Need to select some object.'

def lockTrans(objList = [], attList = ['translate', 'tx', 'ty', 'tz', 'rotate', 'rx', 'ry', 'rz']):
    if len(objList) == 0:
        objList = cmds.ls(sl=True)
    if len(objList) != 0:
        for obj in objList:
            for att in attList:
                cmds.setAttr('%s.%s' %(obj, att), keyable = False)
                cmds.setAttr('%s.%s' %(obj, att), cb = False)
                cmds.setAttr('%s.%s' %(obj, att), lock = True)
    else:
        print 'Need to select some object.'

def progressStart(msg,max): 
    cmds.progressBar(gMainProgressBar, e=True, bp=True, ii=True, st=msg, max=max)

def progressStep():
    cmds.progressBar(gMainProgressBar, e=True, s=1)
    
def progressEnd():
    cmds.progressBar(gMainProgressBar, e=True, ep=True)

def createCtrlPositionData():
    '''
    This method finds all the ctrl objects in a scene, and creates a data set
    describing the positions of the cvs in world space. This data is used to
    reposition the controls after the rig is built.
    
    This is the format of the data:
    
    data = [('ctrlA':['ctrlAShape':[[point1.X, point1.Y, point1.Z],
                                    [point2.X, point2.Y, point2.Z],
                                    etc...]]),
            ('ctrlB':['ctrlBShape':[[point1.X, point1.Y, point1.Z],
                                    [point2.X, point2.Y, point2.Z],
                                     etc...],
                      'ctrlBShape1':[point1.X, point1.Y, point1.Z]]),   
           ]
    
    :Returns:
        A list of ctrlData tuples
        
    :Rtype:
        `list`
    
    '''
    data =[]
    for control in cmds.ls('*.animCtrl', o=True):
        shapes = cmds.listRelatives(control,  shapes=1, type='nurbsCurve')
        shapeData = {}
        for shape in shapes:
            pointData = []
            for i in range(cmds.getAttr('%s.controlPoints' % shape, size=1)):
                pointData.append(cmds.pointPosition('%s.cv[%s]' % (shape, i), w=1))
            shapeData[shape] = pointData
        data.append((control,shapeData))
    return data

def positionCtrls(ctrlData):
    '''
    Positions the controls from the provided data. See createCtrlPositionData()
    for the format of said data
    
    :Parameters:
        ctrlData : `list`
            A list of ctrlData tuples
    '''
    notMatched = []
    currentCtrls = cmds.ls('*.animCtrl', o=True)
    for data in ctrlData:
        ctrl = data[0]
        shapeData = data[1]
        numCtrls = len(cmds.ls(ctrl))
        if numCtrls == 1:
            shapes = shapeData.keys()
            for shape in shapes:
                numShapes = len(cmds.ls(shape))
                if numShapes == 1:
                    curNumPnts = cmds.getAttr('%s.controlPoints' % shape, size=1)
                    oldNumPnts = len(shapeData[shape])
                    if curNumPnts == oldNumPnts:
                        for i, cv in enumerate(shapeData[shape]):
                            cmds.xform('%s.cv[%s]' % (shape, i), ws=1, t=(cv[0], cv[1], cv[2]))
                    else:
                        notMatched.append(shape)
                else:
                    notMatched.append(shape)
        else:
            notMatched.append(ctrl)
        if ctrl in currentCtrls:
            currentCtrls.remove(ctrl)
    
    #report back
    if notMatched:
        cmds.warning("Couldn't match the following:\n%s" % '\n'.join(notMatched))
