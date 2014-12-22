import threading
import world

theWorld = world.World(500,500,20)
i = 0

def main():
	threading.Timer(5.0, main).start()
	global theWorld
	global i 
	i += 1
	print("\n\nTick " + str(i))
	theWorld.perTick()


if __name__ == "__main__":
    main()