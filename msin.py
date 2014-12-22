import threading
import world

def main():
	theWorld = world.World(500,500,20)
	threading.Timer(5.0, theWorld.perTick()).start()

if __name__ == "__main__":
    main()