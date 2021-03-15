# Chatbot generador de Gráficos para modelar arquitecturas a partir de requerimientos funcionales

## 1. Reconocer modelos, propiedades y eventos a partir de requerimientos funcionales

Para esto entrenamos el Chatbot con varios ejemplos de requerimientos categorizados con tags que referencian a los distintos componentes, por ejemplo:

```
Las [facturas](MODEL) [requerirán autorización](EVENT) por parte del [grupo de Gerentes](MODEL) antes de ser [contabilizadas](PROPERTY).
```

De esta manera el chatbot sabrá reconocer estos 3 tipos de entidades en una entrada nueva.
Mientras mas ejemplos se carguen más preciso sera el reconocimiento de las entidades.

## 2. Reconocer estructuras de grafos en los requerimientos
En esta etapa queremos conectar estructuras básicas (cadena, estrella, cadena doble) de grafos con distintos tipos de requerimientos. 
Por ejemplo para un requerimiento como el del ejemplo anterior queremos una cadena doble que vaya del modelo facturas a gerentes, con el evento "autorización" como puente y luego se agregue la propiedad "contabilizadas" a las facturas.
Para esto describimos estas combinaciones simples como "intenciones" que reconoce el chatbot, en el archivo nlu.yml.
Esto significa agrupar todos los requerimientos que creemos comparten una estructura de grafo similar bajo un mismo intent.

## 3. Construccin de grafos a partir de requerimientos
Esta etapa sigue los siguiente pasos:
a. Un usuario habla con el chatbot y el chatbot reconoce en el mensaje alguno de los intents que definimos en el paso 2. El chatbot extrae ademas entidades de esa frase.
b. Ejecutamos una accin que lee dichas entidades y la intención asignada a la frase. 
c. Usando como guia la estructura que define la intención, agregamos al grafo las entidades encontradas siguiendo esa estructura.
d. EL chatbot devuelve al usuario una imagen con el grafo actualizado


