from service.Physics import Physics
from service.Config import Config
from domain.Map import Map
from domain.GameObject import Bot

import math

class PhysicsEngine(Physics):
    """
    Methods used to apply physics to the game world

    Attributes:
        ruleset (Ruleset) : The set of rules needed to make objects behave
        map (Map) : The game world
        deltaTime (int) : Time in milliseconds since last tick
    """

    def __init__(self, ruleset, map_):
        self._ruleset = ruleset
        self._map = map_

        self.collisionsMaps = dict()
        self.collisionsMapsDividers = dict()


    def tick(self, deltaTime):
        """
        Update deltaTime
        """
        self.deltaTime = deltaTime

    def checkSpeed(self, bot, targetSpeed):
        """
        Checks whether a target speed is correct for a bot.

        Returns:
            targetSpeed (int) : A correct target speed for this bot.
        """
        maxSpeed = float(self._ruleset["SpeedMultiplier"]) * bot.getMaxSpeed()

        if targetSpeed > maxSpeed:
            targetSpeed = maxSpeed
        if targetSpeed < 0:
            targetSpeed = 0

        return targetSpeed

    def checkAngle(self, bot, targetX, targetY):
        """
        Checks whether a target point is correct for a bot.

        Returns:
            target_angle (int) : A correct target angle for this bot.
        """
        if (bot.x == targetX and bot.y == targetY):
            return bot.angle

        newAngle = Physics.getAngle( bot.x, bot.y, targetX, targetY)

        deltaAngle = newAngle - bot.angle

        if deltaAngle > 180:
            deltaAngle = deltaAngle - 360

        elif deltaAngle < -180:
            deltaAngle = 360 + deltaAngle
            
        maxAngle = float(self._ruleset["RotationMultiplier"]) * bot.maxRotate
        maxAngle = maxAngle * self.getDeltaTimeModifier()

        if abs(deltaAngle) > maxAngle :
            deltaAngle = maxAngle if deltaAngle > 0 else -maxAngle
            
        return (bot.angle + deltaAngle) % 360

    def getDeltaTimeModifier(self):
        """
        This is the multiplier for all physics operations, since deltaTime can be inconsistent.
        """
        return (self.deltaTime / (1000 / (30 * Config.TimeRate())))

    def checkCollision(self, collisionMap, x, y, targetX, targetY, capX, capY):
        """
        Checks whether a target's path collides with the map.

        Returns:
            position (int,int) : The first valid position.
        """
        
        dx = abs(targetX - x)
        dy = abs(targetY - y)

        currentX = x
        currentY = y

        lastX = x
        lastY = y

        n = int(1 + dx + dy)

        xInc = 1 if (targetX > x) else -1
        yInc = 1 if (targetY > y) else -1

        error = dx - dy

        dx *= 2
        dy *= 2
        
        for i in range(n, 0, -1):

            if capX != None and capY != None and capX == currentX and capY == currentY:
                return (lastX,lastY)
            
            if self.collisionsMaps[collisionMap][int(currentX // self.collisionsMapsDividers[collisionMap])][int(currentY // self.collisionsMapsDividers[collisionMap])]:
                return (lastX, lastY)

            lastX = currentX
            lastY = currentY

            if error > 0:
                currentX += xInc
                error -= dy
            elif error < 0:
                currentY += yInc
                error += dx
            elif error == 0:
                currentX += xInc
                currentY += yInc
                error -= dy
                error += dx
                n -= 1
                
        return (targetX, targetY)

    def viewBlocked(self, x, y, targetX, targetY):
        """
        Checks whether a line is obstruated by a solid block.

        Returns:
            blocked (bool) : True if blocked, False if not blocked
        """
        
        dx = abs(targetX - x)
        dy = abs(targetY - y)

        currentX = x
        currentY = y

        lastX = x
        lastY = y

        n = int(1 + dx + dy)

        xInc = 1 if (targetX > x) else -1
        yInc = 1 if (targetY > y) else -1

        error = dx - dy

        dx *= 2
        dy *= 2
        
        for i in range(n, 0, -1):
            
            if not self._map.blocks[int(currentX // self._map.BLOCKSIZE)][int(currentY // self._map.BLOCKSIZE)].transparent:
                return True

            lastX = currentX
            lastY = currentY

            if error > 0:
                currentX += xInc
                error -= dy
            elif error < 0:
                currentY += yInc
                error += dx
            elif error == 0:
                currentX += xInc
                currentY += yInc
                error -= dy
                error += dx
                n -= 1
                
        return False

    def createCollisionMap(self, name, padding):

        divider = 10 # 1 / round(Map.BLOCKSIZE / padding)
        self.collisionsMapsDividers[name] = divider

        collisionsMapPadding = int(padding // (Map.BLOCKSIZE // divider))
        collisionsMapWidth = int(self._map.blockWidth * divider)
        collisionsMapHeight = int(self._map.blockHeight * divider)

        self.collisionsMaps[name] = [[False for i in range(0,collisionsMapHeight)] for j in range(0,collisionsMapWidth)]

        blockSizeFactored = int(Map.BLOCKSIZE // divider)

        (x,y) = (0,0)
        for blockline in self._map.blocks:
            for block in blockline:
                if block.solid:
                    for rx in range(- collisionsMapPadding, blockSizeFactored + collisionsMapPadding):
                        for ry in range(- collisionsMapPadding, blockSizeFactored + collisionsMapPadding):
                            nx = int(x + rx)
                            ny = int(y + ry)
                            
                            if nx >= 0 and ny >= 0 and nx < collisionsMapWidth and ny < collisionsMapHeight:
                                # print("{} {}".format(nx,ny))
                                self.collisionsMaps[name][nx][ny] = True

                y += blockSizeFactored
            y = 0
            x += blockSizeFactored

    def sees(self, bot1, gameObject):
        if Physics.distance(bot1.x, gameObject.x, bot1.y, gameObject.y) > bot1.viewDistance:
            return False

        deltaAngle = Physics.getAngle(bot1.x,bot1.y,gameObject.x,gameObject.y) - bot1.angle

        if deltaAngle > 180:
            deltaAngle = deltaAngle - 360

        elif deltaAngle < -180:
            deltaAngle = 360 + deltaAngle
        if abs(deltaAngle) > bot1.fov:
            return False
            
        return self.viewBlocked(bot1.x, bot1.y, gameObject.x, gameObject.y)



    def getImpactPoint(self, x, y, targetX, targetY):
        dx = abs(targetX - x)
        dy = abs(targetY - y)

        currentX = x
        currentY = y

        lastX = x
        lastY = y

        n = int(1 + dx + dy)

        xInc = 1 if (targetX > x) else -1
        yInc = 1 if (targetY > y) else -1

        error = dx - dy

        dx *= 2
        dy *= 2
        
        for i in range(n, 0, -1):
            
            if self._map.blocks[int(currentX // self._map.BLOCKSIZE)][int(currentY // self._map.BLOCKSIZE)].solid:
                return (currentX, currentY)

            lastX = currentX
            lastY = currentY

            if error > 0:
                currentX += xInc
                error -= dy
            elif error < 0:
                currentY += yInc
                error += dx
            elif error == 0:
                currentX += xInc
                currentY += yInc
                error -= dy
                error += dx
                n -= 1
                
        return None


    def getShootedBot(self, x, y, angle, shootLength, bots):
        """
        Parameters:
            x (int) : x coord of origin
            y (int) : y coord of irigin
            ange (int) : angle of the shoot in degrees
            shootLength (int) : shoot length in model coord
            bots (list()) : list of bots
        Return :
            (bot, (x, y)): bot shooted, could be none, and the pos.
        """
 
        botsToCheck = list()

        for bot in bots:
            if Physics.angularDistance(angle, Physics.getAngle(x, y, bot.x, bot.y)) >= 90:
                continue

            distanceToBot = Physics.distance(x, y, bot.x, bot.y)
            if distanceToBot > shootLength:
                continue

            # Nearest point of impact
            impactPointX = x + math.cos(math.radians(angle)) * distanceToBot
            impactPointY = y + math.sin(math.radians(angle)) * distanceToBot 

            if bot.isIn(impactPointX, impactPointY):
                if self.getImpactPoint(x, y, impactPointX, impactPointY) == None:
                    # Can't stop here, an other bot can be nearest
                    botsToCheck.append((bot, (impactPointX, impactPointY)))


        n = len(botsToCheck)
        if n == 1:
            return botsToCheck[0]
        
        elif n > 1:
            minDist = Physics.distance(x, y, botsToCheck[0][1][0], botsToCheck[0][1][1])
            minBotIndex = 0

            for i in range(2, n):
                newDist = Physics.distance(x, y, botsToCheck[i][1][0], botsToCheck[i][1][1])

                if newDist < minDist:
                    minDist = newDist
                    minBotIndex = i
            
            return botsToCheck[minBotIndex]


        # else, must return impact point
        targetX = x + math.cos(math.radians(angle)) * shootLength
        targetY = y + math.sin(math.radians(angle)) * shootLength 
        

        impact = self.getImpactPoint(x, y, targetX, targetY)

        if impact == None:
            return (None, (targetX, targetY))
        
        return (None, impact)

