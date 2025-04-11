#!/usr/bin/python3
import sys, subprocess

svg = 'pieces.svg'

pw = subprocess.Popen(['inkscape', '-W', svg], stderr=subprocess.DEVNULL, stdout=subprocess.PIPE)
ph = subprocess.Popen(['inkscape', '-H', svg], stderr=subprocess.DEVNULL, stdout=subprocess.PIPE)

pw.wait()
ph.wait()

w = float(pw.stdout.read()) / 6 + 2.5
h = float(ph.stdout.read()) / 2 + 3

rows = [ 'black', 'white' ]
cols = [ 'king', 'queen', 'bishop', 'knight', 'rook', 'pawn' ]

names = []
jobs = []		

def extract(x, y, name):
	global names, jobs
	names.append(name)
	command = [
		'inkscape',
		'--export-dpi=300',
		'--export-png=' + name + '.png',
		'--export-area=' + str(x*w) + ':' + str(y*h) + ':' + str((x+1)*w) + ':' + str((y+1)*h),
		svg]
	jobs.append(subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))

for y in range(len(rows)):
	for x in range(len(cols)):
		extract(x, y, rows[y] + '_' + cols[x])

print('Creating ', len(jobs), 'files ...')

for name, job in zip(names, jobs):
	job.wait()
	print(name + '.png created')
		
importcode = open('importcode.py', 'w')
mlen = max([ len(name) for name in names ])
importcode.write('fileDict = {\n')
for name in names:
	importcode.write("    '" + name + "'" + ' ' * (mlen-len(name)) + " : 'chessPieces/" + name + ".png',\n")
importcode.write('}\n')	

sys.exit(0)
