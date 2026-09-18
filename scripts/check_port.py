import CSXCAD
from openEMS.ports import LumpedPort
CSX = CSXCAD.ContinuousStructure()
port1 = LumpedPort(CSX, 1, 50, [0,0,0], [0,0,1], 'z', excite=True)
print("LumpedPort methods:")
print([m for m in dir(port1) if not m.startswith('_')])
