import numpy as np
import csv, sys, time

#ASSUMES MUSE FILES AND 256 HZ
#Reads raw data from argument and outputs the alpha/beta relative power
#as a csv in the same format with name = input_filename + "_power"
sampling = 1000

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
	file = []  # no shorthand, memory assignment issue
	filename = fn


	# store file data in 2d list file[tag_index][n] where n is the data point
	with open(filename) as csvfile:
		dataset = csv.reader(csvfile)
		hold = True

		for row in dataset:	
			if(hold):
				elements = len(row)
				if(elements==6):
					elements-=1 # quirk with muse data
				for i in range(elements):
					file.append([])
				for i in range(elements):
					# if calling row[i] gives an out-of-range exception, file is not muse data
					try:
						file[i].append(row[i])
					except:
						print('\n\nEnter a muse csv file name as an argument\n\n')
						exit()
			else:
				for i in range(elements):
					# if calling row[i] gives an out-of-range exception, file is not muse data
					try:
						file[i].append(float(row[i]))
					except:
						print('\n\nEnter a muse csv file name as an argument\n\n')
						exit()
			hold = False
	return file


# Writes Data from list in the format above, 
# i.e. data must be [[header,x1,x2,...,xn],[header,x1,x2,...,xn],[header,x1,x2,...,xn],[header,x1,x2,...,xn],[header,x1,x2,...,xn]]
def muse_writefile(fn, data):
	with open(fn, 'w',newline='') as csvfile:
		w = csv.writer(csvfile)
		check_min=[]
		for k in range(len(data)):
			check_min.append(len(data[k]))
		for i in range(min(check_min)):
			row = []
			for j in range(len(data)):
				row.append(data[j][i])
			w.writerow(row)


def ft_mag(signal, electrode, N_initial, N_final):
	# FOURIER TRANSFORM MAGNITUDE
	#
	E = electrode # electrode to use
	N_i = N_initial # index of initial signal point (skip header at N_i=0)
	N_f = N_final # index of final signal point
	#freq = frequencies # frequencies to plot
	#plot_vals = [] # will store |F{x(t)}|(w) here
	sg = np.fft.rfft(signal[E+1][int(N_i):int(N_f+1)])
	freq = np.fft.rfftfreq(2*len(sg)-1,d=(1/sampling))	
	# return 2d array of freq and |F{x(t)}|(2*pi*freq)
	return [freq, np.abs(sg)]


def bandlimited_avg_power(signal, electrode, N_initial, N_final, F_lower, F_upper):
	mag = ft_mag(signal,electrode,N_initial,N_final)
	ap = 0
	num = 0
	for i in range(len(mag[0])):
		# # ASSUMES THE FREQUENCY ARRAY IS SORTED; can work faster with large number of points
		# if(F_lower>=mag[0][i]):
		# 	continue
		# if(F_upper<mag[0][i]):
		# 	break
		# ap += mag[1][i]**2
		# num += 1
		if(F_lower<mag[0][i] and mag[0][i]<=F_upper):
			ap += mag[1][i]**2
			num += 1		
	try:
		ap /= num
		return ap
	except:
		return float("NaN")


def relative_band_avg_power(signal, electrode, N_initial, N_final, FI_lower, FI_upper,FO_lower, FO_upper):
	apI = bandlimited_avg_power(signal, electrode, N_initial, N_final, FI_lower, FI_upper)
	apO = bandlimited_avg_power(signal, electrode, N_initial, N_final, FO_lower, FO_upper)
	try:
		return apI/apO
	except:
		return float("NaN")


def convert_raw_to_rel_bandpower(filename, FN_lower, FN_upper,FD_lower, FD_upper,frames_per_seg=2560,advancement=2560,write=True): #default 10s with 256 hz
	dataset = muse_readfile(filename)
	output = []
	for i in range(len(dataset)):
		output.append([])
	# add headers
	for i in range(len(dataset)):
		output[i].append(dataset[i][0])
	current_win_end = frames_per_seg
	current_win_start = 1
	while(current_win_end < len(dataset[0])):
		# timestamp will mark the beginning of interval
		output[0].append((current_win_start-1)/sampling)
		# add value for all 4 electrodes
		for i in range(1,len(dataset)):
			output[i].append(relative_band_avg_power(dataset, i-1, current_win_start, current_win_end, FN_lower, FN_upper,FD_lower, FD_upper))
		current_win_start += advancement
		current_win_end += advancement
	if write:
		muse_writefile((filename[:len(filename)-4]+'_power.csv'),output)
	return output



def convert_raw_to_tab_bandpower(filename, frames_per_seg=2560, advancement = 2560, write=True): #default 10s with 256 hz
	dataset = muse_readfile(filename)
	freq_ranges = [[4,8],[8,12],[12,30]]
	output = []
	for i in range(3*(len(dataset)-1)+1):
		output.append([])
	# add headers
	output[0].append(dataset[0][0])
	for i in range(1,len(dataset)):
		output[3*i-2].append(dataset[i][0]+'_theta')
		output[3*i-1].append(dataset[i][0]+'_alpha')
		output[3*i].append(dataset[i][0]+'_beta')
	current_win_end = frames_per_seg
	current_win_start = 1
	while(current_win_end < len(dataset[0])):
		# timestamp will mark the beginning of interval
		output[0].append((current_win_start-1)/256)
		# add 3 values for all 4 electrodes
		for i in range(1,len(dataset)):
			output[3*i-2].append(bandlimited_avg_power(dataset, i-1, current_win_start, current_win_end, freq_ranges[0][0], freq_ranges[0][1]))
			output[3*i-1].append(bandlimited_avg_power(dataset, i-1, current_win_start, current_win_end, freq_ranges[1][0], freq_ranges[1][1]))
			output[3*i].append(bandlimited_avg_power(dataset, i-1, current_win_start, current_win_end, freq_ranges[2][0], freq_ranges[2][1]))
		current_win_start += advancement
		current_win_end += advancement
	if write:
		muse_writefile((filename[:len(filename)-4]+'_power_tab.csv'),output)
	return output



def convert_raw_to_3ratio_bandpower(filename,frames_per_seg=2560, advancement = 2560, write=True): #default 10s with 256 hz
	dataset = muse_readfile(filename)
	freq_ranges = [[4,8],[8,12],[12,30]]
	output = []
	for i in range(3*(len(dataset)-1)+1):
		output.append([])
	# add headers
	output[0].append(dataset[0][0])
	for i in range(1,len(dataset)):
		output[3*i-2].append(dataset[i][0]+'_alpha_to_theta')
		output[3*i-1].append(dataset[i][0]+'_alpha_to_beta')
		output[3*i].append(dataset[i][0]+'_theta_to_beta')
	current_win_end = frames_per_seg
	current_win_start = 1
	while(current_win_end < len(dataset[0])):
		# timestamp will mark the beginning of interval
		output[0].append((current_win_start-1)/256)
		# add 3 values for all 4 electrodes
		for i in range(1,len(dataset)):
			theta = bandlimited_avg_power(dataset, i-1, current_win_start, current_win_end, freq_ranges[0][0], freq_ranges[0][1])
			alpha = bandlimited_avg_power(dataset, i-1, current_win_start, current_win_end, freq_ranges[1][0], freq_ranges[1][1])
			beta = bandlimited_avg_power(dataset, i-1, current_win_start, current_win_end, freq_ranges[2][0], freq_ranges[2][1])
			output[3*i-2].append(alpha/theta)
			output[3*i-1].append(alpha/beta)
			output[3*i].append(theta/beta)
		current_win_start += advancement
		current_win_end += advancement
	if write:
		muse_writefile((filename[:len(filename)-4]+'_power_3ratios.csv'),output)
	return output



#saves as a new csv
#
start = time.time()
mode = 3
window = 4000
adv = 4000
write = True
if(mode==1):
	alpha_to_beta = convert_raw_to_rel_bandpower(read_arg(),8,12,12,30,window,adv,write)
if(mode==2):
	theta_alpha_beta = convert_raw_to_tab_bandpower(read_arg(),window,adv,write)
if(mode==3):
	all3 = convert_raw_to_3ratio_bandpower(read_arg(),window,adv,write)
print('Done: Delay = '+str(time.time()-start))
	
