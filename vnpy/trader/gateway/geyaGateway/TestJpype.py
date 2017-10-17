import os
import jpype
from jpype import *

jarpath = os.path.join(os.path.abspath('.'), 'test.jar')
print jarpath
startJVM(getDefaultJVMPath(), "-ea", "-Djava.class.path=%s" % jarpath)
print getDefaultJVMPath()

TestJpype = jpype.JClass('TestJpype.TestJpype')
test = TestJpype()
res = test.run("a")
print res

shutdownJVM()