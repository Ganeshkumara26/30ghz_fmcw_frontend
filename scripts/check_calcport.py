import CSXCAD
from openEMS.ports import LumpedPort
import inspect

CSX = CSXCAD.ContinuousStructure()
port1 = LumpedPort(CSX, 1, 50, [0,0,0], [0,0,1], 'z', excite=True)
print("CalcPort signature:")
print(inspect.signature(port1.CalcPort))
