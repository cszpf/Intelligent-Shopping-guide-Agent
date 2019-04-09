import os
import re
import pdb
import pandas as pd
import re


path = 'wps_line_one_data_sample_eval'
txt_list = os.listdir(path)
words = ''
for txt in txt_list:
	texts = ''
	
	print(txt)
	with open(os.path.join(path, txt), 'r') as f:
		lines = f.readlines()
		for line in lines:
			ifMatch = re.search('O\\n\Z', line)
			if not ifMatch:
				if re.search('\A\n\Z', line):
					texts += '\n'
				else:
					words += line[0]
					if re.search(' E-', line) or re.search(' S-', line):
						texts += "[$"+words+'#'+line.split('-')[-1].strip()+"*]"
						words = ''
			else:
				if line[0].split(" O")[0] != "":
					texts += line[0]
	with open(os.path.join(path, txt[:-4]+'.ann'), 'w') as f_t:
		f_t.write(texts)	

