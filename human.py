#PERSON
import const
import random

marryGender = const.genders[0]
marryChance = 10

class Person(entity):

	def __init__(self,pos1,pos2,personality):
		Base.__init__(self,pos1,pos2)
		self._gender = random.choice(const.genders)
		self._personality = personality
		self._friends = []
		self._canSee = []
		self._spouse = None

	def __init__(self,width,height):
		Base.__init__(self,width,height)
		self._personality = random.choice(const.personalities)
		self._gender = random.choice(const.genders)
		self._canSee = []
		self._spouse = None

	def interact(self):
		for other in self._nearby:
			if other is Person:
				print(self.getPersonality() + " " + self.getGender() + " interacting with " + other.getPersonality() + " " + other.getGender())
				if self.canBeFriends(other) and not(other in self._friends):
					self.addFriend(other)
				if other in self._friends and self.canBeSpouse(other) and self.getGender() == marryGender and random.randint(1,marryChance) == marryChance and not self._spouse:
						other.setSpouse(self)
						self.setSpouse(other)

	def perTick(self):
		self.interact()
		target = None
		for e in canSee:
			if e is Person and not target:
				target = e
			if self.getGender() != marryGender and e is self._spouse:
				target = e
				break;
		if target:
			self.moveToward(target)
		else:
			self.moveRand()

	def moveRand(self):
		self._pos[0] += random.randint(-1,1)
		self._pos[1] += random.randint(-1,1)

	def moveToward(self,entity):
		pos = entity.getPos()
		deltaX = self._pos[0] - pos[0]
		deltaY = self._pos[1] - pos[1]
		if abs(deltaX) >= abs(deltaY):
			self._pos[0] += (deltaX/abs(deltaX))
		if abs(deltaX) <= abs(deltaY):
			self._pos[1] += (deltaY/abs(deltaY))

	def setCanSee(self,array):
		self._canSee = array

	def canBeFriends(self, other):
		return self._personality.lower() == other.getPersonality().lower()

	def canBeSpouse(self, other):
		return (self._personality == other.getPersonality()) and (self._gender != other.getGender())

	def addFriend(self,other):
		self._friends.append(other)

	def setSpouse(self, other):
		self._spouse = other

	def getGender(self):
		return self._gender

	def getPersonality(self):
		return self._personality
