#!/bin/env python

import networkx as nx
import matplotlib.pyplot as plt
import read_dimacs
import sys, os

def main():
    if len(sys.argv) > 1:
        fname = sys.argv[1]
    else:
        script_name = os.path.basename(__file__)
        print(f"usage: {script_name} <DIMACS graph filename>")
        exit(1)

# graph = nx.Graph()
# graph.add_edges_from([(0, 1), (0, 2), (1, 2), (1, 3), (2, 4), (3, 5), (3, 4), (4, 6), (4, 5), (5, 6)])

    graph = read_dimacs.read_graph(fname)

    print(f"Nodes: {graph.number_of_nodes()}, edges: {graph.number_of_edges()}")

    nx.draw(graph, pos=nx.spring_layout(graph),  with_labels=True)

    #    nx.draw_shell(graph, nlist=[range(5, 10), range(5)], with_labels=True, font_weight='bold')
    plt.show()

if __name__ == "__main__":
    main()
