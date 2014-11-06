#Skin weight I/O.
#2014.10.30.
#weihe@willdigi.com

import os
import cPickle as pickle
import json
from functools import partial

try:
    from PySide import QtGui
    from PySide import QtCore
    from shiboken import wrapInstance
except:
    from PyQt4 import QtGui
    from PyQt4 import QtCore
    from sip import wrapinstance as wrapInstance

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMayaAnim as OpenMayaAnim
import logging
logging.basicConfig(format='%(levelname)s: %(message)s')
import utils.utils as utils
reload(utils)

def getShape(node, intermediate=False):
    """Gets the shape from the specified node.

    @param[in] node Name of a transform or shape node.
    @param[in] intermediate True to get the intermediate shape, False to get the visible shape.
    @return The name of the desired shape node"""
    if cmds.nodeType(node) == 'transform':
        shapes = cmds.listRelatives(node, shapes=True, path=True)
        if not shapes:
            shapes = []
        for shape in shapes:
            isIntermediate = cmds.getAttr('%s.intermediateObject' % shape)
            # Sometimes there are left over intermediate shapes that are not used so
            # check the connections to make sure we get the one that is used.
            if intermediate and isIntermediate and cmds.listConnections(shape, source=False):
                return shape
            elif not intermediate and not isIntermediate:
                return shape
        if shapes:
            return shapes[0]
    elif cmds.nodeType(node) in ['mesh', 'nurbsCurve', 'nurbsSurface']:
        return node
    return None


def getMayaWindow():
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QtGui.QMainWindow)


def show():
    dialog = SkinIODialog(getMayaWindow())
    dialog.show()



class SkinCluster(object):
    kFileExtension = '.skin'

    @classmethod
    def createAndImport(cls, filePath=None, shape=None):
        """Creates a skinCluster on the specified shape if one does not already exist
        and then import the weight data."""
        if not shape:
            try:
                shape = cmds.ls(sl=True)[0]
            except:
                raise RuntimeError('No shape selected')

        if filePath == None:
            startDir = cmds.workspace(q=True, rootDirectory=True)
            filePath = cmds.fileDialog2(dialogStyle=2, fileMode=1, startingDirectory=startDir,
                                        fileFilter='Skin Files (*%s)' % SkinCluster.kFileExtension)
        if not filePath:
            return
        if not isinstance(filePath, basestring):
            filePath = filePath[0]

        # Read in the file
        fh = open(filePath, 'rb')
        data = json.loads(fh.read())
        #data = pickle.load(fh)
        fh.close()

        # Make sure the vertex count is the same
        meshVertices = cmds.polyEvaluate(shape, vertex=True)
        importedVertices = len(data['blendWeights'])
        if meshVertices != importedVertices:
            raise RuntimeError('Vertex counts do not match. %d != %d' %
                    (meshVertices, importedVertices))

        # Check if the shape has a skinCluster
        if SkinCluster.getSkinCluster(shape):
            skinCluster = SkinCluster(shape)
        else:
            # Create a new skinCluster
            joints = data['weights'].keys()

            # Make sure all the joints exist
            unusedImports = []
            noMatch = set([SkinCluster.removeNamespaceFromString(x)
                          for x in cmds.ls(type='joint')])
            for j in joints:
                if j in noMatch:
                    noMatch.remove(j)
                else:
                    unusedImports.append(j)
            # If there were unmapped influences ask the user to map them
            if unusedImports and noMatch:
                mappingDialog = WeightRemapDialog(getMayaWindow())
                mappingDialog.setInfluences(unusedImports, noMatch)
                mappingDialog.exec_()
                for src, dst in mappingDialog.mapping.items():
                    # Swap the mapping
                    data['weights'][dst] = data['weights'][src]
                    del data['weights'][src]

            # Create the skinCluster with post normalization so setting the weights does not
            # normalize all the weights
            joints = data['weights'].keys()
            skinCluster = cmds.skinCluster(joints, shape, tsb=True, nw=2, n=data['name'])
            skinCluster = SkinCluster(shape)

        skinCluster.setData(data)
        print 'Imported %s' % filePath


    @classmethod
    def getSkinCluster(cls, shape):
        """Get the skinCluster node attached to the specified shape.

        @param[in] shape Shape node name
        @return The attached skinCluster name or None if no skinCluster is attached."""
        shape = getShape(shape)
        history = cmds.listHistory(shape, pruneDagObjects=True, il=2)
        if not history:
            return None
        skins = [x for x in history if cmds.nodeType(x) == 'skinCluster']
        if skins:
            return skins[0]
        return None


    @classmethod
    def export(cls, filePath=None, shape=None):
        skin = SkinCluster(shape)
        skin.exportSkin(filePath)


    @classmethod
    def removeNamespaceFromString(cls, value):
        """Removes namespaces from a string.

        Changes NAMESPACE:joint1|NAMESPACE:joint2 to
                joint1|joint2

        @param[in] String name with a namespace.
        @return The name without the namespaces"""
        tokens = value.split('|')
        result = ''
        for i, token in enumerate(tokens):
            if i > 0:
                result += '|'
            result += token.split(':')[-1]
        return result


    def __init__(self, shape=None):
        """Constructor"""
        if not shape:
            try:
                shape = cmds.ls(sl=True)[0]
            except:
                raise RuntimeError('No shape selected')

        self.shape = getShape(shape)
        if not self.shape:
            raise RuntimeError('No shape connected to %s' % shape)

        # Get the skinCluster node attached to the shape
        self.node = SkinCluster.getSkinCluster(shape)
        if not self.node:
            raise ValueError('No skinCluster attached to %s' % self.shape)

        # Get the skinCluster MObject
        selectionList = OpenMaya.MSelectionList()
        selectionList.add(self.node)
        self.mobject = OpenMaya.MObject()
        selectionList.getDependNode(0, self.mobject)
        self.fn = OpenMayaAnim.MFnSkinCluster(self.mobject)
        self.data = {
                'weights' : {},
                'blendWeights' : [],
                'name' : self.node,
                }


    def gatherData(self):
        dagPath, components = self.__getGeometryComponents()
        self.gatherInfluenceWeights(dagPath, components)
        self.gatherBlendWeights(dagPath, components)

        for attr in ['skinningMethod', 'normalizeWeights']:
            self.data[attr] = cmds.getAttr('%s.%s' % (self.node, attr))


    def gatherInfluenceWeights(self, dagPath, components):
        """Gathers all the influence weights"""
        weights = self.__getCurrentWeights(dagPath, components)

        influencePaths = OpenMaya.MDagPathArray()
        numInfluences = self.fn.influenceObjects(influencePaths)
        numComponentsPerInfluence = weights.length() / numInfluences
        for ii in range(influencePaths.length()):
            influenceName = influencePaths[ii].partialPathName()
            # We want to store the weights by influence without the namespace so it is easier
            # to import if the namespace is different
            influenceWithoutNamespace = SkinCluster.removeNamespaceFromString(influenceName)
            self.data['weights'][influenceWithoutNamespace] = \
                    [weights[jj*numInfluences+ii] for jj in range(numComponentsPerInfluence)]


    def gatherBlendWeights(self, dagPath, components):
        """Gathers the blendWeights"""
        weights = OpenMaya.MDoubleArray()
        self.fn.getBlendWeights(dagPath, components, weights)
        self.data['blendWeights'] = [weights[i] for i in range(weights.length())]


    def __getGeometryComponents(self):
        # Get dagPath and member components of skinned shape
        fnSet = OpenMaya.MFnSet(self.fn.deformerSet())
        members = OpenMaya.MSelectionList()
        fnSet.getMembers(members, False)
        dagPath = OpenMaya.MDagPath()
        components = OpenMaya.MObject()
        members.getDagPath(0, dagPath, components)
        return dagPath, components


    def __getCurrentWeights(self, dagPath, components):
        """Get the current weight array"""
        weights = OpenMaya.MDoubleArray()
        util = OpenMaya.MScriptUtil()
        util.createFromInt(0)
        pUInt = util.asUintPtr()
        self.fn.getWeights(dagPath, components, weights, pUInt);
        return weights


    def exportSkin(self, filePath=None):
        """Exports the skinCluster data to disk.

        @param[in] filePath File path"""
        if filePath == None:
            startDir = cmds.workspace(q=True, rootDirectory=True)
            filePath = cmds.fileDialog2(dialogStyle=2, fileMode=0, startingDirectory=startDir,
                                        fileFilter='Skin Files (*%s)' % SkinCluster.kFileExtension)
        if not filePath:
            return
        filePath = filePath[0]
        if not filePath.endswith(SkinCluster.kFileExtension):
            filePath += SkinCluster.kFileExtension

        self.gatherData()

        fh = open(filePath, 'wb')

        data = json.dumps(self.data, sort_keys=True, indent=2)
        fh.write(data)
        #pickle.dump(self.data, fh, pickle.HIGHEST_PROTOCOL)
        fh.close()
        print 'Exported skinCluster (%d influences, %d vertices) %s' % (
                len(self.data['weights'].keys()), len(self.data['blendWeights']), filePath)


    def setData(self, data):
        """Sets the data and stores it in the Maya skinCluster node.

        @param[in] data Data dictionary"""
        self.data = data

        dagPath, components = self.__getGeometryComponents()
        self.setInfluenceWeights(dagPath, components)
        self.setBlendWeights(dagPath, components)

        for attr in ['skinningMethod', 'normalizeWeights']:
            cmds.setAttr('%s.%s' % (self.node, attr), self.data[attr])


    def setInfluenceWeights(self, dagPath, components):
        """Sets all the influence weights"""
        weights = self.__getCurrentWeights(dagPath, components)
        influencePaths = OpenMaya.MDagPathArray()
        numInfluences = self.fn.influenceObjects(influencePaths)
        numComponentsPerInfluence = weights.length() / numInfluences

        # Keep track of which imported influences aren't used
        unusedImports = []

        # Keep track of which existing influences don't get anything imported
        noMatch = [influencePaths[ii].partialPathName() for ii in range(influencePaths.length())]

        for importedInfluence, importedWeights in self.data['weights'].items():
            for ii in range(influencePaths.length()):
                influenceName = influencePaths[ii].partialPathName()
                influenceWithoutNamespace = SkinCluster.removeNamespaceFromString(influenceName)
                if influenceWithoutNamespace == importedInfluence:
                    # Store the imported weights into the MDoubleArray
                    for jj in range(numComponentsPerInfluence):
                        weights.set(importedWeights[jj], jj*numInfluences+ii)
                    noMatch.remove(influenceName)
                    break
            else:
                unusedImports.append(importedInfluence)

        if unusedImports and noMatch:
            mappingDialog = WeightRemapDialog(getMayaWindow())
            mappingDialog.setInfluences(unusedImports, noMath)
            mappingDialog.exec_()
            for src, dst in mappingDialog.mapping.items():
                for ii in range(influencePaths.length()):
                    if influencePaths[ii].partialPathName() == dst:
                        for jj in range(numComponentsPerInfluence):
                            weights.set(self.data['weights'][src][jj], jj*numInfluences+ii)
                        break


        influenceIndices = OpenMaya.MIntArray(numInfluences)
        for ii in range(numInfluences):
            influenceIndices.set(ii, ii)
        self.fn.setWeights(dagPath, components, influenceIndices, weights, False);


    def setBlendWeights(self, dagPath, components):
        """Set the blendWeights"""
        blendWeights = OpenMaya.MDoubleArray(len(self.data['blendWeights']))
        for i, w in enumerate(self.data['blendWeights']):
            blendWeights.set(w, i)
        self.fn.setBlendWeights(dagPath, components, blendWeights)


class WeightRemapDialog(QtGui.QDialog):


    def __init__(self, parent=None):
        super(WeightRemapDialog, self).__init__(parent)
        self.setWindowTitle('Remap Weights')
        self.setObjectName('remapWeightsUI')
        self.setModal(True)
        self.resize(600, 400)
        self.mapping = {}

        mainVbox = QtGui.QVBoxLayout(self)

        label = QtGui.QLabel('The following influences have no corresponding influence from the ' \
                             'imported file.  You can either remap the influences or skip them.')
        label.setWordWrap(True)
        mainVbox.addWidget(label)

        hbox = QtGui.QHBoxLayout()
        mainVbox.addLayout(hbox)

        # The existing influences that didn't have weight imported
        vbox = QtGui.QVBoxLayout()
        hbox.addLayout(vbox)
        vbox.addWidget(QtGui.QLabel('Unmapped influences'))
        self.existingInfluences = QtGui.QListWidget()
        vbox.addWidget(self.existingInfluences)

        vbox = QtGui.QVBoxLayout()
        hbox.addLayout(vbox)
        vbox.addWidget(QtGui.QLabel('Available imported influences'))
        scrollArea = QtGui.QScrollArea()
        widget = QtGui.QScrollArea()
        self.importedInfluenceLayout = QtGui.QVBoxLayout(widget)
        vbox.addWidget(widget)

        hbox = QtGui.QHBoxLayout()
        mainVbox.addLayout(hbox)
        hbox.addStretch()
        btn = QtGui.QPushButton('Ok')
        btn.released.connect(self.accept)
        hbox.addWidget(btn)


    def setInfluences(self, importedInfluences, existingInfluences):
        infs = list(existingInfluences)
        infs.sort()
        self.existingInfluences.addItems(infs)
        width = 200
        for inf in importedInfluences:
            row = QtGui.QHBoxLayout()
            self.importedInfluenceLayout.addLayout(row)
            label = QtGui.QLabel(inf)
            row.addWidget(label)
            toggleBtn = QtGui.QPushButton('>')
            toggleBtn.setMaximumWidth(30)
            row.addWidget(toggleBtn)
            label = QtGui.QLabel('')
            label.setMaximumWidth(width)
            label.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
            row.addWidget(label)
            toggleBtn.released.connect(partial(self.setInfluenceMapping, src=inf, label=label))
        self.importedInfluenceLayout.addStretch()


    def setInfluenceMapping(self, src, label):
        selectedInfluence = self.existingInfluences.selectedItems()
        if not selectedInfluence:
            return
        dst = selectedInfluence[0].text()
        label.setText(dst)
        self.mapping[src] = dst
        # Remove the item from the list
        index = self.existingInfluences.indexFromItem(selectedInfluence[0])
        item = self.existingInfluences.takeItem(index.row())
        del item


class SkinIODialog(QtGui.QDialog):


    def __init__(self, parent=None):
        super(SkinIODialog, self).__init__(parent)
        self.setWindowTitle('Skin IO')
        self.setObjectName('skiniowidget')
        self.setModal(False)
        self.setFixedSize(200, 80)

        vbox = QtGui.QVBoxLayout(self)
        btn = QtGui.QPushButton('Export')
        btn.released.connect(SkinCluster.export)
        vbox.addWidget(btn)
        btn = QtGui.QPushButton('Import')
        btn.released.connect(SkinCluster.createAndImport)
        vbox.addWidget(btn)
"""
Example for using.     
SkinCluster.export()
SkinCluster.createAndImport()
"""
