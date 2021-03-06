from random import seed, uniform
import numpy as np
import collision_detection as cd
import RRT_algorithm as rrt
import time


def init_room(width=30, height=20, n_obst=20, rng_seed=None):
    
    # Init
    seed(rng_seed)
    wall_thk = 0.5
    obstacles = []  
    
    # Walls
    obstacles.append(np.array([[0, 0], [0, wall_thk], [width, wall_thk], [width, 0]]))
    obstacles.append(np.array([[0, wall_thk], [0, height], [wall_thk, height], [wall_thk, wall_thk]]))
    obstacles.append(np.array([[wall_thk, height], [width, height], [width, height-wall_thk], [wall_thk, height-wall_thk]]))
    obstacles.append(np.array([[width, height-wall_thk], [width, wall_thk], [width-wall_thk, wall_thk], [width-wall_thk, height-wall_thk]]))
    
    # Extra wall in middle
    #obstacles.append(np.array([[width/2, wall_thk], [width/2, height-wall_thk-14], [width/2+wall_thk, height-wall_thk-14], [width/2+wall_thk, wall_thk]]))
    
    # Start - the starting robot configuration. Random y pos on LHS of room, with 0 joint angles
    startPos = np.array([uniform(wall_thk+2.5, wall_thk+7), uniform(wall_thk+2.5, height-wall_thk-2.5)])
    start = np.hstack((startPos, np.array([0.0,0.0,0.0])))
    # Goal - the goal for the end effector (px, py, theta)
    goal_end = np.array([uniform(width-wall_thk-2.5, width-wall_thk-7), uniform(wall_thk+2.5, height-wall_thk-2.5), uniform(0, 2*np.pi)])
    
    # Obstacles
    for i in range(n_obst):
        
        # New random poly 
        a = uniform(2*wall_thk, width-2*wall_thk)
        b = uniform(2*wall_thk, height-2*wall_thk)
        margin=1.5
        x1 = uniform(a-2, a)
        y1 = uniform(b-2,min(b-2+margin*abs(x1-a),b))
        x2 = uniform(a-2, a)
        y2 = uniform(max(b+2-margin*abs(x2-a),b), b+2)
        x3 = uniform(a, a+2)
        y3 = uniform(max(b+2-margin*abs(x3-a),b), b+2)
        x4 = uniform(a, a+2)
        y4 = uniform(b-2, min(b-2+margin*abs(x4-a),b))
        poly1 = np.array([[x1, y1], [x2, y2], [x3, y3], [x4, y4]])
        
        # Pre emptively add new poly to list
        obstacles.append(poly1)
        polyClear = True
        
        # Check whether too close to start/end point
        # Obstacles should be completely clear of arm range in the start location
        tooClose = cd.checkPolyCircleIntersecting(poly1, start[0], start[1], 2.5) 
        # No obstacles within 0.5m of goal. Selected goal config will need to be checked to ensure it doesn't collide
        tooClose = tooClose or cd.checkPolyCircleIntersecting(poly1, goal_end[0], goal_end[1], 1) 
        if tooClose:
            # If too close, poly should be discarded
            polyClear = False

        # For every other obstacle in current list, check for collisions
        l = len(obstacles)-1     
        for j in range(l):
            poly2 = obstacles[j]
            intersecting = cd.checkPolysIntersecting(poly1, poly2)
            if intersecting:
                # If collision detected, poly should be discarded, and stop checking further
                polyClear = False
                break
        
        # Remove from the list if location not clear
        if polyClear == False:
            obstacles.pop()

    return start, goal_end, obstacles


# Initialise room with obstacles and start/goal
room_width = 30
room_height = 20
start, goal_end, obstacles = init_room(room_width, room_height, n_obst=20, rng_seed=10)

# Run RRT
start_time = time.time()
#
#
# Choose RRT or RRT* based on which line runs (below):
n_samples = 200
NodeList = rrt.RRT(start, goal_end, room_width, room_height, n_samples, obstacles,debug=True)
#NodeList = rrt.RRT_star(start, goal_end, room_width, room_height, n_samples, obstacles,debug=True)
#
#
end_time = time.time()
elapsed_time = end_time - start_time
print("Elapsed time: ", elapsed_time)


    
    
    
    
