#!/usr/bin/env python
import simpy
from random import random, seed, randint
# seed(21)

MAX_EV_CAPACITY=16.5  # kWh
MAX_EV_RANGE=20       # km
CHARGING_SPEED=3.6    # kWh per hour
NUM_EVS=2

class VPP:
    def __init__(self, env, name):
        self.capacity = simpy.Container(env, init=0, capacity=MAX_EV_CAPACITY*NUM_EVS)
        self.env = env
        self.name = name
        self.mon_proc = env.process(self.monitor_capacity(env))

    def log(self, message):
        print('[%s] - VPP %s [%.2f/%.2f]'% (self.env.now, self.name, self.capacity.level, self.capacity.capacity), message)
    
    def monitor_capacity(self, env):
        level = 0
        while True:
            if level != self.capacity.level:
                self.log('has changed %.2f capacity' % (self.capacity.level - level))
                level = self.capacity.level
                
            yield env.timeout(1)

class EV:
    def __init__(self, env, vpp, name):
        self.battery = simpy.Container(env, init=MAX_EV_CAPACITY, capacity=MAX_EV_CAPACITY)
        self.drive_proc = env.process(self.drive(env, vpp, name))
        self.env = env
        self.name = name
        
        self.state = 'I'
    
    def log(self, message):
        print('[%s] - EV %s [%.2f/%.2f|%s]'% (self.env.now, self.name, self.battery.level, self.battery.capacity, self.state), message)
    
    def plugged_in(self):
        return random() <= 0.3

    def drive(self, env, vpp, name):
        while True:
            # Charging
            if self.state == 'C':
                self.log('is at a charging station')
                # Add capacity from VPP
                yield vpp.capacity.put(self.battery.level)
                idle_time = randint(5, 20) # minutes

                for i in range(idle_time):
                    if self.battery.level < self.battery.capacity - (CHARGING_SPEED / 60):
                        self.log('is charging')
                        yield self.battery.put(CHARGING_SPEED / 60)
                        yield vpp.capacity.put(CHARGING_SPEED / 60)
                        yield env.timeout(1)
                    else:
                        self.log('is already fully charged')
                        yield env.timeout(1)
                
                yield vpp.capacity.get(self.battery.level)
                self.state = 'D'
            
            # Driving
            elif self.state == 'D':
                avg_speed = randint(30, 60) # km/h
                trip_distance = randint(5, 10) # km
                trip_time = int(trip_distance / avg_speed * 60) # minutes
                trip_capacity = MAX_EV_CAPACITY / MAX_EV_RANGE * trip_distance # kWh
                
                if self.battery.level > trip_capacity:
                    self.log('starts driving')
                    yield env.timeout(trip_time)
                    yield self.battery.get(trip_capacity)
                    self.log('drove %d kilometers in %d minutes and consumed %.2f kWh'% (trip_distance, trip_time, trip_capacity))
                else:
                    self.log('does not have enough battery for the planned trip')
                
                self.state = 'I'

            # Idle
            elif self.state == 'I':
                if self.plugged_in():
                    self.state = 'C'
                else:
                    self.log('is idle')
                    idle_time = randint(5, 20) # minutes
                    yield env.timeout(idle_time)
                    self.log('was idle for %d minutes' % idle_time)
                    self.state = 'D'
    
                
def car_generator(env, vpp):
    for i in range(NUM_EVS):
        # print('[%s] - EV %s joined the fleet' % (env.now, i))
        ev = EV(env, vpp, i)
        yield env.timeout(0)


env = simpy.Environment()
vpp = VPP(env, 1)
car_gen = env.process(car_generator(env, vpp))
env.run(200)
