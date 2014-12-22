#world
import entity
import const


class World:
	_worldWidth = 500
	_worldHeight = 500
	_world = None
	_entities = []

	def __init__(self, width, height, people):
		self._worldWidth = width
		self._worldHeight = height
		self._world = [[None for x in range(self._worldHeight)] for y in range(self._worldWidth)] 
		for i in range(people):
			thing = entity.Entity(self._worldWidth,self._worldHeight)
			self._entities.append(thing)
			pos = thing.getPos()
			self._world[pos[0]][pos[1]] = thing

	def checkProximities(self, thing):
		nearby = []
		canSee = []
		pos = thing.getPos()
		x = pos[0]
		y = pos[1]
		for i in range(x-const.interactDist,x+const.interactDist):
			for j in range(y-const.interactDist,y+const.interactDist):
				if i!=x and j!=y:
					#j,i b/c 2d arrays index backwards
					nearby.append(self._world[j][i])

		for i in range(x-const.seeDist,x+const.seeDist):
			for j in range(y-const.seeDist,y+const.seeDist):
				if i!=x and j!=y:
					#j,i b/c 2d arrays index backwards
					canSee.append(self._world[j][i])

		thing.setCanSee(canSee)
		thing.setNearby(nearby)

	def entityUpdate(self,old,thing):
		self._world[old[0]][old[1]] = None
		new = thing.getPos()
		if new[0] < 0:
			new[0] = 0
		elif new[0] > self._worldWidth-1:
			new[0] = self._worldWidth-1

		if new[1] < 0:
			new[1] = 0
		elif new[1] > self._worldWidth-1:
			new[1] = self._worldWidth-1
		thing.setPos(new)
		self._world[new[0]][new[1]] = thing

	def perTick(self):
		for e in self._entities:
			pos = e.getPos()
			e.perTick()
			self.entityUpdate(pos,e)
			self.checkProximities(e)