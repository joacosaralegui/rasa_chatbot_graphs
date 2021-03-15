
# Other imports
import pygraphviz as pgv
import os 
import enchant 
from datetime import datetime
# Constants
SYSTEM = "Sistema"

class Graph:
  def __init__(self, tracker):
      self.graph = get_graph(tracker)