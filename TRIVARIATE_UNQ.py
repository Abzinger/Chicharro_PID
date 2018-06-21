# TRIVARIATE_SYN.py
import ecos
from scipy import sparse
import numpy as np
from numpy import linalg as LA
import math
# from collections import defaultdict
ln  = math.log
log = math.log2
# Creates the optimization problem needed to compute both synergy (also needed for uniqueness)

def core_initialization(_S, X_1, X_2, b_sx1, b_sx2, idx_of, of_idx):
    for s in _S:
        for x1 in X_1:
            if (s,x1) in b_sx1.keys():
                for x2 in X_2:
                    if (s,x2) in b_sx2.keys():
                        idx_of[ (s,x1,x2) ] = len(of_idx)
                        of_idx.append( (s,x1,x2) )
                    #^ if sx2
                #^ for x2
            #^if sx1
        #^ for x1
    #^ for s
def initialization(self, which_sources):
    idx_of_trip  = dict()
    trip_of_idx  = []

    if which_sources == [1,2]:
        core_initialization(self.S, self.X, self.Y, self.b_sx, self.b_sy, idx_of_trip, trip_of_idx)
    elif which_sources == [1,3]:
        core_initialization(self.S, self.X, self.Z, self.b_sx, self.b_sz, idx_of_trip, trip_of_idx)
    elif which_sources == [2,3]:
        core_initialization(self.S, self.Y, self.Z, self.b_sy, self.b_sz, idx_of_trip, trip_of_idx)
    return idx_of_trip, trip_of_idx
#^ initialization 

# ECOS's exp cone: (r,p,w)     w/   w>0  &  exp(r/w) ≤ p/w
# Variables here:  (r,p,w)U(q)
# Translation:     (0,1,2,3)   w/   2>0  &  0/2      ≤ ln(1/2)
def sr_vidx(i):
    return 3*i
def sp_vidx(i):
    return 3*i+1
def sw_vidx(i):
    return 3*i+2
def sq_vidx(self, i, which_sources):
    idx_of_trip,trip_of_idx = self.initialization(which_sources)
    return 3*len(trip_of_idx) + i

def create_model(self, which_sources):
    # (c) Abdullah Makkeh, Dirk Oliver Theis
    # Permission to use and modify under Apache License version 2.0

    # Initialize which sources for the model

    idx_of_trip,trip_of_idx = self.initialization(which_sources)
    m = len(self.b_sx) + len(self.b_sy) + len(self.b_sz)
    if which_sources == [1,2]:
        n = len(trip_of_idx)
    elif which_sources == [1,3]:
        n = len(trip_of_idx)
    elif which_sources == [2,3]:
        n = len(trip_of_idx)        
    #^ if 

    n_vars = 3*n + len(self.quad_of_idx)
    n_cons = 2*n + m

    # Create the equations: Ax = b
    self.b = np.zeros((n_cons,),dtype=np.double)
    
    Eqn   = []
    Var   = []
    Coeff = []

    # The q-w coupling eqautions:
    #         if Sources = X,Y  q_{stv*} - w_{stv} = 0
    #         if Sources = X,Z  q_{st*v} - w_{stv} = 0
    #         if Sources = Y,Z  q_{s*tv} - w_{stv} = 0
    for i,stv in enumerate(trip_of_idx):
        eqn   = i
        w_var = sw_vidx(i)
        Eqn.append( eqn )
        Var.append( w_var )
        Coeff.append( -1. )
        (s,t,v) = stv
        if which_sources == [1,2]:
            for u in self.Z:
                if (s,t,v,u) in self.idx_of_quad.keys(): 
                    q_var = self.sq_vidx(self.idx_of_quad[ (s,t,v,u) ], which_sources)
                    Eqn.append( eqn )
                    Var.append( q_var )
                    Coeff.append( +1. )
                #^ if q_{stv*}
            #^ loop *xy*                
        #^ if SXY
        elif which_sources == [1,3]:  
            for u in self.Y:
                if (s,t,u,v) in self.idx_of_quad.keys(): 
                    q_var = self.sq_vidx(self.idx_of_quad[ (s,t,u,v) ], which_sources)
                    Eqn.append( eqn )
                    Var.append( q_var )
                    Coeff.append( +1. )
                #^ if q_{st*v}
            #^ loop *x*z                
        #^ if SXZ
        elif which_sources == [2,3]:
            for u in self.X:
                if (s,u,t,v) in self.idx_of_quad.keys(): 
                    q_var = self.sq_vidx(self.idx_of_quad[ (s,u,t,v) ], which_sources)
                    Eqn.append( eqn )
                    Var.append( q_var )
                    Coeff.append( +1. )
                #^ if q_{s*tv}
            #^ loop **yz                
        #^if SYZ

    # running number
    eqn = -1 + len(trip_of_idx)
    
    # The q-p coupling equations:
    #         if Sources = X,Y  q_{*tv*} - p_{stv} = 0
    #         if Sources = X,Z  q_{*t*v} - p_{stv} = 0
    #         if Sources = Y,Z  q_{**tv} - p_{stv} = 0
    
    for i,stv in enumerate(trip_of_idx):
        eqn     += 1
        p_var   = sp_vidx(i)
        Eqn.append( eqn )
        Var.append( p_var )
        Coeff.append( -1. )
        
        (s,t,v) = stv
        if which_sources == [1,2]:
            for u1 in self.S:
                for u2 in self.Z: 
                    if (u1,t,v,u2) in self.idx_of_quad.keys(): 
                        q_var = self.sq_vidx(self.idx_of_quad[ (u1,t,v,u2) ], which_sources)
                        Eqn.append( eqn )
                        Var.append( q_var )
                        Coeff.append( +1. )
                    #^ if q_{*tv*}
                #^ for u2
            #^ loop *xy*
        #^ if SXY
        elif which_sources == [1,3]:
            for u1 in self.S:
                for u2 in self.Y: 
                    if (u1,t,u2,v) in self.idx_of_quad.keys(): 
                        q_var = self.sq_vidx(self.idx_of_quad[ (u1,t,u2,v) ], which_sources)
                        Eqn.append( eqn )
                        Var.append( q_var )
                        Coeff.append( +1. )
                    #^ if q_{*t*v}
                #^ for v
            #^ loop *x*z
        #^ if SXZ
        elif which_sources == [2,3]:
            for u1 in self.S:
                for u2 in self.X: 
                    if (u1,u2,t,v) in self.idx_of_quad.keys(): 
                        q_var = self.sq_vidx(self.idx_of_quad[ (u1,u2,t,v) ], which_sources)
                        Eqn.append( eqn )
                        Var.append( q_var )
                        Coeff.append( +1. )
                    #^ if
                #^ for v
            #^ loop **yz
        #^ if SYZ
    #^ for SX_1X_2
    
    # # running number
    # eqn += len(self.trip_of_idx)
    
    # The sx marginals q_{sx**} = b^x_{sx}
    for s in self.S:
        for x in self.X:
            if (s,x) in self.b_sx.keys():
                eqn += 1
                for y in self.Y:
                    for z in self.Z:
                        if (s,x,y,z) in self.idx_of_quad.keys():
                            q_var = self.sq_vidx(self.idx_of_quad[ (s,x,y,z) ], which_sources)
                            Eqn.append( eqn )
                            Var.append( q_var )
                            Coeff.append( 1. )
                        #^ if sxyz exists
                        self.b[eqn] = self.b_sx[ (s,x) ]
                    #^ for z
                #^ for y
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
                            q_var = self.sq_vidx(self.idx_of_quad[ (s,x,y,z) ], which_sources)
                            Eqn.append( eqn )
                            Var.append( q_var )
                            Coeff.append( 1. )
                        #^ if sxyz exists
                        self.b[eqn] = self.b_sy[ (s,y) ]
                    #^ for z
                #^ for x
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
                            q_var = self.sq_vidx(self.idx_of_quad[ (s,x,y,z) ], which_sources)
                            Eqn.append( eqn )
                            Var.append( q_var )
                            Coeff.append( 1. )
                        #^ if sxyz exits
                        self.b[eqn] = self.b_sz[ (s,z) ]
                    #^ for y
                #^ for x
            #^ if sz exists
        #^ for z
    #^ for s

    self.A = sparse.csc_matrix( (Coeff, (Eqn,Var)), shape=(n_cons,n_vars), dtype=np.double)
    
    # Generalized ieqs: gen.nneg of the variable triple (r_i,w_i,p_i), i=0,dots,n-1: 
    Ieq   = []
    Var   = []
    Coeff = []

    # Adding q_{s,x,y,z} >= 0 or q_{s,x,y,z} is free variable

    for i,sxyz in enumerate(self.quad_of_idx):
        q_var = self.sq_vidx(i, which_sources)
        Ieq.append( len(Ieq) )
        Var.append( q_var )
        Coeff.append( -1. )
    #^ for sxyz

    for i,stv in enumerate(trip_of_idx):
        r_var = sr_vidx(i)
        w_var = sw_vidx(i)
        p_var = sp_vidx(i)
        
        Ieq.append( len(Ieq) )
        Var.append( r_var )
        Coeff.append( -1. )
        
        Ieq.append( len(Ieq) )
        Var.append( p_var )
        Coeff.append( -1. )
        
        Ieq.append( len(Ieq) )
        Var.append( w_var )
        Coeff.append( -1. )
    #^ for stv

    self.G         = sparse.csc_matrix( (Coeff, (Ieq,Var)), shape=(n_vars,n_vars), dtype=np.double)
    self.h         = np.zeros( (n_vars,),dtype=np.double )
    self.dims = dict()
    self.dims['e'] = n
    self.dims['l'] = len(self.quad_of_idx)
    
    # Objective function:
    self.c = np.zeros( (n_vars,),dtype=np.double )
    for i,stv in enumerate(trip_of_idx):
        self.c[ sr_vidx(i) ] = -1.
    #^ for stv

    return self.c, self.G, self.h, self.dims, self.A, self.b

#^ create_model()

# def solve(self):
#     # (c) Abdullah Makkeh, Dirk Oliver Theis
#     # Permission to use and modify under Apache License version 2.0
#     self.marg_xyz = None # for cond[]mutinf computation below
    
#     if self.verbose != None:
#         print(self.verbose)
#         self.ecos_kwargs["verbose"] = self.verbose
#     #^ if    
#     solution = ecos.solve(self.c, self.G,self.h, self.dims,  self.A,self.b, **self.ecos_kwargs)

#     if 'x' in solution.keys():
#         self.sol_rpq    = solution['x']
#         self.sol_slack  = solution['s']
#         self.sol_lambda = solution['y']
#         self.sol_mu     = solution['z']
#         self.sol_info   = solution['info']
#         return "success", self.sol_info
#     else: # "x" not in dict solution
#         return "x not in dict solution -- No Solution Found!!!"
#     #^ if/esle
# #^ solve()

def solve(self, c, G, h, dims, A, b):
    # (c) Abdullah Makkeh, Dirk Oliver Theis
    # Permission to use and modify under Apache License version 2.0
    self.marg_xyz = None # for cond[]mutinf computation below
    
    if self.verbose != None:
        # print(self.verbose)
        self.ecos_kwargs["verbose"] = self.verbose
    #^ if
    
    solution = ecos.solve(c, G, h, dims, A, b, **self.ecos_kwargs)

    if 'x' in solution.keys():
        self.sol_rpq    = solution['x']
        self.sol_slack  = solution['s']
        self.sol_lambda = solution['y']
        self.sol_mu     = solution['z']
        self.sol_info   = solution['info']
        return "success", self.sol_rpq, self.sol_slack, self.sol_lambda, self.sol_mu, self.sol_info
    else: # "x" not in dict solution
        return "x not in dict solution -- No Solution Found!!!"
    #^ if/esle
#^ solve()

def check_feasibility(self, which_sources, sol_rpq, sol_slack, sol_lambda, sol_mu):
    # returns pair (p,d) of primal/dual infeasibility (maxima)

    idx_of_trip,trip_of_idx = self.initialization(which_sources)

    # Primal infeasiblility
    
    # non-negative ineqaulity 
    max_q_negativity = 0.
    for i in range(len(self.quad_of_idx)):
        max_q_negativity = max(max_q_negativity, -sol_rpq[self.sq_vidx(i, which_sources)])
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
                    q = max(0., sol_rpq[self.sq_vidx(i, which_sources)])
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
                    q = max(0., sol_rpq[self.sq_vidx(i, which_sources)])
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
                    q = max(0., sol_rpq[self.sq_vidx(i, which_sources)])
                    mysum -= q
                #^ if
            #^ for y
        #^ for x
        max_violation_of_eqn = max( max_violation_of_eqn, abs(mysum) )
    #^ fox sz

    primal_infeasability = max(max_violation_of_eqn, max_q_negativity)
    
    # Dual infeasiblility

    dual_infeasability = 0.

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

    # non-negativity dual ineqaulity

    print(sol_lambda)
    for i,sxyz in enumerate(self.quad_of_idx):
        s,x,y,z = sxyz

        # nu_sxy: dual variable of the q-w coupling constraints
        nu_sxy = sol_lambda[i]

        # mu_xy: dual varaible of the q-t coupling contsraints 
        mu_xy = 0.

        for j,tuv in enumerate(trip_of_idx):
            t,u,v = tuv
            if u == x and v == y:
                mu_idx = j + len(trip_of_idx)
                mu_xy += sol_lambda[mu_idx]
            #^if xy exits
        # Get indices of dual variables of the marginal constriants
        sx_idx = 2*len(trip_of_idx) + idx_of_sx[(s,x)]
        sy_idx = 2*len(trip_of_idx) + len(self.b_sx) + idx_of_sy[(s,y)]
        sz_idx = 2*len(trip_of_idx) + len(self.b_sx) + len(self.b_sy) + idx_of_sz[(s,z)]

        # Find the most vaiolated dual ieq
        # two types of ieq:
        #                 (a,b,c) <_{kexp} 0
        #                  a      <= 0
        print("nonnegative: ", sol_lambda[sx_idx]
              + sol_lambda[sy_idx]
              + sol_lambda[sz_idx]
              + mu_xy
              + nu_sxy
        )
        dual_infeasability = max(dual_infeasability, sol_lambda[sx_idx]
                                         + sol_lambda[sy_idx]
                                         + sol_lambda[sz_idx]
                                         + mu_xy
                                         + nu_sxy
                )
        #^ for
    #^ for
    print("trip_of_idx: ", trip_of_idx)
    for k, sxy in enumerate(trip_of_idx):
        s,x,y = sxy

        # nu_sxy: dual variable of the q-w coupling constraints
        nu_sxy = sol_lambda[k]

        # mu_xy: dual varaible of the q-t coupling contsraints 
        mu_xy = 0.

        for j,tuv in enumerate(trip_of_idx):
            t,u,v = tuv
            if u == x and v == y:
                mu_idx = j + len(trip_of_idx)
                mu_xy += sol_lambda[mu_idx]
            #^if uv exits
        # for s
        print("mu_xy: ", mu_xy)
        print("lg mu:", ln(-sol_lambda[len(trip_of_idx) + k]))
        # Get indices of dual variables of the marginal constriants
        sx_idx = 2*len(trip_of_idx) + idx_of_sx[(s,x)]
        sy_idx = 2*len(trip_of_idx) + len(self.b_sx) + idx_of_sy[(s,y)]
        print(sol_lambda[len(trip_of_idx) +k])
        print("dual of kexp: ", sol_lambda[sx_idx]
              + sol_lambda[sy_idx]
              + mu_xy
              - nu_sxy
              +ln(-sol_lambda[len(trip_of_idx) + k])
              +1)
    #^ for 

    
    # for i,sxyz in enumerate(self.quad_of_idx):
    #     mu_xyz = 0.
    #     s,x,y,z = sxyz
    #     # Compute mu_*xyz
    #     # mu_xyz: dual variable of the coupling constraints
    #     for j,tuvw in enumerate(self.quad_of_idx):
    #         t,u,v,w = tuvw
    #         if u == x and v == y and w == z:
    #             mu_xyz += self.sol_lambda[j]
    #         #^ if
    #     # Get indices of dual variables of the marginal constriants
    #     sx_idx = len(self.quad_of_idx) + idx_of_sx[(s,x)]
    #     sy_idx = len(self.quad_of_idx) + len(self.b_sx) + idx_of_sy[(s,y)]
    #     sz_idx = len(self.quad_of_idx) + len(self.b_sx) + len(self.b_sy) + idx_of_sz[(s,z)]
        
    #     # Find the most violated dual ieq
    #     dual_infeasability = max( dual_infeasability, - self.sol_lambda[sx_idx]
    #                               - self.sol_lambda[sy_idx]
    #                               - self.sol_lambda[sz_idx]
    #                               - mu_xyz
    #                               -ln(-self.sol_lambda[i])
    #                               - 1
    #     )
    # #^ for

    return primal_infeasability, dual_infeasability
#^ check_feasibility()    

def dual_value(self, b):
    return -np.dot(self.sol_lambda, b)

def marginal_ab(self,_A, _B, _C, _D, which_sources, sol_rpq):
    # provide the positive marginals all (a,b) in a system  (a,b,c,d)
    marg_12 = dict()
    marg_13 = dict()
    marg_14 = dict()
    marg_23 = dict()
    marg_24 = dict()
    marg_34 = dict()
    for abcd in self.idx_of_quad.keys():
        a,b,c,d = abcd
        if (a,b) in marg_12.keys():
            marg_12[(a,b)] += max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        else:
            marg_12[(a,b)] = max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        #^ if
    #^ for 

    for abcd in self.idx_of_quad.keys():
        a,b,c,d = abcd
        if (a,c) in marg_13.keys():
            marg_13[(a,c)] += max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        else:
            marg_13[(a,c)] = max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        #^ if
    #^ for 

    for abcd in self.idx_of_quad.keys():
        a,b,c,d = abcd
        if (a,d) in marg_14.keys():
            marg_14[(a,d)] += max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        else:
            marg_14[(a,d)] = max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        #^ if
    #^ for 

    for abcd in self.idx_of_quad.keys():
        a,b,c,d = abcd
        if (b,c) in marg_23.keys():
            marg_23[(b,c)] += max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        else:
            marg_23[(b,c)] = max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        #^ if
    #^ for

    for abcd in self.idx_of_quad.keys():
        a,b,c,d = abcd
        if (b,d) in marg_24.keys():
            marg_24[(b,d)] += max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        else:
            marg_24[(b,d)] = max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        #^ if
    #^ for

    for abcd in self.idx_of_quad.keys():
        a,b,c,d = abcd
        if (c,d) in marg_34.keys():
            marg_34[(c,d)] += max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        else:
            marg_34[(c,d)] = max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        #^ if 
    #^ for
    return marg_12, marg_13, marg_14, marg_23, marg_24, marg_34
#^ marginal_ab()

def marginal_abc(self, _A, _B, _C, _D, which_sources, sol_rpq):
    # provide the positive marginals all (a,b,c) in a system  (a,b,c,d)
    marg = dict()
    for a in _A:
        for b in _B:
            for c in _C:
                for d in _D:
                    if which_sources == [1,2]: w = (a,b,c,d)
                    elif which_sources == [1,3]: w = (a,b,d,c)
                    elif which_sources == [2,3]: w = (a,d,b,c)                    
                    if w in self.idx_of_quad.keys():
                        if (a,b,c) in marg.keys():
                            marg[(a,b,c)] += max(0,sol_rpq[self.sq_vidx(self.idx_of_quad[ w ], which_sources)])
                        else:
                            marg[(a,b,c)] = max(0,sol_rpq[self.sq_vidx(self.idx_of_quad[ w ], which_sources)])
                        #^ if (a,b,c) is a key
                    #^ if w exists
                #^ for d
            #^ for c
        #^for b
    #^ for a 
    return marg
#^ marginal_abc()

def condentropy_2vars(self, which_sources, sol_rpq):
    # compute cond entropy of the distribution in self.sol_rpq
    mysum = 0.
    idx_of_trip,trip_of_idx = self.initialization(which_sources)
    if which_sources == [1,2]:
        # H( S | X, Y )
        marg_SX, marg_SY, marg_SZ, marg_XY, marg_XZ, marg_YZ = self.marginal_ab(self.S, self.X, self.Y, self.Z, which_sources, sol_rpq)
        marg_SXY = self.marginal_abc(self.S, self.X, self.Y, self.Z, which_sources, sol_rpq)
        for s in self.S:
            for x in self.X:
                for y in self.Y:
                    if (s,x,y) in idx_of_trip.keys():
                        # subtract q_{sxy}*log( q_{sxy}/q_{xy} )
                        mysum -= marg_SXY[(s,x,y)]*log(marg_SXY[(s,x,y)]/marg_XY[(x,y)])
        return mysum
    #^ if sources
    elif which_sources == [1,3]:
        # H( S | X, Z )
        marg_SX, marg_SY, marg_SZ, marg_XY, marg_XZ, marg_YZ = self.marginal_ab(self.S, self.X, self.Y, self.Z, which_sources, sol_rpq)
        marg_SXZ = self.marginal_abc(self.S, self.X, self.Z, self.Y, which_sources, sol_rpq)
        for s in self.S:
            for x in self.X:
                for z in self.Z:
                    if (s,x,z) in idx_of_trip.keys():
                        # subtract q_{sxy}*log( q_{sxy}/q_{xy} )
                        mysum -= marg_SXZ[(s,x,z)]*log(marg_SXZ[(s,x,z)]/marg_XZ[(x,z)])
        return mysum
    #^ if sources
    elif which_sources == [2,3]:
        # H( S | Y, Z )
        marg_SX, marg_SY, marg_SZ, marg_XY, marg_XZ, marg_YZ = self.marginal_ab(self.S, self.X, self.Y, self.Z, which_sources, sol_rpq)
        marg_SYZ = self.marginal_abc(self.S, self.Y, self.Z, self.X, which_sources, sol_rpq)
        for s in self.S:
            for y in self.Y:
                for z in self.Z:
                    if (s,y,z) in idx_of_trip.keys():
                        # subtract q_{sxy}*log( q_{sxy}/q_{xy} )
                        mysum -= marg_SYZ[(s,y,z)]*log(marg_SYZ[(s,y,z)]/marg_YZ[(y,z)])
        return mysum

    #^ if sources
#^ condentropy_2vars()

def marginal_a(self,_A, _B, _C, _D, which_sources, sol_rpq):
    # provide the positive marginals all a in a system  (a,b,c,d)
    marg_1 = dict()
    marg_2 = dict()
    marg_3 = dict()
    marg_4 = dict()
    for abcd in self.idx_of_quad.keys():
        a,b,c,d = abcd
        if a in marg_1.keys():
            marg_1[a] += max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        else:
            marg_1[a] = max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        #^ if
    #^ for
    for abcd in self.idx_of_quad.keys():
        a,b,c,d = abcd
        if b in marg_2.keys():
            marg_2[b] += max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        else:
            marg_2[b] = max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        #^ if
    #^ for
    for abcd in self.idx_of_quad.keys():
        a,b,c,d = abcd
        if c in marg_3.keys():
            marg_3[c] += max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        else:
            marg_3[c] = max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        #^ if
    #^ for
    for abcd in self.idx_of_quad.keys():
        a,b,c,d = abcd
        if d in marg_4.keys():
            marg_4[d] += max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        else:
            marg_4[d] = max(0, sol_rpq[self.sq_vidx(self.idx_of_quad[ (a,b,c,d) ], which_sources)])
        #^ if
    #^ for
    return marg_1, marg_2, marg_3, marg_4
#^ marginal_ab()


def condentropy_1var(self,which_sources,sol_rpq):
    mysum = 0. 
    if which_sources == [1,2]:
        # H( S | Z )
        marg_S,marg_X,marg_Y,marg_Z = self.marginal_a(self.S, self.X, self.Y, self.Z, which_sources, sol_rpq)
        marg_SX, marg_SY, marg_SZ, marg_XY, marg_XZ, marg_YZ = self.marginal_ab(self.S, self.X, self.Y, self.Z, which_sources, sol_rpq)
        for s in self.S:
            for z in self.Z:
                if (s,z) in self.b_sz.keys():
                    # Subtract q_{s,z}*log( q_{s,z}/ q_{z} )
                    mysum -= marg_SZ[(s,z)]*log(marg_SZ[(s,z)]/marg_Z[z])
                #^ if sz exists
            #^ for z 
        #^ for z
        return mysum
    #^ if sources
    elif which_sources == [1,3]:
        # H( S | Y )
        marg_S,marg_X,marg_Y,marg_Z = self.marginal_a(self.S, self.X, self.Y, self.Z, which_sources, sol_rpq)
        marg_SX, marg_SY, marg_SZ, marg_XY, marg_XZ, marg_YZ = self.marginal_ab(self.S, self.X, self.Y, self.Z, which_sources, sol_rpq)
        for s in self.S:
            for y in self.Y:
                if (s,y) in self.b_sy.keys():
                    # Subtract q_{s,y}*log( q_{s,y}/ q_{y} )
                    mysum -= marg_SY[(s,y)]*log(marg_SY[(s,y)]/marg_Y[y])
                #^ if sy exists
            #^ for y 
        #^ for s
        return mysum
    #^ if sources
    
    elif which_sources == [2,3]:
        # H ( S | X )        
        marg_S,marg_X,marg_Y,marg_Z = self.marginal_a(self.S, self.X, self.Y, self.Z, which_sources, sol_rpq)
        marg_SX, marg_SY, marg_SZ, marg_XY, marg_XZ, marg_YZ = self.marginal_ab(self.S, self.X, self.Y, self.Z, which_sources, sol_rpq)
        for s in self.S:
            for x in self.X:
                if (s,x) in self.b_sx.keys():
                    # Subtract q_{s,x}*log( q_{s,x}/ q_{x} )
                    mysum -= marg_SX[(s,x)]*log(marg_SX[(s,x)]/marg_X[x])
                #^ if sx exists
            #^ for y 
        #^ for s
        return mysum
    #^ if sources
#^ condentropy_1var()

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

