from tkinter import *
import math
import random
import time
import matplotlib.pyplot as plt

WORLD_WIDTH = 960
WORLD_HEIGHT = 640
ENERGY_FACTOR = 0.001
FOOD_TO_ENERGY_FACTOR = 0.05
FOOD_COST_SPEED = 20

class GameObject:
    def getDistance(self, other):
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5

    def moveToward(self, other, distance):
        if self.getDistance(other) <= distance:
            self.x = other.x
            self.y = other.y
        else:
            angle = math.atan2(other.y-self.y, other.x-self.x)
            self.x += distance * math.cos(angle) * distance
            self.y += distance * math.sin(angle) * distance
            self.checkBoundary()

    def moveAway(self, other, distance):
        angle = math.atan2(other.y-self.y, other.x-self.x)
        self.x -= distance * math.cos(angle) * distance
        self.y -= distance * math.sin(angle) * distance
        self.checkBoundary()

    def checkBoundary(self):
        if self.x < 0:
            self.x += WORLD_WIDTH
        elif self.x > WORLD_WIDTH-1:
            self.x -= WORLD_WIDTH
        if self.y < 0:
            self.y += WORLD_HEIGHT
        elif self.y > WORLD_HEIGHT-1:
            self.y -= WORLD_HEIGHT

    def rest(self):
        self.state = "walk"
        self.target = Point()

    def update(self, deltat):
        if self.mateFreeze > 0:
            self.mateFreeze -= deltat

        self.life -= deltat
        if self.life < 0:
            self.dead = True
            return

        if self.freeze > 0:
            self.freeze -= deltat
            self.energy = min(100, self.energy + self.food * deltat * FOOD_TO_ENERGY_FACTOR)
        else:
            if self.state == "run":
                if not self.target or self.target.dead or self.getDistance(self.target) > self.quitRange or self.getDistance(self.target) < 1:
                    self.rest()
                else:
                    cost = self.weight * self.runSpeed * deltat * ENERGY_FACTOR
                    if self.energy > cost:
                        self.moveToward(self.target, deltat * self.runSpeed * (0.5+self.food/200))
                        self.energy -= cost
                    else:
                        self.rest()

            if self.state == "runaway":
                if not self.target or self.target.dead or self.getDistance(self.target) > self.safeRange:
                    self.rest()
                else:
                    cost = self.weight * self.runSpeed * deltat * ENERGY_FACTOR
                    if self.energy > cost and self.target and not self.target.dead:
                        self.moveAway(self.target, deltat * self.runSpeed * (0.5+self.food/200))
                        self.energy -= cost
                    else:
                        self.rest()

            if self.state == "walk":
                self.energy = min(100, self.energy + self.food * deltat * FOOD_TO_ENERGY_FACTOR)
                if self.getDistance(self.target) > 1:
                    self.moveToward(self.target, deltat * self.walkSpeed * (0.5+self.food/200))
                else:
                    self.target = Point()

        if isinstance(self, Wolf):
            self.food -= FOOD_COST_SPEED * deltat
        elif isinstance(self, Sheep):
            self.food += (40 / (1 + self.neighbor) - FOOD_COST_SPEED) * deltat
            self.food = min(100, self.food)
        if self.food < 0:
            self.dead = True

class Point(GameObject):
    def __init__(self, x = None, y = None):
        if x == None:
            self.x = random.randint(0, WORLD_WIDTH)
        else:
            self.x = x
        if y == None:
            self.y = random.randint(0, WORLD_HEIGHT)
        else:
            self.y = y

class Wolf(GameObject):
    def __init__(self, **kwargs):
        self.walkSpeed = 40
        self.runSpeed = 100
        self.weight = 40
        self.energy = 100
        self.food   = 100
        self.mateRate = 0.35
        self.mateGap = 2
        self.alertRange = 75
        self.quitRange = 125
        self.eatThreshold = 65
        self.eatWolfThreshold = 30
        self.life = 60

        self.x = random.randrange(0, WORLD_WIDTH)
        self.y = random.randrange(0, WORLD_HEIGHT)
        self.state = "walk"
        self.target = Point()
        self.freeze = 0
        self.mateFreeze = 2
        self.dead = False

        for kw, val in kwargs.items():
            if hasattr(self, kw):
                setattr(self, kw, val)

    def eat(self, sheep):
        if sheep.dead == False:
            sheep.dead = True
            self.food = min(self.food+sheep.food, 100)

    def fight(self, wolf):
        if wolf.dead == False:
            if self.food >= wolf.food:
                wolf.dead = True
                self.food = min(self.food + wolf.food, 100)
            else:
                self.dead = True
                wolf.food = min(wolf.food + self.food, 100)

    def chase(self, sheep):
        if self.state != "run":
            self.state = "run"
            self.target = sheep
        else:
            if self.getDistance(self.target) > self.getDistance(sheep):
                self.target = sheep

    def mate(self, wolf):
        newWolf = None
        if self.mateFreeze <= 0 and wolf.mateFreeze <= 0 and random.uniform(0,1) < self.mateRate:
            newWolf = Wolf()
            features = {}
            for feature in ["walkSpeed", "runSpeed", "weight", "alertRange", "quitRange"]:
                setattr(newWolf, feature, (getattr(self, feature) + getattr(wolf, feature))/2 * random.uniform(0.9,1.1))
            newWolf.food = (self.food + wolf.food)/2
            newWolf.x = self.x + random.uniform(-100, 100)
            newWolf.y = self.y + random.uniform(-100, 100)
            newWolf.checkBoundary()

            self.mateFreeze = self.mateGap
            wolf.mateFreeze = wolf.mateGap
        return newWolf

    def __repr__(self):
        return "Walk Speed: {}, Run Speed: {}, Weight: {}, Alert Range: {}, Quit Range: {}, Mate Rate: {}, Mate Gap: {}".format(self.walkSpeed, self.runSpeed, self.weight, self.alertRange, self.quitRange, self.mateRate, self.mateGap)



class Sheep(GameObject):
    def __init__(self, **kwargs):
        self.walkSpeed = 40
        self.runSpeed = 60
        self.weight = 40
        self.mateRate = 0.4
        self.mateGap = 1.5
        self.alertRange = 50
        self.safeRange = 80
        self.life = 40
        self.eatTime = 1

        self.x = random.randrange(0, WORLD_WIDTH)
        self.y = random.randrange(0, WORLD_HEIGHT)
        self.energy = 100
        self.food   = 100
        self.state = "walk"
        self.target = Point()
        self.freeze = 0
        self.mateFreeze = 1.5
        self.dead = False
        self.neighbor = 0

        for kw, val in kwargs.items():
            if hasattr(self, kw):
                setattr(self, kw, val)

    def avoid(self, wolf):
        self.state = "runaway"
        self.target = wolf

    def mate(self, sheep):
        newSheep = None
        if self.mateFreeze <= 0 and sheep.mateFreeze <= 0 and random.uniform(0,1) < self.mateRate:
            newSheep = Sheep()
            for feature in ["walkSpeed", "runSpeed", "weight", "alertRange", "safeRange"]:
                setattr(newSheep, feature, (getattr(self, feature) + getattr(sheep, feature))/2 * random.uniform(0.9,1.1))
            newSheep.food = (self.food + sheep.food) / 2
            newSheep.x = self.x + random.uniform(-100, 100)
            newSheep.y = self.y + random.uniform(-100, 100)
            newSheep.checkBoundary()

            self.mateFreeze = self.mateGap
            sheep.mateFreeze = sheep.mateGap
        return newSheep

    def __repr__(self):
        return "Walk Speed: {}, Run Speed: {}, Weight: {}, Alert Range: {}, Safe Range: {}, Mate Rate: {}, Mate Gap: {}".format(self.walkSpeed, self.runSpeed, self.weight, self.alertRange, self.safeRange, self.mateRate, self.mateGap)

class World:
    def __init__(self):
        self.width = 960
        self.height = 640
        self.framePerSec = 60
        self.currFrame = 0
        
        self.wolves = []
        self.sheep  = []
        self.newWolfNum = 0
        self.newSheepNum = 0
        self.tileWidth = 20
        self.tileHeight = 20
        self.tileWidthNum = int(self.width / self.tileWidth)
        self.tileHeightNum = int(self.height / self.tileHeight)
        self.wolfData = ""
        self.sheepData = ""
        self.wolfNum = []
        self.sheepNum = []

    def start(self):
        for i in range(30):
            self.wolves.append(Wolf())
        for i in range(150):
            self.sheep.append(Sheep())

    def posToTileId(self, x, y):
        ret = int(x/self.tileWidth) + int(y/self.tileHeight) * self.tileWidthNum
        if ret < 0 or ret >= self.tileWidthNum * self.tileHeightNum:
            return None
        return ret
    
    def putInTiles(self):
        self.tiles = [[] for i in range(self.tileWidthNum * self.tileHeightNum)]
        for w in self.wolves:
            self.tiles[self.posToTileId(w.x, w.y)].append(w)
        for s in self.sheep:
            self.tiles[self.posToTileId(s.x, s.y)].append(s)

    def maxDistObjs(self, gameObj, dist):
        minx = gameObj.x - dist
        maxx = gameObj.x + dist
        miny = gameObj.y - dist
        maxy = gameObj.y + dist
        tileIds = []
        x = minx
        while x <= maxx:
            y = miny
            while y <= maxy:
                tileId = self.posToTileId(x,y)
                if tileId:
                    tileIds.append(tileId)
                y += self.tileHeight
            x += self.tileWidth
        ret = []
        for tileId in tileIds:
            ret += self.tiles[tileId]
        return ret


    def refresh(self):
        self.currFrame += 1
        newWolfs = []
        newSheep = []
        self.putInTiles()
        for w in self.wolves:
            if w.food < w.eatThreshold:
                for obj in self.maxDistObjs(w, w.alertRange):
                    if isinstance(obj, Sheep):
                        dist = w.getDistance(obj)
                        if dist < 5:
                            w.eat(obj)
                        else:
                            if dist < w.alertRange:
                                w.chase(obj)
                    elif isinstance(obj, Wolf) and w != obj and obj.food < obj.eatWolfThreshold and w.food > obj.food:
                        dist = w.getDistance(obj)
                        if dist < 5:
                            w.fight(obj)
                        else:
                            if dist < w.alertRange:
                                w.chase(obj)
        for s in self.sheep:
            for obj in self.maxDistObjs(s, s.alertRange):
                dist = s.getDistance(obj)
                if isinstance(obj, Wolf):
                    if s.state == "runaway" and dist < s.getDistance(s.target):
                        s.avoid(obj)
                    elif s.state == "walk" and dist < s.alertRange:
                        s.avoid(obj)

        for w1 in self.wolves:
            for w2 in self.maxDistObjs(w1, 30):
                if isinstance(w2, Wolf) and w1 != w2 and w1.getDistance(w2) < 30 and w1.food > 70 and w2.food > 70:
                    child = w1.mate(w2)
                    if child:
                        self.newWolfNum += 1
                        newWolfs.append(child)

        for s1 in self.sheep:
            s1.neighbor = 0
            tileId = self.posToTileId(s1.x, s1.y)
            for s2 in self.maxDistObjs(s1, 30):
                if isinstance(s2, Sheep) and s1 != s2:
                    if s1.getDistance(s2) < 30 and s1.food > 50 and s2.food > 50:
                        child = s1.mate(s2)
                        if child:
                            self.newSheepNum += 1
                            newSheep.append(child)
                    if s1.getDistance(s2) < 25:
                        s1.neighbor += 1

        avrWolfData = {}
        for w in self.wolves:
            w.update(1/self.framePerSec)
            if not w.dead:
                newWolfs.append(w)
            for feature in ["walkSpeed", "runSpeed", "weight", "alertRange", "quitRange"]:
                if feature in avrWolfData:
                    avrWolfData[feature] += getattr(w, feature)
                else:
                    avrWolfData[feature] = getattr(w, feature)
        for feature in avrWolfData:
            avrWolfData[feature] /= len(self.wolves)


        avrSheepData = {}
        for s in self.sheep:
            s.update(1/self.framePerSec)
            if not s.dead:
                newSheep.append(s)
            for feature in ["walkSpeed", "runSpeed", "weight", "alertRange", "safeRange"]:
                if feature in avrSheepData:
                    avrSheepData[feature] += getattr(s, feature)
                else:
                    avrSheepData[feature] = getattr(s, feature)
        for feature in avrSheepData:
            avrSheepData[feature] /= len(self.sheep)

        self.wolfData = "Wolf ({newWolfNum}) | Walk Speed:{walkSpeed:.2f}, Run Speed: {runSpeed:.2f}, Weight: {weight:.2f}, Alert Range: {alertRange:.2f}, Quit Range: {quitRange:.2f}".format(newWolfNum=self.newWolfNum, **avrWolfData)
        self.sheepData = "Sheep ({newSheepNum}) | Walk Speed:{walkSpeed:.2f}, Run Speed: {runSpeed:.2f}, Weight: {weight:.2f}, Alert Range: {alertRange:.2f}, Safe Range: {safeRange:.2f}".format(newSheepNum=self.newSheepNum, **avrSheepData)

        self.wolves = newWolfs
        self.sheep = newSheep

        if self.currFrame % 60 == 0:
            self.wolfNum.append(len(self.wolves))
            self.sheepNum.append(len(self.sheep))

class Frame:
    def __init__(self, height = WORLD_HEIGHT, width = WORLD_WIDTH):
        self.root = Tk()
        self.strvar = StringVar()
        self.label = Label(self.root, textvariable=self.strvar)
        self.label.pack()
        self.canvas = Canvas(self.root, width = width, height = height)
        self.canvas.pack()
        self.button = Button(self.root, text="Show Figure", command=self.drawFigure)
        self.button.pack()
        self.game = World()

    def start(self):
        self.game.start()
        self.refresh()
        self.root.mainloop()

    def refresh(self):
        t1 = time.time()
        self.game.refresh()
        t2 = time.time()
        self.canvas.delete('all')
        self.drawGame()
        t3 = time.time()
        self.root.after(5, self.refresh)

    def drawGame(self):
        self.strvar.set(self.game.wolfData + "\n" + self.game.sheepData)
        for w in self.game.wolves:
            self.canvas.create_rectangle(w.x-5, w.y-5, w.x+5, w.y+5, fill="#{:02x}0000".format(int(w.food/100*255)))
        for s in self.game.sheep:
            self.canvas.create_rectangle(s.x-5, s.y-5, s.x+5, s.y+5, fill="#00{:02X}00".format(int(s.food/100*255)))

    def drawFigure(self):
        fig, ax1 = plt.subplots()
        t = range(len(self.game.wolfNum))
        ax1.plot(t, self.game.wolfNum, 'r')
        ax1.set_ylabel("Wolf", color='r')
        ax2 = ax1.twinx()
        ax2.plot(t, self.game.sheepNum, 'g')
        ax2.set_ylabel("Sheep", color='g')
        plt.show()


if __name__ == '__main__':
    f = Frame()
    f.start()

