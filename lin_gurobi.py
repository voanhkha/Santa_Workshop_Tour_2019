# Copyright 2019, Kha Vo

from gurobipy import *
import pickle, sys, numpy as np

def load_csv(filename):
    asm = []
    with open(filename) as stream:
        for i, line in enumerate(stream.readlines()):
            if i == 0: continue
            f = int(line.split(',')[-1])
            asm.append(f)
    return asm

def save_csv(asm, filename):
    with open(filename, "w") as s:
        s.write("family_id,assigned_day\n")
        for f, d in enumerate(asm):
            s.write("%d,%d\n" %(f,d+1))

submission_path = 'subs_100/68890.csv'

init_solution = load_csv(submission_path)
init_solution = [i-1 for i in init_solution]

C = list(range(125, 301))
DATAPATH = 'data/'
with open (DATAPATH+'Acc_Table.pkl', 'rb') as fp: ACC = pickle.load(fp)
with open (DATAPATH+'Pre_Table.pkl', 'rb') as fp: PREF = pickle.load(fp)
with open (DATAPATH+'Npp.pkl', 'rb') as fp: FAMILYSIZE = pickle.load(fp)
with open (DATAPATH+'Choice_Table.pkl', 'rb') as fp: CHOICE = pickle.load(fp)

disabled_bad_choice = [[1 if d in row[:5] else 0 for d in range(100) ] for r, row in enumerate(CHOICE)]
x_lb  = [[0 for d in range(100) ] for r, row in enumerate(CHOICE)]
x_ub  = [[1 for d in range(100) ] for r, row in enumerate(CHOICE)]

y_lb = [[0 for occ in range(125, 301)] for d in range(100)]
y_ub = [[1 for occ in range(125, 301)] for d in range(100)]

C1 = [[j for i in range(125, 301)] for j in range(125, 301)]
C2 = [[i for i in range(125, 301)] for j in range(125, 301)]

fixed_occ = [[0 for occ in range(125, 301)] for d in range(100)]
# fixed_occ_125 = fixed_occ.copy()
for d in [0, 2, 3, 10]:
    fixed_occ[d][-1] = 1
# fixed_occ_300 = fixed_occ.copy()
for d in [97, 98, 99, 90, 91, 92, 83, 84, 85, 76, 77 , 78, 69, 70, 71]:
    fixed_occ[d][0] = 1

Nd100 = [(N - 125.)/400 * N**(0.5) for N in range(125, 301)]

_arr = []
with open('occ_constr_2.txt') as stream:
    for i, line in enumerate(stream.readlines()):
        if ',' not in line: continue
        values = int(line.split(',')[0])
        _arr.append(values)
min_arr = _arr[::2]
max_arr = _arr[1::2]

# max_arr = []
# min_arr = []
# with open('occ_constr.txt') as stream:
#     for i, line in enumerate(stream.readlines()):
#         values = line.split(' ')
#         max_arr.append(int(values[-1]))
#         min_arr.append(int(values[0]))


def simple_mst_writer(model, mstfilename, nodecnt, obj):
    mstfile = open(mstfilename, 'w')
    varlist = model.getVars()
    soln = model.cbGetSolution(varlist) #  cbGetSolution
    mstfile.write('# MIP start from soln at node %d obj %e\n' % (nodecnt, obj))
    for var, soln in zip(varlist, soln):
        mstfile.write('%s %.3e\n' % (var.VarName, soln))
    mstfile.close()


def mycallback(model, where):
    if where == GRB.callback.MIPSOL: # MIPSOL
        obj = model.cbGet(GRB.callback.MIPSOL_OBJ)
        nodecnt = int(model.cbGet(GRB.callback.MIPSOL_NODCNT))
        print('Found solution at node', nodecnt, 'obj', obj)
        simple_mst_writer(model, 'sol.mst', nodecnt, obj)

try:
    model = Model("santa2019")

    x = model.addVars(5000, 100, vtype=GRB.BINARY, name='x', ub=disabled_bad_choice, lb=x_lb )

    y = model.addVars(list(range(100)) , list(range(125, 301)), list(range(125, 301)), vtype=GRB.BINARY, name='y', lb=0, ub=1) #lb=y_lb, ub=y_ub)



    model.addConstrs((x.sum(f ,'*') == 1 for f in range(5000)),  name='familyConstr')

    model.addConstrs((np.sum([x[f,d] * FAMILYSIZE[f] for f in range(5000)]) >= min_arr[d] for d in range(100)), name='lowerCapaConstr' )

    model.addConstrs((np.sum([x[f,d] * FAMILYSIZE[f] for f in range(5000)]) <= max_arr[d] for d in range(100)), name='upperCapaConstr' )

   

    model.addConstrs((y.sum(d, '*', '*') == 1 for d in range(100)), name = 'yConstr' ) # each day has 1 number of occupancy

    model.addConstrs( ( sum( [y[d,i,j]*C2[i-125][j-125] for i in range(125,301) for j in range(125,301)] ) == 
    sum( [y[d+1,i,j]*C1[i-125][j-125] for i in range(125,301) for j in range(125,301)] )  for d in range(99) ), name='OccConstr'   ) # occupancy 

    model.addConstr( sum( [y[99,i,j]*C2[i-125][j-125] for i in range(125,301) for j in range(125,301)] ) == 
    sum( [y[99,i,j]*C1[i-125][j-125] for i in range(125,301) for j in range(125,301)] ), name='occLastConstr'   )  # last occupancy day 99
    
    model.addConstrs(( sum([y[d, i, j]*C1[i-125][j-125] for i in range(125,301) for j in range(125,301)]) == 
    np.sum([x[f,d] * FAMILYSIZE[f] for f in range(5000)]) for d in range(100)), name='xyConstr' )

    # model.addConstr( sum([y[99, i, j]*C2[i-125][j-125] for i in range(125,301) for j in range(125,301)]) == 
    # np.sum([x[f,99] * FAMILYSIZE[f] for f in range(5000)]) , name='xyConstrlast' )

    model.ModelSense = GRB.MINIMIZE

    model.setParam('MIPGap', 0) 
    model.setParam('Seed', 24) 

    model.setObjective(
        sum([x[f, d]*PREF[f][d] for f in range(5000) for d in range(100)])  +
        sum([ sum([ y[d,i,j]*ACC[i-125][j-125] for i in range(125,301) for j in range(125,301) ])  for d in range(100) ]) 
        )

    for f, asm in enumerate(init_solution):
        for d in range(100):
            if asm==d: x[f, d].start = 1
            else: x[f, d].start = 0

    # Save problem

    #model.write('santa_gurobi.lp')

    # Optimize
    model.optimize(mycallback)

    status = model.Status
    if status == GRB.Status.INF_OR_UNBD or \
       status == GRB.Status.INFEASIBLE  or \
       status == GRB.Status.UNBOUNDED:
        print('The model cannot be solved because it is infeasible or unbounded')
        sys.exit(0)

    if status != GRB.Status.OPTIMAL:
        print('Optimization was stopped with status ' + str(status))
        sys.exit(0)

    # Print total slack and the number of shifts worked for each worker

except GurobiError as e:
    print('Error code ' + str(e.errno) + ": " + str(e))

except AttributeError as e:
    print('Encountered an attribute error: ' + str(e))