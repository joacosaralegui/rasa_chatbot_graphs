# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List

# Rasa imports
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# Other imports
import pygraphviz as pgv
import os 
import enchant 
from datetime import datetime
# Constants
SYSTEM = "Sistema"

# Action
class ActionShowEntities(Action):

    def name(self) -> Text:
        return "show_entities"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Leo las entidades que encontro en el requerimiento
        entities = get_entities(tracker)
        print_summary(entities)
        # Obtengo el intent, que voy a usar para elegir la estructura de grafo
        intent = get_intent(tracker)
        # Obtengo el grafo almacenado en el tracker (si no existe crea uno nuevo vacio)
        graph_manager = GraphManager(tracker)
        # Actualizo el grafo con las entidades y el intent acordes
        graph_manager.update_graph_with_new_entities(entities,intent)
        # Genero la imagen para mostrar al usuario
        graph_image_file = graph_manager.get_image_file()
        # Devuelvo esa imagen
        dispatcher.utter_message(image=os.path.abspath(graph_image_file))
        
        # Guardo el grafo actualizado
        return [graph_manager.save_to_slot(slotname="graph")]

class GraphManager:
    
    def __init__(self, tracker):
        # Inicializa el grafo vacio o trae el que ya existe en el slot correspondiente
        if self.is_graph_slot_loaded(tracker):
            self.graph = self.load_from_slot(tracker)
        else:
            self.graph = self.create_new()

    def is_graph_slot_loaded(self,tracker):
        # Chequea si el grafo existe
        graph_slot = tracker.get_slot("graph")
        return graph_slot != None

    def create_new(self):
        # Crea grafo nuevo
        return pgv.AGraph(strict=False,directed=True)

    def load_from_slot(self,tracker):
        # Cargo grafo desde el slot
        graph_slot = tracker.get_slot("graph")
        return pgv.AGraph(string=graph_slot)

    def save_to_slot(self,slotname):
        # Guardo grafo a slot
        return SlotSet(slotname,self.graph.to_string())

    def update_graph_with_new_entities(self,entities,intent):
        # De acuerdo al intent ejecuto distintas funciones para actualizar el grafo
        print(intent)
        if intent == "star":
            self.update_graph_with_star_entities(entities)
        elif intent == "simple_chain" or intent == "double_chain":
            self.update_graph_with_chained_entities(entities)  
        else:
            # Mezcla de star con cadena de acuerdo al intent
            nodes = [e for e in entities if e.is_node()]
            if "simple" in intent:
                cut_index = entities.index(nodes[1])
            elif "double" in intent:
                cut_index = entities.index(nodes[2])

            if len(entities) > cut_index:
                self.update_graph_with_chained_entities(entities[:cut_index+1])
                self.update_graph_with_star_entities(entities[cut_index:])  


    def get_image_file(self):
        # Generar imagen del grafo
        filename = 'file'+ str(datetime.now()) +'.png'
        self.draw_in_file(filename)
        return filename

    def draw_in_file(self,filename):
        # Guardar grafo a archivo
        self.graph.layout(prog='dot') 
        self.graph.draw(filename) 

    def add_node(self,node):
        # Agregar nodo al grafo
        self.graph.add_node(node.name,color=node.get_color(),shape=node.get_shape())

    def update_name_if_similar_found_in_graph(self,node_to_add):
        # Para nombres parecidos, unifico
        closest = {'node':None,'distance':3}
        for node_to_compare in self.graph.nodes():
            calculated_distance = enchant.utils.levenshtein(node_to_compare, node_to_add.name)
            if calculated_distance < closest['distance']:
                closest['node'], closest['distance']= node_to_compare, calculated_distance
        
        if closest['node'] != None:
            node_to_add.name = closest['node'].name

    def get_closest_node(self,reference_node,nodes):
        # Obtengo el nodo mas cercano al reference_node
        prev_node = nodes[0]
        if reference_node.start < prev_node.start:
            return prev_node
        else:
            for node in nodes[1:]:
                if reference_node.end < node.start:
                    if abs(reference_node.start - prev_node.end) <  abs(reference_node.end - node.start):
                        return prev_node
                    else:
                        return node
                else:
                    prev_node = node
            return prev_node

    def enough_nodes(self,nodes):
        # si tengo suficientes nodos como para generar un link
        return len(nodes) >= 2

    def update_edge_label(self,edge,entity):
        # Actualizar etiqueta de un conector con el nombre de una entidad
        label = edge.attr['label']
        if entity.name not in label:
            edge.attr['label'] += ", " + entity.name

    def add_labeled_edge(self,node1,node2,entity):
        # Agregar una conexi??n con etiqueta (si ya existe solo actualizo la etiqueta con la entidad nueva
        if self.graph.has_edge(node1.name,node2.name):
            edge = self.graph.get_edge(node1.name, node2.name) 
            self.update_edge_label(edge,entity)
        else:
            self.graph.add_edge(node1.name, node2.name, label=entity.name)  

    def add_edge(self,node1,node2):
        # Agregar conexion entre dos nodos, sin etiqueta
        self.graph.add_edge(node1.name, node2.name)  

    def find_nodes_connected_by_event(self,event,nodes): 
        # Trae los nodos que estan unidos por un evento
        i = 0
        first_node,second_node = nodes[i],nodes[i+1]
        while i < len(nodes)-2:
            if event.end < second_node.start:
                return first_node, second_node
            else:
                i += 1
                first_node,second_node = nodes[i],nodes[i+1]
        return first_node,second_node           

    def update_nodes(self,nodes):
        # Actualiza los nombres de los nodos si encuentra nombres similares en el grafo
        for node in nodes:
            self.update_name_if_similar_found_in_graph(node)
            self.add_node(node)

    def update_events(self,nodes,entities):
        # Actualiza los nombres de las conexiones si tenemos una etiqueta nueva
        events = [e for e in entities if e.is_event()]
        for event in events:
            node1,node2 = self.find_nodes_connected_by_event(event,nodes)          
            self.add_labeled_edge(node1,node2,event)
    
    def update_properties(self,nodes,entities):
        # Lo mismo para las propiedades
        properties = [e for e in entities if e.is_property()]
        for property_node in properties:
            if property_node not in nodes:
                closest_node = self.get_closest_node(property_node,nodes)
                self.add_node(property_node)
                self.add_edge(closest_node, property_node)  

    def connect_unconnected_nodes(self,nodes):
        # Si quedan nodos desconectados los unimos
        prev_node = nodes[0]
        for node in nodes[1:]:
            if not self.graph.has_edge(prev_node.name,node.name):
                self.add_edge(prev_node,node)
                self.add_edge(node,prev_node)
            prev_node = node

    def update_graph_with_chained_entities(self,entities):
        # un modo de agregar entidades
        nodes = [e for e in entities if e.is_node()]
        if not self.enough_nodes(nodes):
            nodes = [e for e in entities if e.is_node() or e.is_property()]
        if not self.enough_nodes(nodes):
            return

        self.update_nodes(nodes)
        self.update_events(nodes,entities)
        self.update_properties(nodes,entities)
        self.connect_unconnected_nodes(nodes)


    def update_graph_with_star_entities(self,entities):
        nodes = [e for e in entities if e.is_node()]
        if not self.enough_nodes(nodes):
            nodes = [e for e in entities if e.is_node() or e.is_property()]
        
        if not self.enough_nodes(nodes):
            return
        
        self.update_nodes(nodes)
        self.update_properties(nodes,entities)
        
        main_node = nodes[0]
        for idx, entity in enumerate(entities[:-1]):
            next_entity = entities[idx+1]
            if entity.is_event() and next_entity.is_node() and next_entity != main_node:
                self.add_labeled_edge(main_node,next_entity,entity)

        for node in nodes[1:]:
            if not self.graph.has_edge(main_node.name,node.name):
                self.add_edge(main_node,node)


class Entity:
    colors = {"MODEL":"blue","SYSTEM":"red","PROVIDER":"yellow","PROPERTY":"cyan"}
    shapes = {"MODEL":"box","SYSTEM":"oval","PROVIDER":"box","PROPERTY":"house"}

    def __init__(self, entity_object):
        self.category = entity_object['entity']
        self.name = entity_object['value']
        self.confidence = entity_object['confidence_entity']
        self.start = entity_object['start']
        self.end = entity_object['end']

        if self.matches_category("SYSTEM"):
            self.name = SYSTEM

    def matches_category(self,category):
        return self.category == category

    def is_node(self):
        return not self.is_event() and not self.is_property()

    def is_event(self):
        return self.matches_category("EVENT")
    
    def is_property(self):
        return self.matches_category("PROPERTY")

    def is_valid(self):
        return self.is_long_enough() and self.is_confidence_enough()

    def is_long_enough(self,min_length_required=2):
        return len(self.name) > min_length_required

    def is_confidence_enough(self,min_confidence_requiered=0.5):
        return  self.confidence > min_confidence_requiered 

    def get_color(self):
        return Entity.colors[self.category]

    def get_shape(self):
        return Entity.shapes[self.category]

# Helper functions

def get_entities(tracker):
    entities_objects = tracker.latest_message['entities']    
    entities = [Entity(e) for e in entities_objects]
    return get_valid_entities(entities)

def get_valid_entities(entities):
    return [e for e in entities if e.is_valid()]

def get_intent(tracker):
    return tracker.latest_message['intent']['name']

def print_summary(entities):
    print("***  New requirement  ****")
    print("Entities: ")
    for e in entities:
        print(f" - {e.category}: {e.name}")
    print("*************************")
