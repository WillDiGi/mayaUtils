'''
Controller create/modify tools.
2014.08.29
weihe@willdigi.com
'''

import maya.cmds as cmds
transform = ['tx','ty','tz','rx','ry','rz','sx','sy','sz']
crvForm = {}
crvForm['diamond'] = [[(0,0,0.18112),
						(0.0311198,0.0311198,0.15),
						(0,0,0.11888),
						(-0.0311198,-0.0311198,0.15),
						(0,0,0.18112),
						(-0.0311198,0.0311198,0.15),
						(0,0,0.11888),
						(0.0311198,-0.0311198,0.15),
						(0,0,0.18112),
						(-0.0311198,0.0311198,0.15),
						(0.0311198,0.0311198,0.15),
						(0.0311198,-0.0311198,0.15),
						(-0.0311198,-0.0311198,0.15),
						(-0.0311198,0.0311198,0.15)],
						[0,1,2,3,4,5,6,7,8,9,10,11,12,13],
						False,
						1]
colors = {'black':1, 'dark_grey':2, 'grey':3, 'magenta':4, 'dark_blue':5,
						'blue':6, 'dark_green':7, 'dark_purple':8, 'purple':9, 'brown':10,
						'dark_brown':11, 'dark_red':12, 'red':13, 'green':14, 'medium_blue':15,
						'white':16, 'yellow':17, 'light_blue':18, 'light_green':19, 'pink':20,
						'light_brown':21, 'light_yellow':22, 'medium_green':23, 'default':0}

class CtrlCrv(object):
	def __init__(self, form, scale=1, color='red', name='M_body_ctrl'):
		self.name = name
		self.form = form
		self.scale = scale
		self.color = color

		self._cvs = crvForm[form][0]
		self._knots = crvForm[form][1]
		self._closed = crvForm[form][2]
		self._degree = crvForm[form][3]

	def createShape(self):
		#create new shape, init shape form and scale.
		#Create attributes, form and scale.
		self._cvs = crvForm[self.form][0]
		self._knots = crvForm[self.form][1]
		self._closed = crvForm[self.form][2]
		self._degree = crvForm[self.form][3]
		self.name = cmds.curve(per=self._closed,
								d=self._degree,
								p=self._cvs,
								k=self._knots,
								n=self.name)
		self.shape = cmds.listRelatives(self.name, s=True)[0]
		self.shape = cmds.rename(self.shape, self.name+'Shape')
		cmds.addAttr(self.shape, ln='scale', at='double', dv=1, keyable=True)
		cmds.addAttr(self.shape, ln='shape', dt='string', keyable=True)
		cmds.setAttr('%s.scale' %self.shape, self.scale)
		cmds.setAttr(type='string', '%s.shape' %self.shape, self.form)

	def changeShape(self, newform):
		if objExists(self.name):
			self.form = newform
			self._cvs = crvForm[self.form][0]
			self._knots = crvForm[self.form][1]
			self._closed = crvForm[self.form][2]
			self._degree = crvForm[self.form][3]
			newCrv = cmds.cruve(per=self._closed,
									d=self._degree,
									p=self._cvs,
									k=self._knots,
									n=self.name)
			newShape = cmds.listRelatives(newCrv, s=True)[0]
			cmds.parent(newCrv, self.name)
			for attribute in transform[:6]:
				cmds.setAttr('%s.%s' %(newCrv, attribute), 0)
			cmds.parent(newShape, self.name, r=True, s=True)
			cmds.delete(newCrv)
			cmds.delete(self.shape)
			cmds.rename(newShape, self.shape)
			cmds.addAttr(self.shape, ln='scale', at='double', dv=1, keyable=True)
			cmds.addAttr(self.shape, ln='shape', dt='string', keyable=True)
			cmds.setAttr('%s.scale' %self.shape, self.scale)
			cmds.setAttr(type='string', '%s.shape' %self.shape, self.form)
			slef.scale = 1
		else:
			print 'Curve is not created yet.'


	def getform(self):
		return self.form

	def changeColor(self, color = 'red'):
		if color in colors.keys():
			self.color = color
			index = colors[color]
			cmds.setAttr('%s.overrideEnabled' %self.shape, True)
			cmds.setAttr('%s.overrideColor' %self.shape, index)
		else:
			print 'Not a valid color option.'
			return False

	def getColor(self):
		return self.color

	def changeScale(self, newScale):
		pass

	def getScale(self):
		return self.scale

	def rename(self, name):
		if not cmds.objExists(name):
			try:
				self.name  = cmds.rename(self.name, name, ignoreShape=False)
				self.shape = cmds.rename(self.shape, name + "Shape")
			except:
				print "rename failed, skipping"
		else:
			print "Name already taken, can not rename control object"

	def add_offset(self):
		pass
