# Copyright (c) 2017, K. Alex Mills. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of K. Alex Mills may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY K. ALEX MILLS ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL K. ALEX MILLS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import math
import random as r

# Very simple Map class for rapid prototyping of map algorithms.
class Map:
   # Initializes a 2D map with the given dimensions. All cells are initially
   # filled with walls.
   def __init__(self, width, height):
      self.width = width
      self.height = height
      self.squares = [0] * width * height

   # Displays the map for your viewing pleasure.
   def __str__(self):
      line = ""
      for y in range(self.height):
         for x in range(self.width):
            if (self.squares[x + y * self.width] > 0):
               line += '.'
            else:
               line += '#'
         line += '\n'
      return line

   # Sets a map cell to be EMPTY.
   def set(self, x, y):
      self.squares[x + y * self.width] = 1;

   # Unsets a map cell to the FILLED WITH A WALL.
   def unset(self, x, y):
      self.squares[x + y * self.width] = 0;
   
   # Returns 1 if the cell is empty, 0 if it contains a wall.
   def get(self, x, y):
      return self.squares[x + y * self.width];
   
   # Modifies this map by performing a logical or of that map with this one.
   def orWith(self, other):
      for x in range(min(other.width, self.width)):
         for y in range(min(other.height, self.height)):
            self.squares[x + y * self.width] |= other.get(x,y)

   # Modified this map by performing a logical and of that map with this one.
   def andWith(self, other):
      for x in range(min(other.width, self.width)):
         for y in range(min(other.height, self.height)):
            self.squares[x + y * self.width] &= other.get(x,y)

# A circle is a tuple (center, radius) where isinstance(center, Point). This returns
# true if cirlce is within distance dist_between of any circle in circle list.
def CircleClose(circle, circle_list, dist_between=0):
   for other_circle in circle_list:
      if other_circle[0].L2(circle[0]) < other_circle[1] + circle[1] + dist_between:
         return True;
   return False;

# Carves out a circle in the map. "Carving" means unsetting set map cells.
def CarveCircle(amap, circle):
   # Iterate over all cells in the circumscribed square.
   for x in [v + circle[0].x - circle[1] for v in range(circle[1] * 2)]:
      for y in [v + circle[0].y - circle[1] for v in range(circle[1] * 2)]:
         # Carve the pont if the distance from (x,y) is less than the radius of the circle
         if (circle[0].L2(Point(x,y)) <= circle[1]):  amap.set(x,y)

# Carves a tunnel defined by a quadratic bezier curve defined by points A, B, and C
def CarveBezier(amap, A, B, C, thin=False):
  t, dt = 0, 0.5 / max(amap.width, amap.height)
  for i in range(int(math.ceil(1 / dt))):
     P0 = A * t + (1 - t) * B
     P1 = B * t + (1 - t) * C
     Pfinal = P0 * t + (1 - t) * P1
     if not thin:
        for disp in [(x,y) for x in [-1,0 ,1] for y in [-1, 0, 1]]:
           if abs(disp[0]) + abs(disp[1]) != 2:
              amap.set(int(Pfinal.x + disp[0]), int(Pfinal.y + disp[1]))
     else:
        amap.set(int(Pfinal.x), int(Pfinal.y))
     t += dt

# This is a prototype for the Goblin Warrens.
# TODO: Implement a much better way of keeping the rooms apart and the tunnels
#       from overlapping. 
def GoblinHalls(amap):
   # Lists of nests stored as (center, radius) where isinstance(center,Point)
   nests = []
   num_its = 0
   while len(nests) < 7 and num_its < 1000:
      num_its += 1
      rad = r.randint(6, 10)  # radius
      new_nest = (Point(r.randint(rad, amap.width - rad), r.randint(rad, amap.height - rad)), rad)
   
      if CircleClose(new_nest, nests, 10):
         continue
      nests.append(new_nest)

      for nest in nests:
         CarveCircle(amap, nest)

   # CConnect each nest with its closest neighbor.
   connected_nests = []
   for i in range(len(nests)):
      curr_nest = nests[i]
      min_nest = (i + 1) % len(nests)
      min_dist = curr_nest[0].L2(nests[min_nest][0])
      
      for j in range(len(nests)):
         if i == j or (i,j) in connected_nests or (j,i) in connected_nests: continue
         dj = curr_nest[0].L2(nests[j][0])
         if dj <= min_dist:
            min_nest = j
            min_dist = dj

      CarveTunnelBetweenNests(amap, nests[i], nests[min_nest]);
      connected_nests.append((i, min_nest))

   # List of sets, each one is a set of connected nests.
   nest_components = []
   # Find groups of nests which are pairwise connected.
   for (i, j) in connected_nests:
      found_component = False
      for k in range(len(nest_components)):
         if i in nest_components[k] or j in nest_components[k]:
            nest_components[k] = nest_components[k].union({i,j})
            found_component = True
            break
      if not found_component:
         nest_components.append({i,j})

   # Connect at least one pair from each connected component to ensure all nests are connected.
   for i in range(len(nest_components) - 1):
      nest1 = nests[list(nest_components[i])[r.randint(0, len(nest_components[i]) - 1)]]
      nest2 = nests[list(nest_components[i + 1])[r.randint(0, len(nest_components[i + 1]) - 1)]]
      CarveTunnelBetweenNests(amap, nest1, nest2)

   # Acidify the walls and smooth over the resulting mess.
   WallAcid(amap, 0.05, 2);
   SmoothDiagonals(amap, 3);
   FillCubbyHoles(amap, 3);

# Subroutine for the Goblin Halls.
def CarveTunnelBetweenNests(amap, nest1, nest2):
   A = nest1[0]
   C = nest2[0]
   if r.randint(0,1) == 1:
      B = Point(min(nest1[0].x, nest2[0].x) - r.randint(1, 5), max(nest1[0].y, nest2[0].y) + r.randint(1, 5))
   else: 
      B = Point(max(nest1[0].x, nest2[0].x) + r.randint(1,5), min(nest1[0].y, nest2[0].y) - r.randint(1,5))
   CarveBezier(amap, A, B, C)

# Carves a quadratic bezier curve using control points A, B, C, then applies
# acid to the carving.
def CarveCavernBezier(amap, A, B, C, base_prob, num_iters):
   # We have to construct and destroy a temporary map since otherwise the wall
   # acid will eat away at other carvings as well.
   temp = Map(amap.width, amap.height)
   CarveBezier(temp, A, B, C, thin=True)
   WallAcid(temp, base_prob, num_iters)
   amap.orWith(temp)

# Randonly eats away at the walls of a map with acid. Any cell which has a
# empty square adjacent to it is randomly set to be empty with a probability
# equal to num_empty_squares * base_prob. The acid is allowed to run for 
# num_iters. 
#
# As written, this algorithm should touch each cell no more than four times,
# regardless of the number of iterations the acid is allowed to "eat" at the
# walls. This makes me happy.
def WallAcid(amap, base_prob, num_iters):
   # Createa a list of boundary cells: cells which have free space adjacent
   # to them.
   boundary = set() 
   for x in [i + 1 for i in range(amap.width - 2)]:
      for y in [i + 1 for i in range (amap.height - 2)]:
         if amap.get(x, y) == 0 :
            is_boundary = False
            for (i, j) in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
               if (x + i >= 0 and x + i < amap.width and   
                   y + j >= 0 and y + j < amap.height):
                  if amap.get(x + i, y + j) == 1:
                     is_boundary = True
                     break
            if is_boundary:
               boundary = boundary.union({(x,y)})

   for i in range(num_iters):
      next_boundary = set()
      for (x, y) in boundary:
         adjacent_walls = []
         for (i, j) in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            if (x + i >= 0 and x + i < amap.width and   
               y + j >= 0 and y + j < amap.height and 
               amap.get(x + i, y + j) == 0):
               adjacent_walls.append((x+i, y+j))
         prob_survive = base_prob * len(adjacent_walls)
         if r.uniform(0.0, 1.0) > prob_survive:
            amap.set(x,y)
            next_boundary = next_boundary.union(adjacent_walls)
      boundary = next_boundary

# Removes cells which are only diagonally adjacent to walls or free-standing. 
# min_diags is the minimum number of adajcent diagonals allowed. Any wall cell
# only adjacent to diagonal walls which is adjacent to fewer than min_diags
# walls is removed.
def SmoothDiagonals(amap, min_diags = 2):
   SmoothHelper(amap, min_diags, toggle=0)

# This fills in open cells which have only one open diagonal space next to
# them.
def FillCubbyHoles(amap, min_diags = 2):
   SmoothHelper(amap, min_diags, toggle=1)

# Helper for smoothing functions. Both of the smoothing functions use the 
# same basic algorithm, but the meaning of zero and one are reversed.
def SmoothHelper(amap, min_diags, toggle):
   for (x, y) in [(x+1, y+1) for x in range(amap.width - 2) for y in range(amap.height - 2)]:
      if amap.get(x, y) == toggle:
         num_cardinal = 0; # number of cardinal wall adajcencies
         for (i, j) in [(-1, 0), (1,0), (0, 1), (0,-1)]:
           if amap.get(x + i, y + j) == toggle:  num_cardinal = num_cardinal + 1
         if num_cardinal > 0: continue
         
         num_diagonal = 0
         for (i, j) in [(-1,-1), (1,1), (-1,1), (1,-1)]:
           if amap.get(x + i, y + j) == toggle:  num_diagonal = num_diagonal + 1
         if num_diagonal < min_diags:
           if toggle == 1:   amap.unset(x,y) 
           elif toggle == 0: amap.set(x,y)

# Simple and elegant pythonic Point.
class Point:
   def __init__(self, x, y=None):
      if y is None:
         if isinstance(x, Point):
            self.x, self.y = x.x, x.y
         else: 
            self.x, self.y = x, x
      else:
         self.x, self.y = x, y
 
   def __add__(self, other):
      other = Point(other)
      return Point(self.x + other.x, self.y + other.y)
   __radd__ = __add__   # commutative

   def __sub__(self, other):
      other = Point(other)
      return Point(self.x - other.x, self.y - other.y)
   
   def __mul__(self, other):
      other = Point(other)
      return Point(self.x * other.x, self.y * other.y)
   __rmul__ = __mul__   # commutative
   
   def __div__(self, other):
      other = Point(other)
      return Point(self.x / other.x, self.y / other.y)

   def L1(self, other):
      return math.abs(self.x - other.x) + math.abs(self.y - other.y)
 
   def L2(self, other):
      return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

   def __repr__(self):
      return 'Point({self.x}, {self.y})'.format(self=self)
   
