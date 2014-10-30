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
