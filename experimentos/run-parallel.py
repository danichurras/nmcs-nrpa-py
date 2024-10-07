#!/bin/env python3

import sys, os, subprocess
import time
import logging

time_limit = 0

# Configure the logging system
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',  
    handlers=[
        logging.FileHandler("debug.log"),  # Write logs to a file
        logging.StreamHandler()            # Also output to the console
    ])

# executa as simulações, 
def run_simulation(tasks, max_concurrent_tasks):
    global time_limit

    command = "../nrpa_per_time.py"
    
    running_tasks = [] 
    next_task = 0

    # Start the first 'k' tasks
    while len(running_tasks) < max_concurrent_tasks and next_task < len(tasks):
        filename, number = tasks[next_task]
        try:
            process = subprocess.Popen([command, filename, str(number), str(time_limit)], cwd='../grafos')  
        except subprocess.CalledProcessError as e:
            logging.error(f"Error occurred while running simulation for {filename}: {e}")
        running_tasks.append(process)
        next_task += 1

    # Monitor and replace completed tasks
    while running_tasks:
        for process in running_tasks:
            retcode = process.poll()  # Check if process has finished
            if retcode is not None:   # Process finished
                running_tasks.remove(process)
                # Start the next task if there are more in the list
                if next_task < len(tasks):
                    filename, number = tasks[next_task]
                    process = subprocess.Popen([command, filename, str(number), str(time_limit)], cwd='../grafos')  
                    running_tasks.append(process)
                    next_task += 1
        time.sleep(0.1)  # Briefly sleep to avoid busy-waiting

def main(input_file, repeticoes, max_concurrent_tasks):
    print(f"Repetições: {repeticoes}")
    print(f"Tempo limite por repetição: {int(time_limit/60)} minutos")
    
    # run the simulation with k+1 and k where k is the known
    # chromatic number of the graph
    tasks = []
    for delta_k in [1,0]:
        try:
            with open(input_file, 'r') as file:
                for line in file:
                    parts = line.strip().split()
                    if len(parts) == 2:
                        filename, numero_de_cores = parts[0], parts[1]
                        # Ensure the second part is an integer
                        try:
                            number = int(numero_de_cores) + delta_k
                            tasks.extend([(filename, number)]*repeticoes)
                        except ValueError:
                            logging.error(f"Invalid number {numero_de_cores} for {filename}, skipping.")
                    else:
                        logging.error(f"Invalid input format: {line.strip()}, skipping.")
        except FileNotFoundError:
            logging.error(f'File {input_file} not found in run-testes.py.')
            exit(1)

    # Call the simulation function with the arguments
    run_simulation(tasks, max_concurrent_tasks)
        
if __name__ == "__main__":
    nparam = len(sys.argv)
    if nparam == 5:
        fname = sys.argv[1]
        repeticoes = int(sys.argv[2])
        time_limit = int(sys.argv[3])
        max_concurrent_tasks = int(sys.argv[4])
    else:
        script_name = os.path.basename(__file__)
        print(f"usage: {script_name} <file with graphs filenames and the chromatic number> repetitions_per_graph  time_limit number_of_parallel_processes")
        exit(1)

    main(fname, repeticoes, max_concurrent_tasks)

