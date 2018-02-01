simport simple_ast
reload = simple_ast.reload_module

import objects

assert(True)
# assert(False)
print 1
print True and False
print True or erp
print False and erp

l = objects.List()
l.append(3)
print l
l[0] += 2
l._content[0] += 4
print l

print 3, 4
x = 4
y = 1 + 1 + x
print y

def foo(a):
    return a + 1

z = foo(10) + foo(10)
while_true:
    print z
    break

testl = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
w = testl[9]

while_true:
    w = w + 1
    print w
    if w > 11:
        break

simple_for elem in testl:
    print elem

class Test:
    cd = 3

print Test.cd
# reload(simple_ast)

def foobar(*args):
    print args

foobar(1)
foobar(1, x, w)

#simple_ast.regular_assign = regular_assign
x, y = [3, 4]

if False:
    print "false"
elif False:
    print "still false"
elif True:
    print "now true"
else:
    print "shouldn't get here"
    print 30

try:
    try:
        print "testing"
        raise Exception()
    except IndexError:
        print "error!"
except Exception:
    print "error 2!"

for elem in testl:
    if elem == 5:
        continue
    if elem == 8:
        break
    print elem
comp = [x for x in [2, 3, 4, 5, 6] if x%2 == 0]

import objects
print objects.sum(comp)

def opt(a, b=5):
    print a, b

opt(3)
opt(1, 2)

obj = objects.object()
print repr(objects.True)
print repr(objects.False)
print objects.Int(3).__padd__(objects.Int(4)).value

l = objects.List()
l.append(3)
l[0] = 4
l.append(4)
l.append(5)
l.append(3)
print str(l)
print l.count(3)
print l.pop(1)
print str(l)
print l.__lt__(l)

l2 = objects.List()
l2.append(3)
l2.append(5)
l2.append(4)
print str(l2)
print l.__lt__(l2)
l.__setslice__(2, 5, l2)
print str(l)
l3 = l.__add__(l2)
print str(l3)
l3.append(10)
print str(l3)
print str(l2)
print str(l)

d = objects.Dict()
print str(d)
#print d.getindex(3)
d[3] = 4
print d
print d[3]
d[4] = 5
d[5] = 6
print d
d[3] = 10
print d
print d[3]
print d.__path__
print d.items()
print d.keys()
print d.values()
print d.__contains__(3)
print d.__contains__(20)
print d.get(3)
print d.get(20, 20)
for k in d:
    print k

d2 = objects.Dict()
d2[3] = 3
d.update(d2)
print d
d3 = objects.Dict(d)
print d3
#d4 = objects.Dict(a=3, b=5)
d4 = objects.Dict()
d4['a'] = 3
d4['b'] = 5
print d4
print d4['b']
print d4.pop('a')
print d4
print d4.setdefault('c', 10)
print d4
del d4['c']
print d4

import util
output = util.MatchError("foo")
print output.__type__ == "MatchError"

n = util.Node("foo", [])
wrapped = util.simple_wrap_tree(["foo", ["bar", "baz"]])
print repr(wrapped)
def getattr(instance, key, default=None):
    return instance.getattr(key, default)

print getattr(n, "name")
#print repr(wrapped)
#wrapped.pprint()
