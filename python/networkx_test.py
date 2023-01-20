import sys
from io import BytesIO

import networkx as nx


def print_graph(di_graph, write_func, format):
    with BytesIO() as buffer:
        write_func(di_graph, buffer)
        print(format)
        print('----------------------------------------------------------------------------------------------------------------')
        print(buffer.getvalue().decode('utf-8'), end='')
        print('----------------------------------------------------------------------------------------------------------------')
        print()


graph = nx.Graph()
graph.add_node('n1', name='Node1', city='Sydney')
graph.add_node('n2', name='Node2', city='London')
graph.add_node('n3', name='Node3', city='Rome')
graph.add_node('n4', name='Node4', city='Paris')
graph.add_node('n5', name='Node5', city='New York')

graph.add_edge('n1', 'n2')
graph.add_edge('n1', 'n3')
graph.add_edge('n2', 'n3')
graph.add_edge('n2', 'n4')
graph.add_edge('n3', 'n5')
graph.add_edge('n4', 'n5')


di_graph = nx.DiGraph()
di_graph.add_node('n1', name='Node1', colour='Red')
di_graph.add_node('n2', name='Node2', colour='Blue')
di_graph.add_node('n3', name='Node3', colour='Yellow')
di_graph.add_node('n4', name='Node4', colour='Green')
di_graph.add_node('n5', name='Node5', colour='Magenta')

di_graph.add_edge('n1', 'n2', weight=1)
di_graph.add_edge('n2', 'n3', weight=2)
di_graph.add_edge('n3', 'n4', weight=4)
di_graph.add_edge('n4', 'n1', weight=6)
di_graph.add_edge('n3', 'n5', weight=8)
di_graph.add_edge('n5', 'n3', weight=10)

print_graph( di_graph, nx.write_adjlist,           'Adjacency list'                   )
print_graph( di_graph, nx.write_edgelist,          'Edge list'                        )
print_graph( di_graph, nx.write_gexf,              'GEXF (Graph Exchange XML Format)' )
print_graph( di_graph, nx.write_gml,               'GML (Graph Modelling Language)'   )
print_graph( di_graph, nx.write_graphml,           'GraphML'                          )
print_graph( di_graph, nx.write_multiline_adjlist, 'Multiline adjacency list'         )
print_graph( di_graph, nx.write_pajek,             'Pajek'                            )
print_graph( di_graph, nx.write_weighted_edgelist, 'Weighted Edgelist'                )
print_graph( graph,    nx.write_graph6,            'Graph6'                           )
print_graph( graph,    nx.write_sparse6,           'Sparse6'                          )


# Outputs in GraphML XML format using the faster LXML framework
#print_graph(di_graph, nx.write_graphml_lxml, 'GraphML (using LXML)')

# Outputs in LaTeX format
#nx.write_latex(di_graph, 'latex_graph.tex')

# Outputs in pickle binary format
#import pickle
#with open('di_graph.gpickle', 'wb') as f:
#    pickle.dump(di_graph, f)

# Outputs in YAML format
#import yaml
#with open('test.yaml', 'w') as f:
#    yaml.dump(di_graph, f)


print('edges:')
print('\n'.join(str(e) for e in di_graph.edges()))
print()

print('nodes:')
print('Node,Out-degree')
print('\n'.join(f'{node},{out_degree}' for node, out_degree in di_graph.out_degree()))
print()

print('Removing nodes and edges to remove cycles (for topological sort)')
di_graph.remove_node('n1')
di_graph.remove_edge('n5', 'n3')
print('Node,Out-degree')
print('\n'.join(f'{node},{out_degree}' for node, out_degree in di_graph.out_degree()))

print("Topological sort")
print(list(nx.topological_sort(di_graph)))
print()
