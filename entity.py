#entity
import const
import random

class Entity:
	def __init__(self,pos1,pos2,personality):
		self._pos = [0,0]
		self._pos[0] = pos1
		self._pos[1] = pos2
		self._nearby = []

	def __init__(self,width,height):
		self._pos = [0,0]
		self._pos[0] = random.randint(0,width-1)
		self._pos[1] = random.randint(0,height-1)
		self._nearby = []

	def interact(self):
		pass

	def perTick(self):
		pass

	def getPos(self):
		return self._pos

	def setPos(self, pos):
		self._pos = pos
		print("a guy is at " + str(self.getPos()))

	def setNearby(self,array):
		self._nearby = array



