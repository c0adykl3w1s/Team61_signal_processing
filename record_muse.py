from muselsl import record
import os


def muse_record(d): # Duration in seconds
	try:
		if __name__ == "__main__":
			# Note: stream must be active
			#f_name = os.path.join(os.getcwd(), 'current_rawdata.csv')
			record(duration=d)#,filename='current_rawdata.csv')
			# Note: will not execute until recording is finished
			print('Recording has ended')
	except:
		print('\n\nOof: Recording Failed\n\nCheck current_rawdata.csv to salvage any data\n\nGoodbye\n\n')
		exit()	


muse_record(1800)
