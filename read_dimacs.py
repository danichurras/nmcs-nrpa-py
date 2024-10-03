import networkx as nx

#----------------------------------------------------
#   read_dimacs() - read a dimacs graph
#----------------------------------------------------

# assume que os vértices são numerados de 1 a n no arquivo
# mas internamente nomeia-os com números de 0 a n-1
def read_graph(fname):
    f = open(fname, "r")
    g = nx.Graph()
    for line in f:
        if line[0] == 'c':
            continue
        if line[0] == 'p':
            scan = line.split()
            n = int(scan[2])
            m = int(scan[3])
            g.add_nodes_from(range(n))
        if line[0] in 'ae':
            scan = line.split()
            u = int(scan[1])-1
            v = int(scan[2])-1
            # print(f"e {u} {v}")
            # weight = float(scan[3])
            if not g.has_edge(u,v):
                g.add_edge(u, v)
                #g.add_edge(u, v, weight=weight)
            #else:
            #    g[u][v]['weight'] += weight
    # print(f'Read dimacs graph with {g.number_of_nodes()} node and {g.number_of_edges()} edges')
    f.close()
    return g
