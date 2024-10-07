#!/bin/env python3

import read_dimacs
import sys, os, signal, time
import math, random
import heapdict
import networkx as nx
import copy
import logging

ALPHA = 0.3
N = 5           # Número de iterações do algoritmo NRPA
max_colors = 4  # Número de cores a serem usadas na coloração
time_expired = False

counter = 0
graph = nx.Graph()

# Configure the logging system
logging.basicConfig(
    level=logging.DEBUG,  # Set the lowest-severity log message to capture
    format='%(asctime)s - %(levelname)s - %(message)s',  # Format with time and log level
    handlers=[
        logging.FileHandler("debug.log"),  # Write logs to a file
        logging.StreamHandler()            # Also output to the console
    ])

class TimeoutException(Exception):
    pass

# Handler function to raise the timeout exception
def timeout_handler(signum, frame):
    global time_expired
    time_expired = True
    #raise TimeoutException("Execution time limit exceeded.")


# fila de prioridade de vértices
class FilaVertices:
    def __init__(self, graph):
        self.fila = heapdict.heapdict()
        n = graph.number_of_nodes()
        for v in graph.nodes:
            self.fila[v] = n - graph.degree(v)
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

def nrpa(state: State, policy, graph):
    global counter, time_expired
    counter += 1
    
    best_score = float('-inf')
    best_sequence = []

    while True:
        state.initial_state()
        score, new_sequence = playout(state, policy, graph)

        if score > best_score:
            best_score = score
            best_sequence = new_sequence
            if score == 0: # encontrou uma coloração valida
                break
            policy = adapt(state, policy, best_sequence)
        if time_expired:
            break
    signal.alarm(0)        
    return best_score, best_sequence, time_expired

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
    if nparam >= 4:
        fname = sys.argv[1]
        max_colors = int(sys.argv[2])
        time_limit = int(sys.argv[3]) # tempo em segundos
    else:
        script_name = os.path.basename(__file__)
        print(f"usage: {script_name} <DIMACS graph filename> <number-of-colors> <tempo_de_execução> [verbose]", file=sys.stderr)
        exit(1)

    try:
        graph = read_dimacs.read_graph(fname)
    except:
        print(f"Cound not open the graph. File {fname} not found.", file=sys.stderr)

    state = State(graph)
    politica = [0] * graph.number_of_nodes() * max_colors

    signal.signal(signal.SIGALRM, timeout_handler) 
    if time_limit:
        signal.alarm(time_limit)
        
    start_time = time.time()
    score, sequencia, time_expired = nrpa(state, politica, graph)
    execution_time = time.time() - start_time 
    
    n = graph.number_of_nodes()
    m = graph.number_of_edges()
    output = []
    
    output.append(f'{os.path.basename(fname):<25} {max_colors:<4} ')
    output.append(f'{n:<6} {m:<6} ')
    
    if valid_sequence(sequencia, graph):
        output.append(f'{score:<6} yes ')
    else:
        output.append(f'{score:<6} no  ')
    if time_expired:
        output.append('limite de tempo ')
    else:
        output.append('.               ')
    output.append(f'{execution_time:>8.2f}')
    
    print(''.join(output), flush=True)
            
    # resposta longa (verbose)
    if nparam >= 4 and sys.argv[3] == 'verbose':
        print(output, flush=True)
        print(f'Nodes: {n}, edges: {m}\n')
        cores = [move[1] for move in sequencia]
        print(f"Cores usadas: {len(set(cores))}")
        print(f"Numero de vezes que nrpa foi executada: {counter}")
        print(f"Melhor pontuação: {core}")
        sequencia.sort()
        print(f"Melhor sequência: {sequencia}")
if __name__ == "__main__":
    main()
