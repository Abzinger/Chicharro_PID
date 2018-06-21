# test_and_gate.py

from sys import path
path.insert(0,"..")

from Chicharro_pid import pid, Chicharro_pid_Exception

# AND gate
xorgate = dict()
xorgate[ (0,0,0,0) ] = .125
xorgate[ (1,0,0,1) ] = .125
xorgate[ (1,0,1,0) ] = .125
xorgate[ (1,1,0,0) ] = .125
xorgate[ (0,0,1,1) ] = .125
xorgate[ (0,1,0,1) ] = .125
xorgate[ (0,1,1,0) ] = .125
xorgate[ (1,1,1,1) ] = .125


# ECOS parameters 
parms = dict()
parms['max_iters'] = 100

print("Starting Chicharro_pid.pid() on AND gate.")
try:
  returndict = pid(xorgate, cone_solver="ECOS", output=2, **parms)
  msg="""Synergistic information: {CI}
  Unique information in X: {UIX}
  Unique information in Y: {UIY}
  Unique information in Z: {UIZ}
  Unique information in X,Y: {UIXY}
  Unique information in X,Z: {UIXZ}
  Unique information in Y,Z: {UIYZ}
  Shared information: {SI}
  Primal feasibility ( min H(S|X,Y,Z) ): {Num_err_I[0]}
  Dual feasibility ( min H(S|X,Y,Z) ): {Num_err_I[1]}
  Duality Gap ( min H(S|X,Y,Z) ): {Num_err_I[2]}
  Primal feasibility ( min H(S|X,Y) ): {Num_err_12[0]}
  Dual feasibility ( min H(S|X,Y) ): {Num_err_12[1]}
  Duality Gap ( min H(S|X,Y) ): {Num_err_12[2]}
  Primal feasibility ( min H(S|X,Z) ): {Num_err_13[0]}
  Dual feasibility ( min H(S|X,Z) ): {Num_err_13[1]}
  Duality Gap ( min H(S|X,Z) ): {Num_err_13[2]}
  Primal feasibility ( min H(S|Y,Z) ): {Num_err_23[0]}
  Dual feasibility ( min H(S|Y,Z) ): {Num_err_23[1]}
  Duality Gap ( min H(S|Y,Z) ): {Num_err_23[2]}"""
  print(msg.format(**returndict))
  
except Chicharro_pid_Exception:
  print("Cone Programming solver failed to find (near) optimal solution. Please report the input probability density function to abdullah.makkeh@gmail.com")

print("The End")