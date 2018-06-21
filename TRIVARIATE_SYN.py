# TRIVARIATE_SYN.py
import ecos
from scipy import sparse
import numpy as np
from numpy import linalg as LA
import math
# from collections import defaultdict

# ECOS's exp cone: (r,p,q)   w/   q>0  &  exp(r/q) ≤ p/q
# Translation:     (0,1,2)   w/   2>0  &  0/2      ≤ ln(1/2)
def r_vidx(i):
    return 3*i
def p_vidx(i):
    return 3*i+1
def q_vidx(i):
    return 3*i+2
ln  = math.log
log = math.log2
# Creates the optimization problem needed to compute both synergy (also needed for uniqueness)
# def init(self):
#     # (c) Abdullah Makkeh, Dirk Oliver Theis
#     # Permission to use and modify under Apache License version 2.0
#     # Data for ECOS
#     self.c            = None
#     self.G            = None
#     self.h            = None
#     self.dims         = dict()
#     self.A            = None
#     self.b            = None
    
#     # ECOS result
#     self.sol_rpq    = None
#     self.sol_slack  = None #
#     self.sol_lambda = None # dual variables for equality constraints
#     self.sol_mu     = None # dual variables for generalized ieqs
#     self.sol_info   = None
    
# #^ init

def create_model(self):
    # (c) Abdullah Makkeh, Dirk Oliver Theis
    # Permission to use and modify under Apache License version 2.0
    n = len(self.quad_of_idx)
    m = len(self.b_sx) + len(self.b_sy) + len(self.b_sz)
    n_vars = 3*n
    n_cons = n+m
    
    # Create the equations: Ax = b
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
    self.dims = dict()
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
    #^ if    
    solution = ecos.solve(self.c, self.G,self.h, self.dims,  self.A,self.b, **self.ecos_kwargs)

    if 'x' in solution.keys():
        self.sol_rpq    = solution['x']
        self.sol_slack  = solution['s']
        self.sol_lambda = solution['y']
        self.sol_mu     = solution['z']
        self.sol_info   = solution['info']
        return "success", self.sol_info
    else: # "x" not in dict solution
        return "x not in dict solution -- No Solution Found!!!"
    #^ if/esle
#^ solve()

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

def check_feasibility(self): # returns pair (p,d) of primal/dual infeasibility (maxima)
    # Primal infeasiblility
    
    # non-negative ineqaulity 
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
            #^ if
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

def dual_value(self):
    return -np.dot(self.sol_lambda, self.b)