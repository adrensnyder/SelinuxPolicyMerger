###################################################################
# Copyright (c) 2023 AdrenDnyder https://github.com/adrensnyder/SelinuxPolicyMerger
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# DISCLAIMER:
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
###################################################################

import argparse
import re
import os
import sys

def read_file(file_path):
	with open(file_path, 'r') as file:
		return file.readlines()

def extract_section(lines, section):
	section_lines = []
	in_section = False

    #print(section)

	for line in lines:
		in_section = False
		line = line.strip()
		if line.startswith(section):
			in_section = True
		if in_section:
			section_lines.append(line.strip())

	return section_lines

def extract_class(lines):
	classarray = []
	for line in lines:
		parts = line.split('{')
		parts[0] = parts[0].strip().split(' ')
		if len(parts) == 2:
			parts[1] = parts[1].replace('{', '').replace('}', '').replace(';', '').strip()
			classarray.append([parts[0][1],parts[1]])
		else:
			parts[0][2] = parts[0][2].replace(';','')
			classarray.append([parts[0][1],parts[0][2]])

	classarray.sort()
	return classarray

def extract_allow(lines):
	allowarray = []
	for line in lines:
		parts = line.split('{')
		parts[0] = parts[0].strip().split(' ')
		if len(parts) == 2:
			parts[1] = parts[1].replace('{', '').replace('}', '').replace(';', '').strip()
			allowarray.append([parts[0][1] + " " + parts[0][2],parts[1]])
		else:
			parts[0][3] = parts[0][3].replace(';','')
			allowarray.append([parts[0][1] + " " + parts[0][2],parts[0][3]])
		
	allowarray.sort()
	return allowarray

def create_class(classname, perms):
	newclass = "class " + classname + " { " + perms	+ " };"
	newclass = newclass.replace("  "," ")
	return newclass

def create_allow(allowname, perms):
	newallow = "allow " + allowname + " { " + perms	+ " };"
	newallow = newallow.replace("  "," ")
	return newallow

def merge(typesection,set1,set2):
	array1 = []
	array2 = []

	if typesection == "class":
		array1 = extract_class(set1)
		array2 = extract_class(set2)

	if typesection == "allow":
		array1 = extract_allow(set1)
		array2 = extract_allow(set2)

	arraynew = []

	newperms = ""

	for i in range(len(array1)):
		type1 = array1[i][0]
		exist = False
		for j in range(len(array2)):
			type2 = array2[j][0]
			if type1 == type2:
				exist = True
				break
		if exist == False:
			if 	typesection == "class":	
				arraynew.append(create_class(type1,array1[i][1]))
			if 	typesection == "allow":
				arraynew.append(create_allow(type1,array1[i][1]))

	for i in range(len(array2)):
		type2 = array2[i][0]
		typei = -1		

		exist = False
		for j in range(len(array1)):
			type1 = array1[j][0]
			if type1 == type2:
				exist = True
				typei = j
				break
			else:
				newperms = array2[i][1]			

		if exist == True:
			perms1 = array1[typei][1].split(' ')
			perms2 = array2[i][1].split(' ')

			newperms = ""

			for x in range(len(perms1)):
				perm1 = perms1[x]
				newperms += perm1 + " "

			for z in range(len(perms2)):
				permmissing = True
				for x in range(len(perms1)):
					perm1 = perms1[x]
					perm2 = perms2[z]
					if perm1 == perm2:
						permmissing = False
						break

				if permmissing == True:
					newperms += perm2  + " "

		if 	typesection == "class":
			arraynew.append(create_class(type2,newperms))

		if 	typesection == "allow":
			arraynew.append(create_allow(type2,newperms))

	arraynew.sort()
	return arraynew

def compare_sections(file1_lines, file2_lines, file_dest):
	# Check Type
	section1_lines = extract_section(file1_lines, "type")
	section2_lines = extract_section(file2_lines, "type")

	set1 = set(section1_lines)
	set2 = set(section2_lines)

	newtypes = []

	for type1 in set1:
		newtypes.append(type1)

	for type2 in set2:
		typemissing = True
		for type1 in set1:
			if type1 == type2:
				typemissing = False
		if typemissing == True:
			newtypes.append(type2)

	newtypes.sort()

	# Print
	#print("module my-zabbix 1.0;")
	#print("")
	#print("require {")
	writefile(file_dest,"module my-zabbix 1.0;")
	writefile(file_dest,"")
	writefile(file_dest,"require {")

	# Print Type
	for element in newtypes:
		#print("\t" + element)
		writefile(file_dest,"\t" + element)

	# Check Class
	section1_lines = extract_section(file1_lines, "class")
	section2_lines = extract_section(file2_lines, "class")

	set1 = set(section1_lines)
	set2 = set(section2_lines)

	# Print Class

	classarray=merge("class",set1,set2)
	for element in classarray:
		#print("\t" + element)
		writefile(file_dest,"\t" + element)

	# Print
	#print("}")
	#print("")
	writefile(file_dest,"}")
	writefile(file_dest,"")

	# Check Allow
	section1_lines = extract_section(file1_lines, "allow")
	section2_lines = extract_section(file2_lines, "allow")

	set1 = set(section1_lines)
	set2 = set(section2_lines)

	# Print Merge

	allowarray=merge("allow",set1,set2)

	for element in allowarray:
		writefile(file_dest,element)

def writefile(file,line):
	if isinstance(line,str):
		with open(file, 'a') as filewrite:
			filewrite.write(line + "\n")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Compare SELinux policy files.")
	parser.add_argument("--file1", required=True, help="Path to the file 1 to be compared")
	parser.add_argument("--file2", required=True, help="Path to the file 2 to be compared")
	parser.add_argument("--dest", required=True, help="Path to the destination file (Will be overwritten)")

	args = parser.parse_args()

	if not os.path.exists(args.file1) and not os.path.exists(args.file2):
		print("Error: One of the file specified does not exist")
		sys.exit()
	
	file1_lines = read_file(args.file1)
	file2_lines = read_file(args.file2)
	file_dest = args.dest

	if os.path.exists(file_dest):
		os.remove(file_dest)

	compare_sections(file1_lines, file2_lines, file_dest)

