'''
Deveolped By Tim Mackintosh 
To make using the Maya API easier
Its also handy to store objects as DependNode Objects because its a 
MFnDependencyNode and is a pointer to the object rather than the string
'''

import maya.cmds as cmds
from maya import OpenMaya
import types, fnmatch, sys, re, inspect
from maya import cmds, OpenMaya, OpenMayaAnim

class DependNode(OpenMaya.MFnDependencyNode):
    @classmethod
    def create(cls, nodeType, nodeName=None):
        dNode = DependNode(cmds.createNode(nodeType))
        if dNode.hasFn(OpenMaya.MFn.kShape):
            dNode = dNode.getParent()
        if nodeName: dNode.setName(findUniqueName(nodeName))
        return dNode

    def __init__(self, inObject=None):
        OpenMaya.MFnDependencyNode.__init__(self)
        self.__obj = None

        if isinstance(inObject, OpenMaya.MObject):
            self.__obj=inObject

        elif isinstance(inObject, OpenMaya.MDagPath):
            self.__obj=inObject.node()

        elif issubclass(inObject.__class__, DependNode):
            self.__obj=inObject.asMObject()

        elif (isinstance(inObject, str)) or (isinstance(inObject, unicode)):
            if not cmds.objExists(inObject):
                raise Exception, "DependNode: \n\tObject '" + inObject + "' does NOT exist."
            list = OpenMaya.MSelectionList()
            self.__obj = OpenMaya.MObject()
            OpenMaya.MGlobal.getSelectionListByName(inObject, list)
            list.getDependNode(0,self.__obj)

        if inObject and (not self.__obj):
            raise Exception, "Illegal type passed in to DependNode!!!\n\t" + `type(inObject)` + " Passed in."

        if self.__obj:
            OpenMaya.MFnDependencyNode.setObject(self, self.__obj)

    def __eq__(self, otherObj):
        if isinstance(otherObj, self.__class__):
            return self.object() == otherObj.asMObject()
        else:
            return False

    def setObject(self, inObject):
        dNode = DependNode(inObject)
        obj = dNode.asMObject()
        OpenMaya.MFnDependencyNode.setObject(self, obj)
        self.__obj = obj

    def isDagNode(self):
        if self.object().hasFn(OpenMaya.MFn.kDagNode):
            return True
        return False

    def __assertDagNode(self):
        assert self.isDagNode(), "Function only relevant to dagNodes!"

    def asMObject(self):
        return OpenMaya.MFnDependencyNode.object(self)

    def asMDagPath(self):
        self.__assertDagNode()
        dPath = OpenMaya.MDagPath.getAPathTo(self.object())
        return dPath

    def asMItGeometry(self):
        self.__assertDagNode()
        dPath = OpenMaya.MItGeometry(self.asMObject())
        return dPath

    def asMFnDagNode(self):
        self.__assertDagNode()
        return OpenMaya.MFnDagNode(self.asMDagPath())

    def asMFnTransform(self):
        self.__assertDagNode()
        return OpenMaya.MFnTransform(self.asMDagPath())

    def asMFnIkJoint(self):
        self.__assertDagNode()
        if self.getApiTypeStr() != 'kJoint':
            raise riggingToolsError.RiggingToolsError, 'This method can be used only for DagNodeWrappers that "contains" a dagNode of type kJoint, but the wrapped dagNode is of type %s' %self.getApiTypeStr()
        path = OpenMaya.MDagPath()
        self.asMFnDagNode().getPath(path)
        tran = OpenMayaAnim.MFnIkJoint(path)
        return tran

    def asMFnNurbsCurve(self):
        assert (self.asMObject().hasFn(OpenMaya.MFn.kNurbsCurve)), "Object has no functions 'kNurbsCurve'"
        crvFn = OpenMaya.MFnNurbsCurve()
        crvFn.setObject(self.asMDagPath())
        return crvFn

    def asMFnSkinCluster(self):
        assert (self.asMObject().hasFn(OpenMaya.MFn.kSkinClusterFilter)), "Object has no functions 'kSkinCluster'"
        scFn = OpenMayaAnim.MFnSkinCluster()
        scFn.setObject(self.asMObject())
        return scFn

    def asMFnMesh(self):
        assert (self.asMObject().hasFn(OpenMaya.MFn.kMesh)), "Object has no function 'kMesh'"
        meshFn = OpenMaya.MFnMesh()
        meshFn.setObject(self.asMDagPath())
        return meshFn

    def getName(self):
        return self.name()

    def getFullName(self):
        if self.isDagNode():
            return OpenMaya.MFnDagNode(self.object()).fullPathName()
        return self.getName()

    def fullName(self):
        return self.getFullName()

    def getShortName(self):
        if self.isDagNode():
            fullName = OpenMaya.MFnDagNode(self.object()).fullPathName()
            tokes = fullName.split("|")
            return tokes[len(tokes)-1]
        return self.getName()

    def shortName(self):
        return self.getShortName()

    def getPartialName(self):
        if self.isDagNode():
            return self.asMDagPath().partialPathName()
        return self.getName()

    def partialName(self):
        return self.getPartialName()

    def setName(self, name):
        OpenMaya.MFnDependencyNode.setName(self, findUniqueName(name))

    def getApiTypeStr(self):
        return self.object().apiTypeStr()

    def getApiType(self):
        return self.object().apiType()

    def hasFn(self, MFn):
        if self.asMObject().hasFn(MFn):
            return True
        return False

    def setColor(self, colorIndex):
        self.__assertDagNode()
        self.setAttr("overrideColor", colorIndex)
        self.setAttr("overrideEnabled", 1)

    def getChildren(self, name="*", inTypes=None, recursive=False, ignoreNamespace=True, noIntermediate=False):
        self.__assertDagNode()
        childrenFound = DependNodeArray()

        def _getThem(nodeName, name, inTypes, recursive, ignoreNamespace):
            children = None
            children = cmds.listRelatives(nodeName, ni=noIntermediate, children=True, fullPath=True)

            if noIntermediate and children:
                myList = [node for node in children if not cmds.getAttr(node + '.intermediateObject')]
                children = myList

            if children:
                for childName in children:
                    shortName = childName.split("|")[-1]
                    if ignoreNamespace:
                        shortName = shortName.split(":")[-1]
                    if fnmatch.fnmatch(shortName, name):
                        wrapper = DependNode(childName)
                        if inTypes:
                            for type in inTypes:
                                if issubclass(type.__class__, str):
                                    if wrapper.getApiTypeStr()==type:
                                        childrenFound.append(wrapper)
                                elif issubclass(type.__class__, int):
                                    if wrapper.hasFn(type):
                                        childrenFound.append(wrapper)
                        else:
                            childrenFound.append(wrapper)
                    if recursive:
                        _getThem(childName, name, inTypes, recursive, ignoreNamespace)

        _getThem(self.getFullName(), name, inTypes, recursive, ignoreNamespace)

        return childrenFound

    def getChild(self, val, inTypes=None, recursive=False, ignoreNamespace=True):
        self.__assertDagNode()
        child = None
        if type(val) == int:
            children = self.getChildren('*', inTypes, recursive, ignoreNamespace)
            child = children[val]
        elif type(val) == str:
           children = self.getChildren(val, inTypes, recursive, ignoreNamespace)
           if len(children) > 0:
               child = children[0]

        return child

    def getChildrenCount(self):
        self.__assertDagNode()
        '''
        Return the number of children of this DAG node.
        @return: Integer
        '''
        return self.self.asMDagPath().childCount()

    def getParent(self):
        self.__assertDagNode()
        return DependNode(self.asMFnDagNode().parent(0))

    def setParent(self, parent, preserveState=False):
        self.__assertDagNode()
        parentNode = DependNode(parent)

        currentTranslateLockStates = None
        if preserveState:
            currentTranslateLockStates = self.lockAttributes(["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"],
                                                         [0,0,0, 0,0,0, 0,0,0])
        cmds.parent(self.getFullName(), parentNode.getFullName())
        if preserveState:
            self.lockAttributes(["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"], currentTranslateLockStates)

    def getMostAscendant(self):
        self.__assertDagNode()
        parent = self
        while (cmds.listRelatives(parent.getFullName(), p=True)):
            parent = DependNode(cmds.listRelatives(parent.getFullName(), f=True, p=True)[0])
        return parent

    def listHistory(self, MFnType=None, future=False, includeShapeHistory=False):
        direction = OpenMaya.MItDependencyGraph.kUpstream
        traversal = OpenMaya.MItDependencyGraph.kBreadthFirst
        filter = OpenMaya.MFn.kInvalid
        if future:
            direction = OpenMaya.MItDependencyGraph.kDownstream
        if MFnType:
            filter = MFnType

        rootNodes = [self]
        if (includeShapeHistory) and (self.isDagNode()):
            shapes = self.getChildren("*", [OpenMaya.MFn.kShape], False)
            for i in range(0, len(shapes)):
                rootNodes.append(shapes[i])

        historyNodes = DependNodeArray()
        for node in rootNodes:
            try:
                iter = OpenMaya.MItDependencyGraph(node.asMObject(),
                                                   filter,
                                                   direction,
                                                   traversal)
                try:
                    while(not iter.isDone()):
                        dn = DependNode(iter.currentItem())
                        historyNodes.append(DependNode(iter.currentItem()))
                        iter.next()
                except:
                    pass
            except:
                return historyNodes
        return historyNodes

    def getWorldTranslation(self):
        self.__assertDagNode()
        return self.asMFnTransform().getTranslation(OpenMaya.MSpace.kWorld)

    def getWorldPosition(self):
        self.__assertDagNode()
        t = self.getWorldTranslation()
        return OpenMaya.MPoint(t.x, t.y, t.z)

    def setWorldTranslation(self, mVector):
        self.__assertDagNode()
        currentTranslateLockStates = self.lockAttributes(["tx", "ty", "tz"], [0,0,0])
        self.asMFnTransform().setTranslation(mVector, OpenMaya.MSpace.kWorld)
        self.lockAttributes(["tx", "ty", "tz"], currentTranslateLockStates)

    def setWorldPosition(self, mVector):
        if mVector.__class__==list:
            mVector = OpenMaya.MVector(mVector[0], mVector[1], mVector[2])
        self.setWorldTranslation(mVector)

    def getLocalTranslation(self):
        self.__assertDagNode()
        return self.asMFnTransform().getTranslation(OpenMaya.MSpace.kObject)

    def setLocalTranslation(self, mVector):
        self.__assertDagNode()
        currentTranslateLockStates = self.lockAttributes(["tx", "ty", "tz"], [0,0,0])
        self.asMFnTransform().setTranslation(mVector, OpenMaya.MSpace.kObject)
        self.lockAttributes(["tx", "ty", "tz"], currentTranslateLockStates)

    def setLocalScale(self, list3):
        self.__assertDagNode()
        currentTranslateLockStates = self.lockAttributes(["sx", "sy", "sz"], [0,0,0])
        su = OpenMaya.MScriptUtil()
        su.createFromList([list3[0], list3[1], list3[2]], 3)
        dPtr = su.asDoublePtr()
        self.asMFnTransform().setScale(dPtr)
        self.lockAttributes(["sx", "sy", "sz"], currentTranslateLockStates)

    def getMatrix(self):
        self.__assertDagNode()
        globalMatrix = self.getWorldMatrix()
        parentInverse = self.getParentMatrix().inverse()
        return globalMatrix*parentInverse

    def setMatrix(self, inMatrix):
        self.__assertDagNode()
        thisTran = self.asMFnTransform()
        tMatrix = OpenMaya.MTransformationMatrix(inMatrix)
        thisTran.set( tMatrix )

    def getWorldMatrix(self):
        self.__assertDagNode()
        return self.asMDagPath().inclusiveMatrix()

    def setWorldMatrix(self, inMatrix, useJointOrient=False):
        self.__assertDagNode()
        currentTranslateLockStates = self.lockAttributes(["tx", "ty", "tz", "rx", "ry", "rz" ,"sx", "sy", "sz"],
                                                         False)
        thisTran = self.asMFnTransform()
        if self.asMFnDagNode().dagRoot().apiTypeStr=='kWorld':
            tMatrix = OpenMaya.MTransformationMatrix(inMatrix)
            thisTran.set( tMatrix )
        else:
           parentInvMatrix = self.getParent().getWorldMatrixInverse()
           worldMat = inMatrix * parentInvMatrix
           tMatrix = OpenMaya.MTransformationMatrix(worldMat)
           thisTran.set( tMatrix )

        if self.getApiTypeStr()=="kJoint":
            if useJointOrient:
                cmds.setAttr(self.getFullName() + ".jox", cmds.getAttr(self.getFullName() + ".rx"))
                cmds.setAttr(self.getFullName() + ".joy", cmds.getAttr(self.getFullName() + ".ry"))
                cmds.setAttr(self.getFullName() + ".joz", cmds.getAttr(self.getFullName() + ".rz"))
                cmds.setAttr(self.getFullName() + ".rx", 0)
                cmds.setAttr(self.getFullName() + ".ry", 0)
                cmds.setAttr(self.getFullName() + ".rz", 0)
        self.lockAttributes(["tx", "ty", "tz", "rx", "ry", "rz" ,"sx", "sy", "sz"], currentTranslateLockStates)

    def getWorldMatrixInverse(self):
        self.__assertDagNode()
        return self.asMDagPath().inclusiveMatrixInverse()

    def getParentMatrix(self):
        self.__assertDagNode()
        return self.asMDagPath().exclusiveMatrix()

    def getParentInverseMatrix(self):
        self.__assertDagNode()
        return self.asMDagPath().exclusiveMatrix().inverse()

    def getXVec(self):
        self.matrix = self.getWorldMatrix()
        self.xVec = OpenMaya.MVector(self.matrix(0,0), self.matrix(0,1), self.matrix(0,2))
        return self.xVec

    def getYVec(self):
        self.matrix = self.getWorldMatrix()
        self.yVec = OpenMaya.MVector(self.matrix(1,0), self.matrix(1,1), self.matrix(1,2))
        return self.yVec

    def getZVec(self):
        self.matrix = self.getWorldMatrix()
        self.zVec = OpenMaya.MVector(self.matrix(2,0), self.matrix(2,1), self.matrix(2,2))
        return self.zVec

    def getParent(self):
        self.__assertDagNode()
        return DependNode((OpenMaya.MFnDagNode(self.object())).parent(0) )

    def getAttrAsMPlug(self, attribute):
        try:
            plug = self.findPlug(attribute)
            return plug

        except:
            try:
                list = OpenMaya.MSelectionList()
                OpenMaya.MGlobal.getSelectionListByName((self.getFullName() + "." + attribute), list)
                if not list.length():
                    return None

                plug = OpenMaya.MPlug()
                list.getPlug(0, plug)
                return plug
            except:
                return None

    def getAttrAsMObject(self, attribute):
        plug = self.getAttrAsMPlug(attribute)
        return plug.attribute()

    #Returns state before changed
    #lockValues accepts a bool or list of attributes the length of attributes
    def lockAttributes(self, attributes, lockValues=None):
        setValues = []
        if (lockValues==True):
            setValues = [True] * len(attributes)
        elif (lockValues==False):
            setValues = [False] * len(attributes)
        elif (hasattr(lockValues, "__class__")) and (lockValues.__class__==list):
            setValues = lockValues
        else:
            setValues = [True] * len(attributes)

        currentStates = []
        for i in range(0, len(attributes)):
            lockedState = cmds.getAttr(self.getFullName() + "." + attributes[i], l=True)
            currentStates.append(lockedState)
            cmds.setAttr(self.getFullName() + "." + attributes[i], l=setValues[i])

        return currentStates

    #Returns state before changed
    #keyableValues accepts a bool or list of attributes the length of attributes
    def setAttributesKeyable(self, attributes, keyableValues=None):
        setValues = []
        if (keyableValues==True):
            setValues = [True] * len(attributes)
        elif (keyableValues==False):
            setValues = [False] * len(attributes)
        elif (hasattr(keyableValues, "__class__")) and (keyableValues.__class__==list):
            setValues = keyableValues
        else:
            setValues = [True] * len(attributes)

        currentStates = []
        for i in range(0, len(attributes)):
            keyableState = cmds.getAttr(self.getFullName() + "." + attributes[i], k=True)
            currentStates.append(keyableState)
            cmds.setAttr(self.getFullName() + "." + attributes[i], k=setValues[i])

        return currentStates

    #flags is the mel flags that can be used on addAttr
    def addAttr(self, **flags):
        val = cmds.addAttr(self.getFullName(), **flags)
        return val

    #flags is the mel flags that can be used on setAttr
    def setAttr(self, attr, *args, **flags):
        val = cmds.setAttr(self.getFullName() + "." + attr, *args, **flags)
        return val

    #flags is the mel flags that can be used on xform 
    def xformPivot(self, pos, *args, **flags):
        if self.getApiTypeStr() == 'kTransform':
            cmds.xform(self.getFullName(), ws=True, rp=pos, sp=pos)
            return True
        raise Exception, "xformPivot will only work on Transforms"

    #flags is the mel flags that can be used on setAttr
    def getAttr(self, attr, **flags):
        val = cmds.getAttr(self.getFullName() + "." + attr, **flags)
        return val

    #flags is the mel flags that can be used on listAttr
    def listAttr(self, **flags):
        val = cmds.listAttr(self.getFullName(), **flags)
        return val

    def attributeExists(self, attr):
        return self.attributeQuery(attr, ex=True)

    def attributeQuery(self, attr, **flags):
        return cmds.attributeQuery(attr, node=self.getFullName(), **flags)

    def connect(self, otherNode, thisAttr, otherAttr):
        otherNode = DependNode(otherNode)
        currentLockStates = otherNode.lockAttributes([otherAttr], False)
        cmds.connectAttr(self.getFullName() + "." + thisAttr,
                         otherNode.getFullName() + "." + otherAttr,
                         f=True)
        otherNode.lockAttributes([otherAttr], currentLockStates)

    def disconnect(self, otherNode, thisAttr, otherAttr):
        otherNode = DependNode(otherNode)
        cmds.disconnectAttr(self.getFullName() + "." + thisAttr,
                         otherNode.getFullName() + "." + otherAttr)

    def listConnections(self, attr, **flags):
        return cmds.listConnections(self.getFullName() + "." + attr, **flags)

    def delete(self):
        cmds.delete(self.getFullName())

    def select(self):
        cmds.select(self.getFullName())

    #Returns DependNodeArray.
    def duplicate(self, n=None):
        sDupes = cmds.duplicate(self.getFullName(), rc=True)
        nodeArray = DependNodeArray(sDupes)
        if n:
            nodeArray[0].setName(findUniqueName(n))
        return nodeArray

class DependNodeArray(list):
    @classmethod
    def ls(cls, name="*", type=None):
        items = None
        if type:
            items = cmds.ls(name, type=type, r=True)
        else:
            items = cmds.ls(name, r=True)
        return DependNodeArray(items)

    def __init__(self, inItem_array=None):
        list.__init__(self)
        if not inItem_array:
            self = []

        elif (inItem_array.__class__==list) or\
            (inItem_array.__class__==DependNodeArray):
            for node in inItem_array:
                self.append(node)

        elif (inItem_array.__class__==OpenMaya.MObjectArray) or\
            (inItem_array.__class__==OpenMaya.MDagPathArray):
            for i in range(0, inItem_array.length()):
                self.append(inItem_array[i])

        else:
            self.append(inItem_array)

    def __contains__(self, node):
        for i in range(0, len(self)):
            if node.__eq__(self[i]):
                return True
        return False

    def __checkType__(self, node):
        if hasattr(node, "__class__") and \
        ((node.__class__==str) or (node.__class__==unicode)):
            return DependNode(node)
        elif hasattr(node, "__class__") and isinstance(node, DependNode):
            return node
        elif hasattr(node, "__class__") and issubclass(node.__class__, DependNode):
            return node
        elif hasattr(node, "__class__") and isinstance(node, DependNodeArray):
            return node
        elif hasattr(node, "__class__") and issubclass(node.__class__, DependNodeArray):
            return node
        else:
            node = DependNode(node)
            return node

    def append(self, node):
        list.append(self, self.__checkType__(node))

    def insert(self, index, node):
        node = self.__checkType__(node)
        list.insert(index, node)

    def extend(self, node_nodeArray):
        if not node_nodeArray:
            return

        extArr = []
        if (node_nodeArray.__class__.__name__=="list") or\
         (node_nodeArray.__class__.__name__=="DependNodeArray"):
            for node in node_nodeArray:
                extArr.append(self.__checkType__(node))

        elif issubclass(node_nodeArray.__class__, DependNodeArray):
            for node in node_nodeArray:
                extArr.append(self.__checkType__(node))

        elif (node_nodeArray.__class__==OpenMaya.MObjectArray) or\
            (node_nodeArray.__class__==OpenMaya.MDagPathArray):
            for i in range(0, node_nodeArray.length()):
                self.append(node_nodeArray[i])

        else:
            extArr.append(self.__checkType__(node_nodeArray))
        list.extend(self, extArr)

    def removeDuplicates(self, id=None):
        if not len(self) > 1:
            return

        seen = DependNodeArray()
        result = DependNodeArray()
        for i in range(0, len(self)):
            if not seen.__contains__(self[i]):
                result.append(self[i])
            elif id:
                if not self[i].__eq__(DependNode(id)):
                    result.append(self[i])
            seen.append(self[i])

        self.clear()
        self.extend(result)

    def clear(self):
        cnt = len(self)-1
        for i in range(0, len(self)):
            self.pop(cnt)
            cnt -= 1

    def asFullNameArray(self):
        arr = []
        for node in self:
            arr.append(node.getFullName())
        return arr

    def asShortNameArray(self):
        arr = []
        for node in self:
            arr.append(node.getShortName())
        return arr

    def asPartialNameArray(self):
        arr = []
        for node in self:
            arr.append(node.getPartialName())
        return arr

    def asWorldTranslation(self):
        arr = []
        for node in self:
            arr.append(node.getWorldTranslation())
        return arr

    def delete(self):
        cmds.delete(self.asFullNameArray())

#Utilities++
def findUniqueName(nameToTest):
    list = OpenMaya.MSelectionList()
    try:
        OpenMaya.MGlobal.getSelectionListByName(nameToTest, list)
    except:
        return nameToTest

    if list.length():
        nums = re.search("([0-9]+)$", nameToTest)
        if nums:
            nums = int(nums.group(0))
            nums += 1
            split = re.split("([0-9]+)$", nameToTest)
            nameToTest = (split[0] + `nums`)
            return findUniqueName(nameToTest)
        else:
            nameToTest += "1"
            return findUniqueName(nameToTest)
    else:
        return nameToTest
#Utilities--

























