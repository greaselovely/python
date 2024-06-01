
#from matplotlib import pyplot as plt

"""
So I bought my truck used a few years ago
and the previous owner put a bunch of third
party parts on it including replacing the wheels
with 24" wheels and clearly someone had adjusted
the speedometer to account for the change in wheel
size.  The truck comes with 20" wheels from the factory

I replaced the wheels with 22" because the 24" were the 
short walled tires that would easily damage the wheels
when running over the slightest bump.  I haven't been
able to find anyone to change the speedo so for years
I've been mentally accounting for the actual speed vs
what the speedo displays.  I decided I needed / wanted to 
understand the math and thus wanted to create a table
that would show a predictable (close enough) list to go open

My lady helped with the math and we pooped this out.  Works well.

"""

### known points ###
# x and y below refer to a graph axis
# not used in the lambda functions per se
# x = speedo
x_lst = [15,20,27,45,50,60]
# y = actual
y_lst = [20,25,35,55,65,75]
### known points ###

spd_str="Speedo"
act_str="Actual"
actual=[]
a=[] # y_lst
b=[] # x_lst

# list from 0 MPH to 80 MPH incremented by 5
speedo=list(range(0, 80, 5))

# convert to floats because s & z below are floats 
# and we need to do some math with the floats
for i in y_lst:
    a.append(float(y_lst[-1] - i))

for i in x_lst:
    b.append(float(x_lst[-1] - i))

# remove zeroes from list to avoid divide by zero problem
a = a[:-1]
b = b[:-1]

# divide a by b:
ess=list(map(lambda x,y: x/y, a, b))
s = (sum(ess)/len(ess))

# get z by subtracting actual from s (above) multiplied by speedo
zee=list(map(lambda x,y: y - s * x, x_lst, y_lst))
z = (sum(zee)/len(zee))

# create a predicted list of speeds based on known points
for i in speedo:
    actual.append(int(s * i + z))

final_lst=list(zip(speedo, actual))

print("{}   {}".format(spd_str, act_str))
for i in final_lst:
    if len(str(i[1])) == 1:
        print(str(i[0])+ " " * len(spd_str) + "  " + str(i[1]))
    else:
        print(str(i[0])+ " " * len(spd_str) + " " + str(i[1]))

#fig = plt.gcf()
#fig.set_size_inches(8,8)
#plt.scatter(speedo, actual)
#plt.show()