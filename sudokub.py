#!/usr/bin/python3
import sys
import subprocess
import time
import random
import math
import copy

"""
    course  : INFO9015 
    year    : 2023
    author  : Simon Gardier (S192580)
"""

# reads a sudoku from file
# columns are separated by |, lines by newlines
# Example of a 4x4 sudoku:
# |1| | | |
# | | | |3|
# | | |2| |
# | |2| | |
# spaces and empty lines are ignored
def sudoku_read(filename):
    myfile = open(filename, 'r')
    sudoku = []
    N = 0
    for line in myfile:
        line = line.replace(" ", "")
        if line == "":
            continue
        line = line.split("|")
        if line[0] != '':
            exit("illegal input: every line should start with |\n")
        line = line[1:]
        if line.pop() != '\n':
            exit("illegal input\n")
        if N == 0:
            N = len(line)
            if N != 4 and N != 9 and N != 16 and N != 25:
                exit("illegal input: only size 4, 9, 16 and 25 are supported\n")
        elif N != len(line):
            exit("illegal input: number of columns not invariant\n")
        line = [int(x) if x != '' and int(x) >= 0 and int(x) <= N else 0 for x in line]
        sudoku += [line]
    return sudoku

# print sudoku on stdout
def sudoku_print(myfile, sudoku):
    if sudoku == []:
        myfile.write("impossible sudoku\n")
    N = len(sudoku)
    for line in sudoku:
        myfile.write("|")
        for number in line:
            if N > 9 and number < 10:
                myfile.write(" ")
            myfile.write(" " if number == 0 else str(number))
            myfile.write("|")
        myfile.write("\n")

# returns a string containing the generic constraints for a sudoku of size N
def sudoku_generic_constraints(N):
    data_length = len(str(N))
    constraints_parts = []
    count = 0

    def output(s):
        constraints_parts.append(s)
    lit_values =    [[[f"{str(i).zfill(data_length)}{str(j).zfill(data_length)}{str(k).zfill(data_length)} " for k in range(1, N+1)] for j in range(1, N+1)] for i in range(1, N+1)]
    notlit_values = [[[f"{str(-i).zfill(data_length)}{str(j).zfill(data_length)}{str(k).zfill(data_length)} " for k in range(1, N+1)] for j in range(1, N+1)] for i in range(1, N+1)]

    def celllits(i, j):
        constraints_parts.extend(lit_values[i-1][j-1])

    def newlit(i,j,k):
        output(lit_values[i-1][j-1][k-1])

    def newnotlit(i,j,k):
        output(notlit_values[i-1][j-1][k-1])

    def newcl():
        nonlocal count
        output("0\n")
        count += 1

    if N == 4:
        n = 2
    elif N == 9:
        n = 3
    elif N == 16:
        n = 4
    elif N == 25:
        n = 5
    else:
        exit("Only supports size 4, 9, 16 and 25")

    #Cells constraints
    for i in range(1, N+1):
        for j in range(1, N+1):
            celllits(i, j)
            newcl()
            for value in range(1, N+1):
                for otherValue in range(value+1, N+1):
                    newnotlit(i, j, value)
                    newnotlit(i, j, otherValue)
                    newcl()

    #Lines constraints
    for line in range(1, N+1):
        for value in range(1, N+1):
            for col in range(1, N+1):
                newlit(line, col, value)
            newcl()
        for col in range(1, N+1):
            for otherCol in range(col+1, N+1):
                for value in range(1, N+1):
                    newnotlit(line, col, value)
                    newnotlit(line, otherCol, value)
                    newcl()
    
    #Columns constraints
    for col in range(1, N+1):
        for value in range(1, N+1):
            for line in range(1, N+1):
                newlit(line, col, value)
            newcl()
        for cellLine in range(1, N+1):
            for otherCellLine in range(cellLine+1, N+1):
                for value in range(1, N+1):
                    newnotlit(cellLine, col, value)
                    newnotlit(otherCellLine, col, value)
                    newcl()

    #Squares constraints
    for i in range(n):
        for j in range(n):
            for value in range(1, N+1):
                for line in range (1, n+1):
                    for col in range (1, n+1):
                        newlit(line+i*n, col+j*n, value)
                newcl()
            for line1 in range(1, n+1):
                for col1 in range(1, n+1):
                    for col2 in range(col1+1, n+1):
                        for value in range(1, N+1):
                            newnotlit(line1+i*n, col1+j*n, value)
                            newnotlit(line1+i*n, col2+j*n, value)
                            newcl()
                    for line2 in range(line1+1, n+1):
                        for col2 in range(1, n+1):
                            for value in range(1, N+1):
                                newnotlit(line1+i*n, col1+j*n, value)
                                newnotlit(line2+i*n, col2+j*n, value)
                                newcl()
    return ''.join(constraints_parts), count

# returns a string containing the specific constraints for a sudoku
def sudoku_specific_constraints(sudoku):

    N = len(sudoku)
    constraints_parts = []
    data_length = len(str(N))
    count = 0

    def output(s):
        constraints_parts.append(s)

    def newlit(i,j,k):
        output(f"{str(i).zfill(data_length)}{str(j).zfill(data_length)}{str(k).zfill(data_length)} ")

    def newcl():
        nonlocal count
        output("0\n")
        count += 1

    for i in range(N):
        for j in range(N):
            if sudoku[i][j] > 0:
                newlit(i + 1, j + 1, sudoku[i][j])
                newcl()

    return ''.join(constraints_parts), count

# returns a string containing the constraints for a sudoku to have another solution
def sudoku_other_solution_constraint(solved_sudoku, unsolved_sudoku):

    N = len(unsolved_sudoku)
    constraints_parts = []
    data_length = len(str(N))

    def output(s):
        constraints_parts.append(s)

    def newnotlit(i,j,k):
        output(f"{str(-i).zfill(data_length)}{str(j).zfill(data_length)}{str(k).zfill(data_length)} ")

    def newcl():
        output("0\n")

    for i in range(1, N+1):
        for j in range(1, N+1):
            if unsolved_sudoku[i-1][j-1] == 0:
                newnotlit(i, j, solved_sudoku[i-1][j-1])
    newcl()
    return ''.join(constraints_parts), 1

def sudoku_solve(filename):
    command = "java -jar org.sat4j.core.jar sudoku.cnf"
    process = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    for line in out.split(b'\n'):
        line = line.decode("utf-8")
        if line == "" or line[0] == 'c':
            continue
        if line[0] == 's':
            if line != 's SATISFIABLE':
                return []
            continue
        if line[0] == 'v':
            line = line[2:]
            units = line.split()
            if units.pop() != '0':
                exit("strange output from SAT solver:" + line + "\n")
            units = [int(x) for x in units if int(x) >= 0]
            N = len(units)
            if N == 16:
                N = 4
            elif N == 81:
                N = 9
            elif N == 256:
                N = 16
            elif N == 625:
                N = 25
            else:
                exit("strange output from SAT solver:" + line + "\n")
            sudoku = [ [0 for i in range(N)] for j in range(N)]
            data_len = len(str(N))
            i_pos = 100 ** data_len
            j_pos = 10 ** data_len
            value_size =  10 ** data_len
            for number in units:
                sudoku[(number // i_pos) - 1][((number // j_pos) % j_pos) - 1] = number % value_size
            return sudoku
        exit("strange output from SAT solver:" + line + "\n")
        return []

# returns a sudoku grid of size N
def sudoku_generate(size, minimal=False):
    def sudoku_generate_is_valid(sudoku, i, j, value):
        N = len(sudoku)
        square_size = int(math.sqrt(N))

        for k in range(N):
            if sudoku[i][k] == value or sudoku[k][j] == value:
                return False

        top_left_line, top_left_column = (i // square_size) * square_size, (j // square_size) * square_size

        for line in range(top_left_line, top_left_line + square_size):
            for column in range(top_left_column, top_left_column + square_size):
                if sudoku[line][column] == value:
                    return False
        return True

    def sudoku_generate_solve_sudoku(sudoku):
        N = len(sudoku)
        for i in range(N):
            for j in range(N):
                if sudoku[i][j] == 0:
                    possible_values = list(range(1, N + 1))
                    random.shuffle(possible_values)
                    for value in possible_values:
                        if sudoku_generate_is_valid(sudoku, i, j, value):
                            sudoku[i][j] = value
                            if sudoku_generate_solve_sudoku(sudoku):
                                return True
                            sudoku[i][j] = 0
                    return False
        return True

    n = math.isqrt(size)
    if(n*n != size):
        exit("Unable to create a sudoku grid of size :", size)
    solved_sudoku = [[0 for value in range(size)] for line in range(size)]
    if(not sudoku_generate_solve_sudoku(solved_sudoku)):
        exit("Unable to generate a solved grid for this size")
    sudoku_grid = copy.deepcopy(solved_sudoku)
    generic_constraints_string, constraintsCount1 = sudoku_generic_constraints(size)

    if minimal :
        for i in range(0, size):
            for j in range(0, size):
                if sudoku_grid[i][j] == size:
                    sudoku_grid[i][j] = 0

    positions = [(i, j) for i in range(0, size) for j in range(0, size)]
    random.shuffle(positions)
    nbToRemove = n
    
    while len(positions) != 0:
        removed = {}
        for i in range(0, nbToRemove):
            position = positions.pop()
            removed[position] = sudoku_grid[position[0]][position[1]]
        for position, _ in removed.items():
            sudoku_grid[position[0]][position[1]] = 0

        specific_constraints_string, constraintsCount2 = sudoku_specific_constraints(sudoku_grid)
        other_solution_constraints, constraintsCount3 = sudoku_other_solution_constraint(solved_sudoku, sudoku_grid)

        myfile = open("sudoku.cnf", 'w')
        myfile.write("p cnf "+str(size)+str(size)+str(size)+" "+str(constraintsCount1+constraintsCount2+constraintsCount3)+"\n")
        myfile.write(generic_constraints_string)
        myfile.write(specific_constraints_string)
        myfile.write(other_solution_constraints)
        myfile.close()

        other_solution = sudoku_solve("sudoku.cnf")
        if other_solution != []:
            for position, value in removed.items():
                sudoku_grid[position[0]][position[1]] = value

    return sudoku_grid

from enum import Enum
class Mode(Enum):
    SOLVE = 1
    UNIQUE = 2
    CREATE = 3
    CREATEMIN = 4

start_time = time.time()
OPTIONS = {}
OPTIONS["-s"] = Mode.SOLVE
OPTIONS["-u"] = Mode.UNIQUE
OPTIONS["-c"] = Mode.CREATE
OPTIONS["-cm"] = Mode.CREATEMIN

if len(sys.argv) != 3 or not sys.argv[1] in OPTIONS :
    sys.stdout.write("./sudokub.py <operation> <argument>\n")
    sys.stdout.write("     where <operation> can be -s, -u, -c, -cm\n")
    sys.stdout.write("  ./sudokub.py -s <input>.txt: solves the Sudoku in input, whatever its size\n")
    sys.stdout.write("  ./sudokub.py -u <input>.txt: check the uniqueness of solution for Sudoku in input, whatever its size\n")
    sys.stdout.write("  ./sudokub.py -c <size>: creates a Sudoku of appropriate <size>\n")
    sys.stdout.write("  ./sudokub.py -cm <size>: creates a Sudoku of appropriate <size> using only <size>-1 numbers\n")
    sys.stdout.write("    <size> is either 4, 9, 16, or 25\n")
    exit("Bad arguments\n")

mode = OPTIONS[sys.argv[1]]

if mode == Mode.SOLVE or mode == Mode.UNIQUE:
    filename = str(sys.argv[2])
    sudoku = sudoku_read(filename)
    N = len(sudoku)

    generic_constraints_string, constraintsCount1 = sudoku_generic_constraints(N)
    specific_constraints_string, constraintsCount2 = sudoku_specific_constraints(sudoku)

    myfile = open("sudoku.cnf", 'w')
    myfile.write("p cnf "+str(N)+str(N)+str(N)+" "+str(constraintsCount1+constraintsCount2)+"\n")
    myfile.write(generic_constraints_string)
    myfile.write(specific_constraints_string)
    myfile.close()

    sys.stdout.write("sudoku\n")
    sudoku_print(sys.stdout, sudoku)
    sudoku = sudoku_solve("sudoku.cnf")
    sys.stdout.write("\nsolution\n")
    sudoku_print(sys.stdout, sudoku)

    if sudoku != [] and mode == Mode.UNIQUE:
        unsolved_sudoku = sudoku_read(filename)
        other_solution_constraints, constraintsCount3 = sudoku_other_solution_constraint(sudoku, unsolved_sudoku)

        myfile = open("sudoku.cnf", 'w')
        myfile.write("p cnf "+str(N)+str(N)+str(N)+" "+str(constraintsCount1+constraintsCount2+constraintsCount3)+"\n")
        myfile.write(generic_constraints_string)
        myfile.write(specific_constraints_string)
        myfile.write(other_solution_constraints)
        myfile.close()

        sudoku = sudoku_solve("sudoku.cnf")
        if sudoku == []:
            sys.stdout.write("\nsolution is unique\n")
        else:
            sys.stdout.write("\nother solution\n")
            sudoku_print(sys.stdout, sudoku)

elif mode == Mode.CREATE:
    size = int(sys.argv[2])
    sudoku = sudoku_generate(size)
    sys.stdout.write("\ngenerated sudoku\n")
    sudoku_print(sys.stdout, sudoku)

elif mode == Mode.CREATEMIN:
    size = int(sys.argv[2])
    sudoku = sudoku_generate(size, True)
    sys.stdout.write("\ngenerated sudoku\n")
    sudoku_print(sys.stdout, sudoku)
print("---"+ str(time.time()-start_time) +"seconds ---")
