# test_and_gate.py

from sys import path
path.insert(0,"..")

from Chicharro_pid_control import pid, Chicharro_pid_Exception

# AND gate
andgate = dict()
andgate[ (0,0,0,0) ] = .125
andgate[ (0,0,0,1) ] = .125
andgate[ (0,0,1,0) ] = .125
andgate[ (0,1,0,0) ] = .125
andgate[ (0,0,1,1) ] = .125
andgate[ (0,1,0,1) ] = .125
andgate[ (0,1,1,0) ] = .125
andgate[ (1,1,1,1) ] = .125


# ECOS parameters 
parms = dict()
parms['max_iters'] = 100

print("Starting Chicharro_pid.pid() on AND gate.")
try:
  returndict = pid(andgate, cone_solver="ECOS", output=2, **parms)

  # msg="""Shared information: {SI}
  # Unique information in Y: {UIY}
  # Unique information in Z: {UIZ}
  # Synergistic information: {CI}
  # Primal feasibility: {Num_err[0]}
  # Dual feasibility: {Num_err[1]}
  # Duality Gap: {Num_err[2]}"""
  msg="""Synergistic information: {CI}
  Primal feasibility: {Num_err[0]}
  Dual feasibility: {Num_err[1]}
  Duality Gap: {Num_err[2]}"""
  print(msg.format(**returndict))
  
except Chicharro_pid_Exception:
  print("Cone Programming solver failed to find (near) optimal solution. Please report the input probability density function to abdullah.makkeh@gmail.com")

print("The End")