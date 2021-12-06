import matplotlib.pyplot as plt
import numpy as np
from math import sin, cos, sqrt, pi
from muselsl import stream, record, list_muses
from muselsl.muse import Muse
from datetime import datetime
import os
import csv, sys, time, threading


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


def muse_readfile_from_line(filename, start_line = 1): # LINE INDEX STARTS AT ONE
	data = [[],[],[],[],[]]
	current_line = 1
	with open(filename) as csvfile:
		dataset = csv.reader(csvfile)
		header = (start_line == 1)
		while(current_line < start_line): # skip ahead in the file until current_line == start_line
			current_line += 1
			next(csvfile)
		for row in dataset:	
			if(header): # The header will be kept as strings
				for i in range(5):
					try: # if calling row[i] gives an out-of-range exception, file is not muse data
						data[i].append(row[i])
					except:
						print('\n\nData Is Not Formatted Correctly\n\n')
						exit()
			else:
				for i in range(5): # if calling row[i] gives an out-of-range exception, file is not muse data
					try:
						data[i].append(float(row[i]))
					except:
						print('\n\nData Is Not Formatted Correctly\n\n')
						exit()
			header = False # ensures that only the header elements are kept as strings
			current_line += 1
	return [data, current_line]



def muse_stream():
	if __name__ == "__main__":
		try:
			muses = list_muses()

			if not muses:
				print('No Muses found')
			else:
				stream(muses[0]['address'],timeout=14400)
				# Note: Streaming is synchronous, so code here will not execute until the stream has been closed
				print('Stream has ended')
		except:
			print('\n\nOof: Stream Failed\n\nCheck current_rawdata.csv to salvage any data\n\nGoodbye\n\n')
			exit()



def muse_record(d): # Duration in seconds
	try:
		if __name__ == "__main__":
			# Note: stream must be active
			f_name = os.path.join(os.getcwd(), 'current_rawdata.csv')
			record(duration=d,filename = f_name)#,filename='current_rawdata.csv')
			# Note: will not execute until recording is finished
			print('Recording has ended')
	except:
		print('\n\nOof: Recording Failed\n\nCheck current_rawdata.csv to salvage any data\n\nGoodbye\n\n')
		exit()		


def ft_mag(signal, electrode, N_initial, N_final):
	# FOURIER TRANSFORM MAGNITUDE
	#
	E = electrode # electrode to use
	N_i = N_initial # index of initial signal point (skip header at N_i=0)
	N_f = N_final # index of final signal point
	#freq = frequencies # frequencies to plot
	#plot_vals = [] # will store |F{x(t)}|(w) here
	sg = np.fft.rfft(signal[E+1][int(N_i):int(N_f+1)])
	freq = np.fft.rfftfreq(2*len(sg)-1,d=(1/256))	
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
	if(num!=0):
		ap /= num
		return ap
	return -0.0000001


def relative_band_avg_power(signal, electrode, N_initial, N_final, FI_lower, FI_upper,FO_lower, FO_upper):
	apI = bandlimited_avg_power(signal, electrode, N_initial, N_final, FI_lower, FI_upper)
	apO = bandlimited_avg_power(signal, electrode, N_initial, N_final, FO_lower, FO_upper)
	return apI/apO


def eeg_live_analysis_from_updating_file(filename="current_stream_data.csv", mode = 1, duration=1800, mean_time_interval=5, print_power=True):
	# run for duration (seconds)
	# checks for updated data file every check_for_update_interval (seconds)
	# if data file has no update, check again after check_for_update_interval (seconds)
	# if data file has an update, add it to the data array
	# 
	start_time = time.time()
	mean_window_frames = int(mean_time_interval * 256)
	print('\n')
	#last_line = 1
	first = True
	delay = []
	num_electrodes = 4
	freq_ranges = [[4,8],[8,12],[12,30]]
	data = []
	power_data = []
	tag = ''
	computation_times = []
	for i in range(num_electrodes+1):
		data.append([])
	if(mode==1):
		for i in range(num_electrodes+1):
			power_data.append([])
	elif(mode==2 or mode==3):
		for i in range(3*num_electrodes+1):
			power_data.append([])
	try:
		timestamp_start = 0
		N_i = 1
		N_f = 1
		line = 1
		startline = 0
		last_update_time = os.path.getmtime(filename) # gives the last time the file was modified
		while ((time.time()-start_time) < duration): # main body of function runs in this loop
			check_update_time = os.path.getmtime(filename) # keeps checking the 'modified' time
			if(abs(last_update_time - check_update_time) >= 0.1): # if True, an update to the file occured
				time.sleep(0.1) # must be sure file is closed after update before accessing again
				temp = muse_readfile_from_line(filename,line)
				#print(check_update_time)
				hold = len(data[0])
				if(hold != 0):
					N_i = hold # get start of interval for power calculation
				for i in range(len(data)): # updates all 5 columns of the data array
					data[i].extend(temp[0][i])
				#print(temp[0])
				N_f = len(data[0])-1 # get end of interval for power calculation
				line = temp[1] # get next line to start from in the csv file
				delay.append(time.time()-check_update_time)
				if(first): #ignore first sample and all negative timestamps
					first = False
					timestamp_start = check_update_time
					# add headers
					power_data[0].append(data[0][0])
					for i in range(1,len(data)):
						if(mode==1):
							power_data[i].append(data[i][0])
							tag = '_power_a2b_live.csv'
						if(mode==2):
							power_data[3*i-2].append(data[i][0]+'_theta')
							power_data[3*i-1].append(data[i][0]+'_alpha')
							power_data[3*i].append(data[i][0]+'_beta')
							tag = '_power_tab_live.csv'
						if(mode==3):
							power_data[3*i-2].append(data[i][0]+'_alpha_to_theta')
							power_data[3*i-1].append(data[i][0]+'_alpha_to_beta')
							power_data[3*i].append(data[i][0]+'_theta_to_beta')
							tag = '_power_3ratios_live.csv'
				else:
					if(startline==0):
						startline = N_i
					# # SYNC CHECKING
					# if(abs((N_f-N_i+1)-mean_window_frames)>10 or abs((check_update_time-last_update_time)-mean_time_interval) > (0.02*mean_time_interval)):
					# 	print('\n\n\nERROR: SYNC LOST\n\nCHECK INPUT STREAM\n\n\nEXITING...\n\n\n')
					# 	exit()
					print('Samples in Interval = '+str(N_f-N_i+1))
					power_data[0].append(check_update_time-timestamp_start)
					# add value for all 4 electrodes
					comp1 = time.time()
					if(mode==1):
						for i in range(1,len(power_data)):
							power_data[i].append(relative_band_avg_power(data, i-1, N_i, N_f, 8, 12, 12, 30))
						# print('\n\n\n')
						print('timestamp = '+str(power_data[0][len(power_data[0])-1])+' s\n', end='')
						for i in range(1,len(data)):
							print('\n'+data[i][0]+' (alpha/beta)')
							print(str(power_data[i][len(power_data[i])-1]))
						print('\n\n\n')
					else:
						for i in range(1,len(data)):
							theta = bandlimited_avg_power(data, i-1, N_i, N_f, freq_ranges[0][0], freq_ranges[0][1])
							alpha = bandlimited_avg_power(data, i-1, N_i, N_f, freq_ranges[1][0], freq_ranges[1][1])
							beta = bandlimited_avg_power(data, i-1, N_i, N_f, freq_ranges[2][0], freq_ranges[2][1])
							if(mode==2):
								power_data[3*i-2].append(theta)
								power_data[3*i-1].append(alpha)
								power_data[3*i].append(beta)
							if(mode==3):
								power_data[3*i-2].append(alpha/theta)
								power_data[3*i-1].append(alpha/beta)
								power_data[3*i].append(theta/beta)
						# print('\n\n\n')
						print('timestamp = '+str(power_data[0][len(power_data[0])-1])+' s\n', end='')
						for i in range(1,len(data)):
							if(mode==2):
								print('\n'+data[i][0]+' (theta, alpha, beta)')
							if(mode==3):
								print('\n'+data[i][0]+' (alpha/theta, alpha/beta, theta/beta)')
							print(str(power_data[3*i-2][len(power_data[3*i-2])-1])+','+str(power_data[3*i-1][len(power_data[3*i-1])-1])+','+str(power_data[3*i][len(power_data[3*i])-1]))
						print('\n\n\n')
					comp2 = time.time()
					computation_times.append(comp2-comp1)
					print('Computation Time = '+str(comp2-comp1)+' s\n\n\n')
				last_update_time = check_update_time # update this
			# save power data when done
		muse_writefile((filename[:len(filename)-4]+tag),power_data)
		return [data, power_data, startline]
	except KeyboardInterrupt:
		muse_writefile((filename[:len(filename)-4]+tag),power_data)		
		return [data, power_data, startline, computation_times]


m = 3
mean_window_duration = 5
demo_plot = True
dataset = eeg_live_analysis_from_updating_file(read_arg(),m)
# plot if in mode 1
if(demo_plot and m==1):
	plt.figure(1)
	t = []
	for i in range(len(dataset[0][0])-1):
		t.append(dataset[0][0][i+1]-dataset[0][0][dataset[2]])
	plt.plot(t[dataset[2]-1:],dataset[0][1][dataset[2]:], 'b',label='TP9')
	plt.plot(t[dataset[2]-1:],dataset[0][2][dataset[2]:], 'tab:green',label='AF7')
	plt.plot(t[dataset[2]-1:],dataset[0][3][dataset[2]:], 'tab:red',label='AF8')
	plt.plot(t[dataset[2]-1:],dataset[0][4][dataset[2]:], 'tab:orange',label='TP10')
	plt.xlabel('Time (s)')
	plt.ylabel('Voltage (mV)')
	plt.legend()
	plt.figure(2)
	t2 = []
	for i in range(len(dataset[1][0])-1):
		t2.append(dataset[1][0][i+1])
	plt.plot(t2,dataset[1][1][1:], 'b',label='TP9')
	plt.plot(t2,dataset[1][2][1:], 'tab:green',label='AF7')
	plt.plot(t2,dataset[1][3][1:], 'tab:red',label='AF8')
	plt.plot(t2,dataset[1][4][1:], 'tab:orange',label='TP10')
	plt.xlabel('Time (s)')
	plt.ylabel('Alpha/Beta Power in Window (t, t+'+str(mean_window_duration)+')')
	plt.legend()
	plt.show()

# computation times
plt.figure(1)
t = []
for i in range(len(dataset[3])):
	t.append(i+1)
plt.plot(t,dataset[3], 'b')
plt.xlabel('Sample Index')
plt.ylabel('Time (s)')
plt.show()
print(max(dataset[3]))
# 
# t1i=time.time()
# test_data = muse_readfile_from_line('live_analysis_testcase_0.csv', start_line = 1)
# t1f=time.time()
# muse_writefile('test2_from60000.csv',test_data[0])
# print(test_data[1])
# print(t1f-t1i)
# t2i=time.time()
# test_data = muse_readfile_from_line('test2.csv', start_line = 861095)
# t2f=time.time()
# muse_writefile('test2_from60000.csv',test_data[0])
# print(test_data[1])
# print(t2f-t2i)


# t1i=time.time()
# test_data = muse_readfile_from_line('test1.csv', start_line = 1)
# t1f=time.time()
# muse_writefile('test1_from60000.csv',test_data[0])
# print(test_data[1])
# print(t1f-t1i)
# t2i=time.time()
# test_data = muse_readfile_from_line('test1.csv', start_line = 109244)
# t2f=time.time()
# muse_writefile('test1_from60000.csv',test_data[0])
# print(test_data[1])
# print(t2f-t2i)


# test_data = muse_readfile_from_line('test1.csv', start_line = 1)
# muse_writefile('test1.csv',test_data[0])
# print(os.path.getmtime('test1.csv'))
# time.sleep(5)
# test_data = muse_readfile_from_line('test1.csv', start_line = 1)
# muse_writefile('test1.csv',test_data[0])
# print(os.path.getmtime('test1.csv'))


# t1i=time.time()
# test_data = muse_readfile_from_line('test3.csv', start_line = 1)
# t1f=time.time()
# muse_writefile('test3_from60000.csv',test_data[0])
# print(test_data[1])
# print(t1f-t1i)
# t2i=time.time()
# test_data = muse_readfile_from_line('test3.csv', start_line = 9940000)
# t2f=time.time()
# muse_writefile('test3_from60000.csv',test_data[0])
# print(test_data[1])
# print(t2f-t2i)

