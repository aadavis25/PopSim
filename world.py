#world
import entity
import const


class World:
	___worldWidth = 500
	___worldHeight = 500
	___world = None
	___entities = []

	def __init__(self, width, height, people):
		self.___worldWidth = width
		self.___worldHeight = height
		self.___world = [[None for x in range(self.___worldHeight)] for y in range(self.___worldWidth)] 
		for i in range(people):
			thing = entity.Entity(self.___worldWidth,self.___worldHeight)
			self.___entities.append(thing)
			pos = thing.getPos()
			self.___world[pos[0]][pos[1]] = thing

	def checkProximities(self, thing):
		nearby = []
		pos = thing.getPos()
		x = pos[0]
		y = pos[1]
		for i in range(x-const.interactDist,x+const.interactDist):
			for j in range(y-const.interactDist,y+const.interactDist):
				if i!=x and j!=y:
					#j,i b/c 2d arrays index backwards
					nearby.append(self.___world[j][i])
		thing.setNearby(nearby)

	def interact(self,one,two):
		one.interact(two)
		two.interact(one)

	def entityUpdate(self,old,thing):
		self.___world[old[0]][old[1]] = None
		new = thing.getPos()
		if new[0] < 0:
			new[0] = 0
		elif new[0] > self.___worldWidth-1:
			new[0] = self.___worldWidth-1

		if new[1] < 0:
			new[1] = 0
		elif new[1] > self.___worldWidth-1:
			new[1] = self.___worldWidth-1
		thing.setPos(new)
		self.___world[new[0]][new[1]] = thing

	def perTick(self):
		for e in self.___entities:
			pos = e.getPos()
			e.perTick()
			self.entityUpdate(pos,e)
			self.checkProximities(e)
			e.interact()