# Rigging Utilits.
#2014.08.29.
#weihe@willdigi.com

import maya.cmds as cmds

def matchTrans(source, target):
    dummyConstraint = cmds.parentConstraint(source, target, mo=False)[0]
    cmds.delete(dummyConstraint)

def insertOffset(target):
    offsetGrp = cmds.createNode('transform', n=target+'_off')
    matchTrans(target, offsetGrp)
    parentNode = cmds.listRelatives(target, p=True)
    if type(parentNode) != 'NoneType':
        cmds.parent(offsetGrp, parentNode)
    cmds.parent(target, offsetGrp)
    return offsetGrp

def insertSDK(source, target):
    locGrp = cmds.createNode('transform', name=target+'_'+source+'_loc')
    sdkGrp = cmds.createNode('transform', name=target+'_'+source+'_sdk')
    cmds.parent(sdkGrp, locGrp)
    matchTrans(source, locGrp)
    parentNode = cmds.listRelatives(target, p=True)[0]
    if parentNode.split('_')[-1] != 'off':
        offsetGrp = insertOffset(target)
    else:
        offsetGrp = parentNode
        parentNode = cmds.listRelatives(offsetGrp, p=True)
    cmds.parent(locGrp, parentNode)
    cmds.parent(offsetGrp, sdkGrp)
    cmds.connectAttr(source+'.rotate', sdkGrp+'.rotate')
    cmds.connectAttr(source+'.translate', sdkGrp+'.translate')
