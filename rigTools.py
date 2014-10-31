# Rigging Tools.
#2014.10.31.
#weihe@willdigi.com

import maya.cmds as cmds

def createFollicle(baseMesh, n='folli', uv=[0.5,0.5]):
    folliShape=cmds.createNode('follicle', n=n+'Shape')
    folliTrans=cmds.listRelatives(folliShape, parent=True)[0]
    baseShape=cmds.listRelatives(baseMesh, shapes=True)[0]

    cmds.connectAttr('%s.local' %baseShape, '%s.inputSurface' %folliShape)
    cmds.connectAttr('%s.worldMatrix[0]' %baseShape, '%s.inputWorldMatrix' %folliShape)
    cmds.connectAttr('%s.outRotate' %folliShape, '%s.rotate' %folliTrans)
    cmds.connectAttr('%s.outTranslate' %folliShape, '%s.translate' %folliTrans)
    cmds.setAttr('%s.parameterU' %folliShape, uv[0])
    cmds.setAttr('%s.parameterV' %folliShape, uv[1])
