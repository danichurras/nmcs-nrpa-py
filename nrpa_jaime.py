#!/bin/env python

import read_dimacs
import sys, os
import math, random
import heapdict
import matplotlib.pyplot as plt
import networkx as nx
import copy

ALPHA = 0.3
N = 5           # Número de iterações do algoritmo NRPA
LEVEL = 4       # Limite de níveis de recursão
max_colors = 4  # Número de cores a serem usadas na coloração

counter = 0
graph = nx.Graph()

# fila de prioridade de vértices
class FilaVertices:
    def __init__(self, graph):
        self.fila = heapdict.heapdict()
        for v in graph.nodes:
            self.fila[v] = graph.degree(v)
    def pop(self):
        return self.fila.popitem()[0]
    def muda_prioridade(self, v, prioridade):
        self.fila[v] = prioridade
    
class State:
    def __init__(self, graph):
        self.n = graph.number_of_nodes()
        self.color = [None]*self.n
        self.colored = 0  # número de vértices coloridos

    def __str__(self):
        return str(str(self.color)+'\n'+ str(self.colored) + '/' + str(self.n)+'\n')

    def is_terminal(self) -> bool:
        return self.colored == self.n

    def is_color_valid(self, vertex: int, color: int) -> bool:
        for neighbor in graph[vertex]:
            if self.color[neighbor] == color:
                return False
        return True

    # Alterações nos movimentos:
    # 1. os movimentos possíveis consideram um único vértice, como
    # descrito no artigo
    # 2. Devolve primeiro as cores válidas e se não houver nenhum, devolve
    # as cores inválidas (há vizinhos com a mesma cor)
    def possible_moves(self, vertex):
        cores_invalidas = []
        existe_valida = False
        for color in range(max_colors):
            if self.is_color_valid(vertex, color):
                existe_valida = True
                yield (vertex, color)
            else:
                cores_invalidas.append(color)
        if not existe_valida:
            for color in cores_invalidas:
                yield (vertex, color)

    def play(self, move: tuple[int, int]):
        vertex, color = move
        self.color[vertex] = color
        self.colored += 1

    def score1(self) -> int:
        conflicts = 0
        for u, v in graph.edges():
            if self.color[u] == self.color[v]:
                conflicts += 1
        return -conflicts
        
    def score2(self) -> int:
        conflicts = 0
        for u, v in graph.edges():
            if self.color[u] == self.color[v]:
                conflicts += 1
        s = set(self.color)
        colors_used = len(s)
        # se score() for aplicado apenas a terminais, não há
        # necessidade de subtrair 1 para o valor None
        if None in s:
            colors -= 1
        return -conflicts - colors_used

    def initial_state(self):
        for i in range(self.n):
            self.color[i] = None
        self.colored = 0

def terminal_sequence(sequence):
    return len(sequence) == graph.number_of_nodes()

def code(move: tuple[int, int]) -> int:
    return move[0] * max_colors + move[1]

def playout(state: State, policy: list[float], graph) -> tuple[int, list[tuple[int, int]]]:
    fila_vertices = FilaVertices(graph)
    sequence = []

    while not terminal_sequence(sequence):
        vertex = fila_vertices.pop()
        z = 0.0
        # Calcula a soma exponencial dos pesos da política para normalização
        for move in state.possible_moves(vertex):
            z += math.exp(policy[code(move)])

        # Seleciona um movimento com base na distribuição de Gibbs
        r = random.uniform(0, 1)
        cumulative_probability = 0.0
        chosen_move = None
        for move in state.possible_moves(vertex):
            probability = math.exp(policy[code(move)]) / z
            cumulative_probability += probability
            if r <= cumulative_probability:
                chosen_move = move
                break

        # Executa o movimento escolhido e adiciona à sequência
        state.play(chosen_move)
        sequence.append(chosen_move)

    return state.score1(), sequence

def nrpa(state: State, level: int, policy: list[float], graph) -> tuple[int, list[tuple[int, int]]]:
    global counter
    counter += 1

    # print(state)

    if level == 0:
        state.initial_state()
        return playout(state, policy, graph)

    best_score = float('-inf')
    best_sequence = []

    for _ in range(N):
        result, new_sequence = nrpa(state, level - 1, policy.copy(), graph)
        if result > best_score:
            # cores_usadas = len(set([move[1] for move in new_sequence]))
            # print(f"Nova pontuação recorde de nível {level}: {result}\tCores usadas: {cores_usadas}")

            best_score = result
            best_sequence = new_sequence

        # Adapta a política com base na melhor sequência encontrada
        policy = adapt(state, policy, best_sequence)

    return best_score, best_sequence

def adapt(state: State, policy: list[float], sequence: list[tuple[int, int]]) -> list[float]:
    updated_policy = policy.copy()

    for move in sequence:
        vertex = move[0]
        updated_policy[code(move)] += ALPHA

        z = 0.0
        for m in state.possible_moves(vertex):
            z += math.exp(policy[code(m)])

        for m in state.possible_moves(vertex):
            updated_policy[code(m)] -= ALPHA * (math.exp(policy[code(m)]) / z)

    return updated_policy

# teste se uma coloração é válida
# usado para validação da coloração encontrada e depuração
def valid_coloring(state, graph):
    for u, v in graph.edges():
        if state.color[u] == state.color[v]:
            print(f'Vertices adjacentes {u} (original {(u+1)}) e {v} ({(v+1)}) receberam as cores {state.color[u]} e {state.color[v]}.')
            return False
    return True

def valid_sequence(sequence, graph):
    state = State(graph)
    for move in sequence:
        state.play(move)
    return valid_coloring(state, graph)

def main():
    global graph, max_colors
    nparam = len(sys.argv)
    if nparam == 3:
        fname = sys.argv[1]
        max_colors = int(sys.argv[2])
    else:
        script_name = os.path.basename(__file__)
        print(f"usage: {script_name} <DIMACS graph filename> <number-of-colors>")
        exit(1)

    graph = read_dimacs.read_graph(fname)
    print(f"Nodes: {graph.number_of_nodes()}, edges: {graph.number_of_edges()}\n")
    
    #graph = nx.Graph()
    #graph.add_edges_from([(0, 1), (0, 2), (1, 2), (1, 3), (2, 4), (3, 5), (3, 4), (4, 6), (4, 5), (5, 6)])
    
    state = State(graph)
    politica = [0] * graph.number_of_nodes() * max_colors

    melhor_score, melhor_sequencia = nrpa(state, LEVEL, politica, graph)

    cores = [move[1] for move in melhor_sequencia]

    if valid_sequence(melhor_sequencia, graph):
        print("Coloração válida.")
    else:
        print(f'Coloração não válida.')

    print(f"Cores usadas: {len(set(cores))}")
    print(f"Numero de vezes que nrpa foi executada: {counter}")
    print(f"Melhor pontuação: {melhor_score}")
    melhor_sequencia.sort()
    print(f"Melhor sequência: {melhor_sequencia}")

if __name__ == "__main__":
    main()
