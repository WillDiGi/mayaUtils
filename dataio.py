#Attributes export/import tools. 
#2014.10.30.
#weihe@willdigi.com

import cPickle as pickle
import maya.cmds as cmds
import maya.mel as mel
import tools.utils as utils
import json
reload(utils)

class AttributeData(object):
    dataFileExtension = '.data'

    def __init__(self):
        self.data = {}
        self.nodeList = cmds.ls(sl = True)
        cb=mel.eval('global string $gChannelBoxName; $temp=$gChannelBoxName;')

        self.attrList = cmds.channelBox(cb, q=True, sma=True)

    def gatherData(self):
        count = len(self.nodeList)
        if not self.nodeList:
            print 'Please select some nodes.'
            return
        elif not self.attrList:
            utils.progressStart('Exporting attributes from selection.', count)
            for node in self.nodeList:
                self.data[node] = {}
                channelList = cmds.listAttr(node, k=True)
                for attr in channelList:
                    self.data[node][attr] = cmds.getAttr(node+'.'+attr)
                utils.progressStep()
            utils.progressEnd()
        else:
            utils.progressStart('Exporting attributes from selection.', count)
            for node in self.nodeList:
                self.data[node] = {}
                for attr in self.attrList:
                    self.data[node][attr] = cmds.getAttr(node+'.'+attr)
                utils.progressStep()
            utils.progressEnd()

    def ExportData(self, filePath = None):
        """Exports the attribute data to disk.

        @param filePath File path"""
        if filePath == None:
            startDir = cmds.workspace(q=True, rootDirectory=True)
            filePath = cmds.fileDialog2(dialogStyle=2, fileMode=0, startingDirectory=startDir,
                                        fileFilter='Data Files (*%s)' % AttributeData.dataFileExtension)
        if not filePath:
            return
        filePath = filePath[0]
        if not filePath.endswith(AttributeData.dataFileExtension):
            filePath += AttributeData.dataFileExtension

        self.gatherData()
        fh = open(filePath, 'wb')
        
        #pickle.dump(self.data, fh, pickle.HIGHEST_PROTOCOL)
        #Old version, dump data with pickle.
        data = json.dumps(self.data, sort_keys=True, indent=2)
        fh.write(data)

        fh.close()
        print 'Exporting attribute data successed!'

    def ImportData(self, filePath = None):
        if filePath == None:
            startDir = cmds.workspace(q=True, rootDirectory=True)
            filePath = cmds.fileDialog2(dialogStyle=2, fileMode=1, startingDirectory=startDir,
                                        fileFilter='Data Files (*%s)' % AttributeData.dataFileExtension)
        if not filePath:
            return
        if not isinstance(filePath, basestring):
            filePath = filePath[0]
 
        fh = open(filePath, 'rb')
        data = json.loads(fh.read())
        #data = pickle.load(fh)
        #Old version, get data with pickle.
        fh.close()
        self.setData(data)

    def setData(self, data):
        """Apply the data to the nodes.

        @param data Data dictionary"""
        self.data = data
        count=len(self.data.keys())
        utils.progressStart('Exporting attributes from selection.', count)
        for key in self.data:
            node = key
            if cmds.objExists(node):
                for key in self.data[node]:
                    try:
                        cmds.setAttr((node + '.' + key), self.data[node][key])
                    except:
                        print (node + '.' + key + ' not exists.')
            else:
                print ('%s not exist.' %node)
            utils.progressStep()
        utils.progressEnd()
