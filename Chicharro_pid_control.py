# Chicharro_pid.py -- Python module
#
# Chicharro_pid: Chicharro trivariate Partial Information Decomposition
# https://github.com/Abzinger/Chicharro_pid 
# (c) Abdullah Makkeh, Dirk Oliver Theis
# Permission to use and modify with proper attribution
# (Apache License version 2.0)
#
# Information about the algorithm, documentation, and examples are here:
# @Article{makkeh2018broja,
#          author =       {Makkeh, Abdullah and Theis, Dirk Oliver and Vicente, Raul},
#          title =        {BROJA-2PID: A cone programming based Partial Information Decomposition estimator},
#          journal =      {Entropy},
#          year =         2018,
#          volume =    {20},
#          number =    {4},
#          pages =     {271}
# }
# Please cite this paper when you use this software (cf. README.md)
##############################################################################################################
import ecos
from scipy import sparse
import numpy as np
from numpy import linalg as LA
import math
from collections import defaultdict

log = math.log2
ln  = math.log

# ECOS's exp cone: (r,p,q)   w/   q>0  &  exp(r/q) ≤ p/q
# Translation:     (0,1,2)   w/   2>0  &  0/2      ≤ ln(1/2)
def r_vidx(i):
    return 3*i
def p_vidx(i):
    return 3*i+1
def q_vidx(i):
    return 3*i+2

class Chicharro_pid_Exception(Exception):
    pass


class Solve_w_ECOS():
    # (c) Abdullah Makkeh, Dirk Oliver Theis
    # Permission to use and modify under Apache License version 2.0
    def __init__(self, marg_sx, marg_sy, marg_sz):
        # (c) Abdullah Makkeh, Dirk Oliver Theis
        # Permission to use and modify under Apache License version 2.0

        # ECOS parameters
        self.ecos_kwargs   = dict()
        self.verbose       = False

        # Data for ECOS
        self.c            = None
        self.G            = None
        self.h            = None
        self.dims         = dict()
        self.A            = None
        self.b            = None

        # ECOS result
        self.sol_rpq    = None
        self.sol_slack  = None #
        self.sol_lambda = None # dual variables for equality constraints
        self.sol_mu     = None # dual variables for generalized ieqs
        self.sol_info   = None

        # Probability density funciton data
        self.b_sx         = dict(marg_sx)
        self.b_sy         = dict(marg_sy)
        self.b_sz         = dict(marg_sz)
        self.S            =set([ s for s,x in self.b_sx.keys() ]
                               + [ s for s,y in self.b_sy.keys() ]
                               + [ s for s,z in self.b_sz.keys() ])
        self.X            = set( [ x  for s,x in self.b_sx.keys() ] )
        self.Y            = set( [ y  for s,y in self.b_sy.keys() ] )
        self.Z            = set( [ z  for s,z in self.b_sz.keys() ] )
        self.idx_of_quad  = dict()
        self.quad_of_idx  = []

        # Do stuff:
        for s in self.S:
            for x in self.X:
                if (s,x) in self.b_sx.keys():
                    for y in self.Y:
                        if (s,y) in self.b_sy.keys():
                            for z in self.Z:
                                if (s,z) in self.b_sz.keys():
                                    self.idx_of_quad[ (s,x,y,z) ] = len( self.quad_of_idx )
                                    self.quad_of_idx.append( (s,x,y,z) )
                                #^ if
                            #^ for z
                        #^ if
                    #^ for y
                #^ if
            #^ for x
        #^ for s
    #^ init()

    # Creates the optimization problem needed to compute both synergy and unique info 
    def create_model(self):
        # (c) Abdullah Makkeh, Dirk Oliver Theis
        # Permission to use and modify under Apache License version 2.0
        n = len(self.quad_of_idx)
        m = len(self.b_sx) + len(self.b_sy) + len(self.b_sz)
        n_vars = 3*n
        n_cons = n+m

        #
        # Create the equations: Ax = b
        #
        self.b = np.zeros((n_cons,),dtype=np.double)

        Eqn   = []
        Var   = []
        Coeff = []

        # The q-p coupling equations: q_{*xyz} - p_{sxyz} = 0
        for i,sxyz in enumerate(self.quad_of_idx):
            eqn     = i
            p_var   = p_vidx(i)
            Eqn.append( eqn )
            Var.append( p_var )
            Coeff.append( -1. )

            (s,x,y,z) = sxyz
            for u in self.S:
                if (u,x,y,z) in self.idx_of_quad.keys():
                    q_var = q_vidx(self.idx_of_quad[ (u,x,y,z) ])
                    Eqn.append( eqn )
                    Var.append( q_var )
                    Coeff.append( +1. )
                #^ if
            #^ loop *xyz
        #^ for sxyz

        # running number
        eqn = -1 + len(self.quad_of_idx)

        # The sx marginals q_{sx**} = b^x_{sx}
        for s in self.S:
            for x in self.X:
                if (s,x) in self.b_sx.keys():
                    eqn += 1
                    for y in self.Y:
                        for z in self.Z:
                            if (s,x,y,z) in self.idx_of_quad.keys():
                                q_var = q_vidx(self.idx_of_quad[ (s,x,y,z) ])
                                Eqn.append( eqn )
                                Var.append( q_var )
                                Coeff.append( 1. )
                            #^ if
                        #^ for z
                    #^ for y
                    self.b[eqn] = self.b_sx[ (s,x) ]
                #^ if sx exists
            #^ for x
        #^ for s

        # The sy marginals q_{s*y*} = b^y_{sy}
        for s in self.S:
            for y in self.Y:
                if (s,y) in self.b_sy.keys():
                    eqn += 1
                    for x in self.X:
                        for z in self.Z:
                            if (s,x,y,z) in self.idx_of_quad.keys():
                                q_var = q_vidx(self.idx_of_quad[ (s,x,y,z) ])
                                Eqn.append( eqn )
                                Var.append( q_var )
                                Coeff.append( 1. )
                            #^ if
                        #^ for z
                    #^ for x
                    self.b[eqn] = self.b_sy[ (s,y) ]                    
                #^ if sy exists
            #^ for y
        #^ for s

        # The sz marginals q_{s**z} = b^z_{sz}
        for s in self.S:
            for z in self.Z:
                if (s,z) in self.b_sz.keys():
                    eqn += 1
                    for x in self.X:
                        for y in self.Y:
                            if (s,x,y,z) in self.idx_of_quad.keys():
                                q_var = q_vidx(self.idx_of_quad[ (s,x,y,z) ])
                                Eqn.append( eqn )
                                Var.append( q_var )
                                Coeff.append( 1. )
                            #^ if
                        #^ for y
                    #^ for x
                    self.b[eqn] = self.b_sz[ (s,z) ]
                #^ if sz exists
            #^ for z
        #^ for s

        self.A = sparse.csc_matrix( (Coeff, (Eqn,Var)), shape=(n_cons,n_vars), dtype=np.double)

        # Generalized ieqs: gen.nneg of the variable quadruple (r_i,q_i,p_i), i=0,dots,n-1:
        Ieq   = []
        Var   = []
        Coeff = []
        for i,sxyz in enumerate(self.quad_of_idx):
            r_var = r_vidx(i)
            q_var = q_vidx(i)
            p_var = p_vidx(i)

            Ieq.append( len(Ieq) )
            Var.append( r_var )
            Coeff.append( -1. )

            Ieq.append( len(Ieq) )
            Var.append( p_var )
            Coeff.append( -1. )

            Ieq.append( len(Ieq) )
            Var.append( q_var )
            Coeff.append( -1. )
        #^ for sxyz

        self.G         = sparse.csc_matrix( (Coeff, (Ieq,Var)), shape=(n_vars,n_vars), dtype=np.double)
        self.h         = np.zeros( (n_vars,),dtype=np.double )
        self.dims['e'] = n

        # Objective function:
        self.c = np.zeros( (n_vars,),dtype=np.double )
        for i,sxyz in enumerate(self.quad_of_idx):
            self.c[ r_vidx(i) ] = -1.
        #^ for xyz
    #^ create_model()

    def solve(self):
        # (c) Abdullah Makkeh, Dirk Oliver Theis
        # Permission to use and modify under Apache License version 2.0
        self.marg_xyz = None # for cond[]mutinf computation below

        if self.verbose != None:
            self.ecos_kwargs["verbose"] = self.verbose

        solution = ecos.solve(self.c, self.G,self.h, self.dims,  self.A,self.b, **self.ecos_kwargs)

        if 'x' in solution.keys():
            self.sol_rpq    = solution['x']
            self.sol_slack  = solution['s']
            self.sol_lambda = solution['y']
            self.sol_mu     = solution['z']
            self.sol_info   = solution['info']
            return "success"
        else: # "x" not in dict solution
            return "x not in dict solution -- No Solution Found!!!"
        #^ if/esle
    #^ solve()        
    def provide_marginals(self):
        if self.marg_xyz == None:
            self.marg_xyz = dict()
            self.marg_x  = defaultdict(lambda: 0.)
            self.marg_y  = defaultdict(lambda: 0.)
            self.marg_z  = defaultdict(lambda: 0.)
            for x in self.X:
                for y in self.Y:
                    for z in self.Z:
                        xyzsum = 0.
                        for s in self.S:
                            if (s,x,y,z) in self.idx_of_quad.keys():
                                q = self.sol_rpq[ q_vidx(self.idx_of_quad[ (s,x,y,z) ]) ]
                                if q>0:
                                    xyzsum += q
                                    self.marg_x[ x ] += q
                                    self.marg_y[ y ] += q
                                    self.marg_z[ z ] += q
                                #^ if q>0
                            #^if
                        #^ for s
                        if xyzsum > 0. :    self.marg_xyz[ (x,y,z) ] = zysum
                    #^ for z
                #^ for y
            #^ for x
        #^ if ∄ marg_xyz
    #^ provide_marginals()

    # def condYmutinf(self):
    #     self.provide_marginals()

    #     mysum = 0.
    #     for x in self.X:
    #         for z in self.Z:
    #             if not (x,z) in self.b_xz.keys(): continue
    #             for y in self.Y:
    #                 if (x,y,z) in self.idx_of_trip.keys():
    #                     i = q_vidx(self.idx_of_trip[ (x,y,z) ])
    #                     q = self.sol_rpq[i]
    #                     if q > 0:  mysum += q*log( q * self.marg_y[y] / ( self.b_xy[ (x,y) ] * self.marg_yz[ (y,z) ] ) )
    #                 #^ if
    #             #^ for i
    #         #^ for z
    #     #^ for x
    #     return mysum
    # #^ condYmutinf()

    # def condZmutinf(self):
    #     self.provide_marginals()

    #     mysum = 0.
    #     for x in self.X:
    #         for y in self.Y:
    #             if not (x,y) in self.b_xy.keys(): continue
    #             for z in self.Z:
    #                 if (x,y,z) in self.idx_of_trip.keys():
    #                     i = q_vidx(self.idx_of_trip[ (x,y,z) ])
    #                     q = self.sol_rpq[i]
    #                     if q > 0:  mysum += q*log( q * self.marg_z[z] / ( self.b_xz[ (x,z) ] * self.marg_yz[ (y,z) ] ) )
    #                 #^ if
    #             #^ for z
    #         #^ for y
    #     #^ for x
    #     return mysum
    # #^ condZmutinf()

    def entropy_S(self,pdf):
        mysum = 0.
        for s in self.S:
            psum = 0.
            for x in self.X:
                if not (s,x) in self.b_sx: continue
                for y in self.Y:
                    if not (s,y) in self.b_sy:  continue
                    for z in self.Z:
                        if (s,x,y,z) in pdf.keys():
                            psum += pdf[(s,x,y,z)]
                        #^ if
                    #^ for z
                #^ for y
            #^ for x
            mysum -= psum * log(psum)
        #^ for x
        return mysum
    #^ entropy_S()

    def condentropy(self):
        # compute cond entropy of the distribution in self.sol_rpq
        mysum = 0.
        for x in self.X:
            for y in self.Y:
                for z in self.Z:
                    marg_s = 0.
                    q_list = [ q_vidx(self.idx_of_quad[ (s,x,y,z) ]) for s in self.S if (s,x,y,z) in self.idx_of_quad.keys()]
                    for i in q_list:
                        marg_s += max(0,self.sol_rpq[i])
                    for i in q_list:
                        q = self.sol_rpq[i]
                        if q > 0:  mysum -= q*log(q/marg_s)
                    #^ for i
                #^ for z
            #^ for y
        #^ for x
        return mysum
    #^ condentropy()

    def condentropy__orig(self,pdf):
        mysum = 0.
        for x in self.X:
            for y in self.Y:
                for z in self.Z:
                    s_list = [ s  for s in self.S if (s,x,y,z) in pdf.keys()]
                    marg = 0.
                    for s in s_list: marg += pdf[(s,x,y,z)]
                    for s in s_list:
                        p = pdf[(s,x,y,z)]
                        mysum -= p*log(p/marg)
                    #^ for xyz
                #^ for z
            #^ for y
        #^ for x
        return mysum
    #^ condentropy__orig()

    def dual_value(self):
        return -np.dot(self.sol_lambda, self.b)
    #^ dual_value()
    
    def check_feasibility(self): # returns pair (p,d) of primal/dual infeasibility (maxima)
        # Primal infeasiblility
        # ---------------------
        max_q_negativity = 0.
        for i in range(len(self.quad_of_idx)):
            max_q_negativity = max(max_q_negativity, -self.sol_rpq[q_vidx(i)])
        #^ for
        max_violation_of_eqn = 0.
        # sx** - marginals:
        for sx in self.b_sx.keys():
            mysum = self.b_sx[sx]
            for y in self.Y:
                for z in self.Z:
                    s,x = sx
                    if (s,x,y,z) in self.idx_of_quad.keys():
                        i = self.idx_of_quad[(s,x,y,z)]
                        q = max(0., self.sol_rpq[q_vidx(i)])
                        mysum -= q
                    #^ if
                #^ for z
            #^ for y 
            max_violation_of_eqn = max( max_violation_of_eqn, abs(mysum) )
        #^ fox sx
        # s*y* - marginals:
        for sy in self.b_sy.keys():
            mysum = self.b_sy[sy]
            for x in self.X:
                for z in self.Z:
                    s,y = sy
                    if (s,x,y,z) in self.idx_of_quad.keys():
                        i = self.idx_of_quad[(s,x,y,z)]
                        q = max(0., self.sol_rpq[q_vidx(i)])
                        mysum -= q
                    #^ if
                #^ for z
            #^ for x
            max_violation_of_eqn = max( max_violation_of_eqn, abs(mysum) )
        #^ fox sy
        # s**z - marginals:
        for sz in self.b_sz.keys():
            mysum = self.b_sz[sz]
            for x in self.X:
                for y in self.Y:
                    s,z = sz
                    if (s,x,y,z) in self.idx_of_quad.keys():
                        i = self.idx_of_quad[(s,x,y,z)]
                        q = max(0., self.sol_rpq[q_vidx(i)])
                        mysum -= q
                    #^ if
                #^ for y
            #^ for x
            max_violation_of_eqn = max( max_violation_of_eqn, abs(mysum) )
        #^ fox sz

        primal_infeasability = max(max_violation_of_eqn,max_q_negativity)
        
        # Dual infeasiblility
        # -------------------
        idx_of_sx = dict()
        i = 0
        for s in self.S:
            for x in self.X:
                if (s,x) in self.b_sx.keys():
                    idx_of_sx[(s,x)] = i
                    i += 1
                #^ if sx exists
            #^ for x
        #^ for s

        idx_of_sy = dict()
        i = 0
        for s in self.S:
            for y in self.Y:
                if (s,y) in self.b_sy.keys():
                    idx_of_sy[(s,y)] = i
                    i += 1
                #^ if sy exists
            #^ for y
        #^ for s

        idx_of_sz = dict()
        i = 0
        for s in self.S:
            for z in self.Z:
                if (s,z) in self.b_sz.keys():
                    idx_of_sz[(s,z)] = i
                    i += 1
                #^ if sz exists
            #^ for z
        #^ for s

        dual_infeasability = 0.
        for i,sxyz in enumerate(self.quad_of_idx):
            mu_xyz = 0.
            s,x,y,z = sxyz
            # Compute mu_*xyz
            # mu_xyz: dual variable of the coupling constraints
            for j,tuvw in enumerate(self.quad_of_idx):
                t,u,v,w = tuvw
                if u == x and v == y and w == z:
                    mu_xyz += self.sol_lambda[j]

            # Get indices of dual variables of the marginal constriants
            sx_idx = len(self.quad_of_idx) + idx_of_sx[(s,x)]
            sy_idx = len(self.quad_of_idx) + len(self.b_sx) + idx_of_sy[(s,y)]
            sz_idx = len(self.quad_of_idx) + len(self.b_sx) + len(self.b_sy) + idx_of_sz[(s,z)]

            # Find the most violated dual ieq
            dual_infeasability = max( dual_infeasability, - self.sol_lambda[sx_idx]
                                                          - self.sol_lambda[sy_idx]
                                                          - self.sol_lambda[sz_idx]
                                                          - mu_xyz
                                                          -ln(-self.sol_lambda[i])
                                                          - 1
                                    )
        #^ for

        return primal_infeasability, dual_infeasability
    #^ check_feasibility()

#^ class Solve_w_ECOS


def marginal_sx(p):
    marg = dict()
    for sxyz,r in p.items():
        s,x,y,z = sxyz
        if (s,x) in marg.keys():    marg[(s,x)] += r
        else:                       marg[(s,x)] =  r
    return marg

def marginal_sy(p):
    marg = dict()
    for sxyz,r in p.items():
        s,x,y,z = sxyz
        if (s,y) in marg.keys():   marg[(s,y)] += r
        else:                      marg[(s,y)] =  r
    return marg

def marginal_sz(p):
    marg = dict()
    for sxyz,r in p.items():
        s,x,y,z = sxyz
        if (s,z) in marg.keys():   marg[(s,z)] += r
        else:                      marg[(s,z)] =  r
    return marg

# def I_X_Y(p):
#     # Mutual information I( X ; Y )
#     mysum   = 0.
#     marg_x  = defaultdict(lambda: 0.)
#     marg_y  = defaultdict(lambda: 0.)
#     b_xy    = marginal_xy(p)
#     for xyz,r in p.items():
#         x,y,z = xyz
#         if r > 0 :
#             marg_x[x] += r
#             marg_y[y] += r
    
#     for xy,t in b_xy.items():
#         x,y = xy
#         if t > 0:  mysum += t * log( t / ( marg_x[x]*marg_y[y] ) )
#     return mysum
# #^ I_X_Y()

# def I_X_Z(p):
#     # Mutual information I( X ; Z )
#     mysum   = 0.
#     marg_x  = defaultdict(lambda: 0.)
#     marg_z  = defaultdict(lambda: 0.)
#     b_xz    = marginal_xz(p)
#     for xyz,r in p.items():
#         x,y,z = xyz
#         if r > 0 :
#             marg_x[x] += r
#             marg_z[z] += r
    
#     for xz,t in b_xz.items():
#         x,z = xz
#         if t > 0:  mysum += t * log( t / ( marg_x[x]*marg_z[z] ) )
#     return mysum
# #^ I_X_Z()

# def I_X_YZ(p):
#     # Mutual information I( X ; Y , Z )
#     mysum    = 0.
#     marg_x   = defaultdict(lambda: 0.)
#     marg_yz  = defaultdict(lambda: 0.)
#     for xyz,r in p.items():
#         x,y,z = xyz
#         if r > 0 :
#             marg_x[x]      += r
#             marg_yz[(y,z)] += r
    
#     for xyz,t in p.items():
#         x,y,z = xyz
#         if t > 0:  mysum += t * log( t / ( marg_x[x]*marg_yz[(y,z)] ) )
#     return mysum
# #^ I_X_YZ()

def pid(pdf_dirty, cone_solver="ECOS", output=0, **solver_args):
    # (c) Abdullah Makkeh, Dirk Oliver Theis
    # Permission to use and modify under Apache License version 2.0
    assert type(pdf_dirty) is dict, "chicharro_pid.pid(pdf): pdf must be a dictionary"
    assert type(cone_solver) is str, "chicharro_pid.pid(pdf): `cone_solver' parameter must be string (e.g., 'ECOS')"
    if __debug__:
        for k,v in pdf_dirty.items():
            assert type(k) is tuple or type(k) is list,           "chicharro_2pid.pid(pdf): pdf's keys must be tuples or lists"
            assert len(k)==4,                                     "chicharro_pid.pid(pdf): pdf's keys must be tuples/lists of length 4"
            assert type(v) is float or ( type(v)==int and v==0 ), "chicharro_pid.pid(pdf): pdf's values must be floats"
            assert v > -.1,                                       "chicharro_pid.pid(pdf): pdf's values must not be negative"
        #^ for
    #^ if
    assert type(output) is int, "chicharro_pid.pid(pdf,output): output must be an integer"

    # Check if the solver is implemented:
    assert cone_solver=="ECOS", "chicharro_pid.pid(pdf): We currently don't have an interface for the Cone Solver "+cone_solver+" (only ECOS)."

    pdf = { k:v  for k,v in pdf_dirty.items() if v > 1.e-300 }

    bx_sx = marginal_sx(pdf)
    by_sy = marginal_sy(pdf)
    bz_sz = marginal_sz(pdf)

    # if cone_solver=="ECOS": .....
    if output > 0:  print("BROJA_2PID: Preparing Cone Program data",end="...")
    solver = Solve_w_ECOS(bx_sx, by_sy, bz_sz)
    solver.create_model()
    if output > 1: solver.verbose = True

    ecos_keep_solver_obj = False
    if 'keep_solver_object' in solver_args.keys():
        if solver_args['keep_solver_object']==True: ecos_keep_solver_obj = True
        del solver_args['keep_solver_object']

    solver.ecos_kwargs = solver_args

    if output > 0: print("done.")

    if output == 1: print("Chicharro_pid: Starting solver",end="...")
    if output > 1: print("Chicharro_pid: Starting solver.")
    retval = solver.solve()
    if retval != "success":
        print("\nCone Programming solver failed to find (near) optimal solution.\nPlease report the input probability density function to abdullah.makkeh@gmail.com\n")
        if ecos_keep_solver_obj:
            return solver
        else:
            raise Chicharro_pid_Exception("Chicharro_pid_Exception: Cone Programming solver failed to find (near) optimal solution. Please report the input probability density function to abdullah.makkeh@gmail.com")
        #^ if (keep solver)
    #^ if (solve failure)

    if output > 0:  print("\nChicharro_pid: done.")

    if output > 1:  print(solver.sol_info)

    # entropy_X     = solver.entropy_X(pdf)
    condent       = solver.condentropy()
    condent__orig = solver.condentropy__orig(pdf)
    # condYmutinf   = solver.condYmutinf()
    # condZmutinf   = solver.condZmutinf()
    dual_val      = solver.dual_value()
    bits = 1/log(2)

    # elsif cone_solver=="SCS":
    # .....
    # #^endif


    return_data = dict()
    # return_data["SI"]  = ( entropy_X - condent - condZmutinf - condYmutinf ) * bits
    # return_data["UIY"] = ( condZmutinf                                     ) * bits
    # return_data["UIZ"] = ( condYmutinf                                     ) * bits
    return_data["CI"]  = ( condent - condent__orig                         ) * bits
    
    primal_infeas,dual_infeas = solver.check_feasibility()
    return_data["Num_err"] = (primal_infeas, dual_infeas, max(-condent*ln(2) - dual_val, 0.0))
    return_data["Solver"] = "ECOS http://www.embotech.com/ECOS"

    if ecos_keep_solver_obj:
        return_data["Solver Object"] = solver
    #^ if (keep solver)

    return return_data
#^ pid()

#EOF