import matplotlib.pyplot as plt
import numpy as np
import csv, sys

def read_arg():
	try:
		filename = sys.argv[1]
	except:
		print('\n\nEnter a muse csv file name as an argument\n\n')
		exit()


	# check file extension
	if(filename[len(filename)-4:] != '.csv'):
		print('\n\nEnter a muse csv file name as an argument\n\n')
		exit()
	return filename


#outputs a 2d list from a muse format csv input
#file = [['timestamp',x1,x2,...,xn],['tp9',x1,x2,...,xn],['af7',x1,x2,...,xn],['af8',x1,x2,...,xn],['tp10',x1,x2,...,xn]]
# where x1-xn are the float data vals under the given header
def muse_readfile(fn):
	# file vars
	file = [[],[],[],[],[],[],[],[],[],[],[],[],[]] # no shorthand, memory assignment issue
	filename = fn


	# store file data in 2d list file[tag_index][n] where n is the data point
	with open(filename) as csvfile:
		dataset = csv.reader(csvfile)
		hold = True
		for row in dataset:	
			if(hold):		
				for i in range(13):
					# if calling row[i] gives an out-of-range exception, file is not muse data
					try:
						file[i].append(row[i])
					except:
						print('\n\nEnter a muse csv file name as an argument\n\n')
						exit()
			else:
				for i in range(13):
					# if calling row[i] gives an out-of-range exception, file is not muse data
					try:
						file[i].append(float(row[i]))
					except:
						print('\n\nEnter a muse csv file name as an argument\n\n')
						exit()
			hold = False
	return file


file = muse_readfile(read_arg())


t = []
for i in range(len(file[0])-1):
	t.append(5*i)
print(t)
print(file[1][1:])
plt.plot(t[399:],file[10][400:], 'b',label='TP10_alpha/theta')
plt.plot(t[399:],file[11][400:], 'tab:green',label='TP10_alpha/beta')
plt.plot(t[399:],file[12][400:], 'tab:red',label='TP10_theta/beta')
#plt.plot(t,file[4][1:], 'tab:orange',label='TP10')
plt.xlabel('Time (s)')
plt.ylabel('Relative Power in Window (t, t+'+str(5)+')')
# plt.ylabel('Voltage(mV)')
plt.legend()
plt.show()
# plt.plot(t,file[1][1:], 'b',label='TP9')
# plt.plot(t,file[2][1:], 'tab:green',label='AF7')
# plt.plot(t,file[3][1:], 'tab:red',label='AF8')
# plt.plot(t,file[4][1:], 'tab:orange',label='TP10')