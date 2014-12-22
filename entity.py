#entity
import const
import random

marryGender = const.genders[0]
marryChance = 10

class Entity:
	___personality = ''
	___gender = ''
	___friends = []
	___spouse = None
	___pos = [0,0]
	___nearby = []


	def __init__(self,pos1,pos2,personality):
		print("new person")
		self.___gender = random.choice(const.genders)
		self.___pos[0] = pos1
		self.___pos[1] = pos2
		self.___personality = personality

	def __init__(self,width,height):
		print("new person")
		self.___personality = random.choice(const.personalities)
		self.___gender = random.choice(const.genders)
		self.___pos[0] = random.randint(0,width-1)
		self.___pos[1] = random.randint(0,height-1)

	def interact(self):
		for other in self.___nearby:
			if other:
				print(self.getPersonality() + " " + self.getGender() + " interacting with " + other.getPersonality() + " " + other.getGender())
				if self.canBeFriends(other):
					self.addFriend(other)
				if self.canBeSpouse(other):
					if self.getGender() == marryGender and random.randint(1,marryChance) == marryChance and not self.___spouse:
						other.setSpouse(self)
						self.setSpouse(other)

	def canBeFriends(self, other):
		return self.___personality.lower() == other.getPersonality().lower()

	def addFriend(self,other):
		self.___friends.append(other)

	def canBeSpouse(self, other):
		return (self.___personality == other.getPersonality()) and (self.___gender != other.getGender())

	def getGender(self):
		return self.___gender

	def setSpouse(self, other):
		self.___spouse = other

	def getPersonality(self):
		return self.___personality

	def perTick(self):
		self.moveRand()

	def moveRand(self):
		self.___pos[0] += random.randint(-1,1)
		self.___pos[1] += random.randint(-1,1)

	def getPos(self):
		return self.___pos

	def setPos(self, pos):
		self.___pos = pos
		print("a guy is at " + str(self.getPos()))

	def setNearby(self,array):
		self.___nearby = array



