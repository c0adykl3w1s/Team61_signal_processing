from muselsl import stream,list_muses

# def muse_stream():
# 	if __name__ == "__main__":
# 		try:
# 			muses = list_muses()

# 			if not muses:
# 				print('No Muses found')
# 			else:
# 				stream(muses[0]['address'],timeout=14400)
# 				# Note: Streaming is synchronous, so code here will not execute until the stream has been closed
# 				print('Stream has ended')
# 		except:
# 			print('\n\nOof: Stream Failed\n\nCheck current_rawdata.csv to salvage any data\n\nGoodbye\n\n')
# 			exit()


def muse_stream():
	if __name__ == "__main__":
		try:
			stream('00:55:DA:B5:B1:70',timeout=14400)
			# Note: Streaming is synchronous, so code here will not execute until the stream has been closed
			print('Stream has ended')
		except:
			print('\n\nOof: Stream Failed\n\n\nGoodbye\n\n')
			exit()


muse_stream()