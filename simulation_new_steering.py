# -*- coding: utf-8 -*-
"""
Created on Fri Dec 17 15:04:38 2021

@author: Ricardo Valadas
"""

import numpy as np
from robotModel import Robot
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
#from RRT_algorithm import collisionBox
from shapely.geometry import Polygon,Point

def buildPolygons(r,link_centre,angle): 
    poly = []
    link_length = r.l[0]
    link_width = 0.2
    r = Robot()
    R = r.rotationMatrix(angle)
    poly.append(link_centre + R.dot(np.array([-link_length/2,link_width/2])))
    poly.append(link_centre + R.dot(np.array([link_length/2,link_width/2])))
    poly.append(link_centre + R.dot(np.array([link_length/2,-link_width/2])))
    poly.append(link_centre + R.dot(np.array([-link_length/2,-link_width/2])))
    return poly

def collisionBox(r,q): 
    mp,p_centre1,p_centre2,_,_ = r.ForwardKinematicsConfig(q)
    phi = q[2]
    # for the base it's a circle:
    base_box = Point(mp).buffer(0.6) # Create a circle centered at the centre of the mobile base with radius 0.5
    polygon1 = Polygon(buildPolygons(r,p_centre1,r.q[0]+phi))
    polygon2 = Polygon(buildPolygons(r,p_centre2,q[3]+q[4]+phi))
    
    return base_box,polygon1,polygon2

def integrateNumerically(r,mp_dot,phi_dot,dq,dt):
    # Integrate numerically:
    mp = r.mp.copy()
    phi = r.phi
    p = r.p.copy()
    theta = r.theta
    q = r.q.copy()
        
    mp += mp_dot*dt
    phi += phi_dot*dt
    q += dq[:]*dt
    p[0] = mp[0] + np.cos(phi)*(r.l[0]*np.cos(q[0]) + r.l[1]*np.cos(q[0]+q[1])) - np.sin(phi)*(r.l[0]*np.sin(q[0]) + r.l[1]*np.sin(q[0]+q[1]))
    p[1] = mp[1] + np.sin(phi)*(r.l[0]*np.cos(q[0]) + r.l[1]*np.cos(q[0]+q[1])) + np.cos(phi)*(r.l[0]*np.sin(q[0]) + r.l[1]*np.sin(q[0]+q[1]))
    theta = phi + q[0] + q[1]
    
    # Find position of the first joint (to plot)
    
    # Position of the first joint w.r.t the mobile base:
    p_em = np.array([r.l[0]*np.cos(q[0]),
                     r.l[0]*np.sin(q[0])])
    
    p_joint_1 = np.zeros(2)
    p_joint_1[0] = mp[0] + np.cos(phi)*p_em[0] - np.sin(phi)*p_em[1]
    p_joint_1[1] = mp[1] + np.sin(phi)*p_em[0] + np.cos(phi)*p_em[1]
    
    return mp,phi,q,p,theta,p_joint_1

def visualizeMovement(r):
    plt.cla()
    plt.xlim([-5,5])
    plt.ylim([-5,5])
    #plt.axis('equal')
    ax = plt.gca()
    # Plot the body of the robot:
    robotBody = plt.Circle((r.mp[0], r.mp[1]), r.R, color='r',fill=False)
    plt.plot([r.mp[0],r.mp[0]+0.8*np.cos(r.phi)],[r.mp[1],r.mp[1]+0.8*np.sin(r.phi)],color='k')
    ax.add_patch(robotBody)
    # Plot link 1:
    plt.plot([r.mp[0],r.p_joint_1[0]],[r.mp[1],r.p_joint_1[1]],color='orange')
    plt.plot(r.p_joint_1[0],r.p_joint_1[1],'.',color='k')
    
    # Plot link 2:
    plt.plot([r.p_joint_1[0],r.p[0]],[r.p_joint_1[1],r.p[1]],color='orange')
    # Add the gripper
    angle = np.rad2deg(r.theta)
    gripper = Arc((r.p[0]+0.25*np.cos(r.theta), r.p[1]+0.25*np.sin(r.theta)),0.5,0.5,angle+90,0,180, color='r')
    ax.add_patch(gripper)
    
    base_box,polygon1,polygon2 = collisionBox(r, np.array([r.mp[0],r.mp[1],r.phi,r.q[0],r.q[1]]))
    base_x,base_y = base_box.exterior.xy
    plt.plot(base_x,base_y,'g')
    x1,y1 = polygon1.exterior.xy
    x2,y2 = polygon2.exterior.xy
    
    poly1 = Polygon([np.array([1,1]),np.array([1,2]),np.array([2,2]),np.array([2,1])])
    poly2 = Polygon([np.array([3,3]),np.array([4,3]),np.array([4,4]),np.array([3,4])])
    poly3 = Polygon([np.array([7,7]),np.array([8,7]),np.array([8,8]),np.array([7,8])])
    
    
    plt.plot(poly1.exterior.xy[0],poly1.exterior.xy[1])
    plt.plot(poly2.exterior.xy[0],poly2.exterior.xy[1])
    plt.plot(poly3.exterior.xy[0],poly3.exterior.xy[1])
            
    plt.plot(x1,y1)
    plt.plot(x2,y2)
    plt.grid()
    plt.pause(0.001)
    

# Total time in seconds:
T = 2
dt = 0.005 # time step

plt.figure(1)
plt.pause(2)

# Initialise an instance of the robot class
r = Robot()
storeP = np.array([r.p])

# Define desired configuration to reach
q_des = np.array([-2,1,0,np.pi,np.pi/2])

# Define the direction to move the mobile robot to the desired position
vector = np.array([q_des[0]-r.mp[0],q_des[1]-r.mp[1]])/np.linalg.norm([q_des[0]-r.mp[0],q_des[1]-r.mp[1]])

# Initialise some variables:
error_i = 0
prev_error = 0

# PID CONTROLLER:
Kp = 50
Ki = 0.01
Kd = 0.001

# Trajectory part 1 - just rotate the phi to the desired direction of movement
for i in range(0,int(T/dt)):
    X_des = [r.mp[0],r.mp[1],np.arctan2(vector[1],vector[0]),r.q[0],r.q[1]]
    X = r.phi

    error = X_des[2] - X
    if abs(error)<0.01*np.pi/180:
        break
    error_d = (prev_error - error)
    error_i = error_i + error

    mp_dot = np.zeros(2)
    phi_dot = Kp*error + Ki*error_i*dt + Kd*error_d/dt
    dq = np.zeros(2)
    
    # Integrate numerically
    mp,phi,q,p,theta,p_joint_1 = integrateNumerically(r,mp_dot,phi_dot,dq,dt)
    
    r.Update(mp,phi,p,theta,q,dq,np.array([0.0,0.0]),p_joint_1) 
    
    # Visualize the movement
    visualizeMovement(r)
    storeP = np.append(storeP,[p],axis=0)
    # Save error for the derivative controller
    prev_error = error
    

# Trajectory part 2 - move the mobile robot in straight line
prev_error = [0,0]
error_i = [0,0]
for i in range(0,int(T/dt)):
    X_des = [q_des[0],q_des[1],r.phi,r.q[0],r.q[1]]
    X = np.array([r.mp[0],r.mp[1]])
    
    error = X_des[0:2] - X
    if (np.absolute(error)<0.0001).all():
        break
    error_d = (prev_error - error)
    error_i = error_i + error
    
    mp_dot = Kp*error + Ki*error_i*dt + Kd*error_d/dt
    phi_dot = 0
    dq = np.zeros(2)
    
    # Integrate numerically
    mp,phi,q,p,theta,p_joint_1 = integrateNumerically(r,mp_dot,phi_dot,dq,dt)
    
    r.Update(mp,phi,p,theta,q,dq,np.array([0.0,0.0]),p_joint_1) 
    
    # Visualize the movement
    visualizeMovement(r)
    storeP = np.append(storeP,[p],axis=0)
    # Save error for the derivative controller
    prev_error = error

# Trajectory part 3 - rotate phi and [q1,q2] to the desired values
prev_error = 0
error_i = 0    
for i in range(0,int(T/dt)):
    X_des = [r.mp[0],r.mp[1],q_des[2],q_des[3],q_des[4]]
    X = np.array([r.phi,r.q[0],r.q[1]])
    
    error = X_des[2:] - X
    if (np.absolute(error)<0.01*np.pi/180).all():
        break
    error_d = (prev_error - error)
    error_i = error_i + error
    
    mp_dot = np.zeros(2)
    Q_dot = Kp*error + Ki*error_i*dt + Kd*error_d/dt
    phi_dot = Q_dot[0]
    dq = Q_dot[1:]
    
    # Integrate numerically
    mp,phi,q,p,theta,p_joint_1 = integrateNumerically(r,mp_dot,phi_dot,dq,dt)
    
    r.Update(mp,phi,p,theta,q,dq,np.array([0.0,0.0]),p_joint_1) 
    
    # Visualize the movement
    visualizeMovement(r)
    storeP = np.append(storeP,[p],axis=0)
    # Save error for the derivative controller
    prev_error = error

# Plot the trajectory of the end-effector
plt.plot(storeP[:,0],storeP[:,1],'--')

# =============================================================================
# # Trajectory part 4 - rotate [q1,q2] to the desired values
# prev_error = [0,0]
# error_i = [0,0]    
# for i in range(0,int(T/dt)):
#     X_des = [r.mp[0],r.mp[1],r.phi,q_des[3],q_des[4]]
#     X = np.array([r.q[0],r.q[1]])
#     
#     error = X_des[3:] - X
#     if (np.absolute(error)<0.01*np.pi/180).all():
#         break
#     error_d = (prev_error - error)
#     error_i = error_i + error
#     
#     mp_dot = np.zeros(2)
#     phi_dot = 0
#     dq = Kp*error + Ki*error_i*dt + Kd*error_d/dt
#     
#     # Integrate numerically
#     mp,phi,q,p,theta,p_joint_1 = integrateNumerically(r,mp_dot,phi_dot,dq,dt)
#     
#     r.Update(mp,phi,p,theta,q,dq,np.array([0.0,0.0]),p_joint_1) 
#     
#     # Visualize the movement
#     visualizeMovement(r)
#     storeP = np.append(storeP,[p],axis=0)
#     # Save error for the derivative controller
#     prev_error = error
# =============================================================================
