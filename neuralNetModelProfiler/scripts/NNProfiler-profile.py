__author__      = "Kiriti Nagesh Gowda"
__copyright__   = "Copyright 2018, AMD NeuralNet Model Profiler"
__license__     = "MIT"
__version__     = "0.9.0"
__maintainer__  = "Kiriti Nagesh Gowda"
__email__       = "Kiriti.NageshGowda@amd.com"
__status__      = "Alpha"

import os
import getopt
import sys
import subprocess
from subprocess import call

# caffe models to benchmark
caffeModelConfig =	[ 
			('xyznet',3,1024,2048),
			('xyznet_18-04',3,1024,2048),
			('googlenet',3,224,224),
			('inceptionv4',3,299,299),
			('resnet50',3,224,224),
			('resnet101',3,224,224),
			('resnet152',3,224,224),
			('vgg16',3,224,224),
			('vgg19',3,224,224)
			]

opts, args = getopt.getopt(sys.argv[1:], 'd:l:m:f:')

buildDir = ''
profileLevel = 0
profileMode = 0
miopenFind = 1

for opt, arg in opts:
    if opt == '-d':
    	buildDir = arg
    elif opt =='-l':
    	profileLevel = int(arg)
    elif opt =='-m':
    	profileMode = int(arg)
    elif opt =='-f':
    	miopenFind = int(arg)

if buildDir == '':
    print('Invalid command line arguments.\n \t\t\t\t-d [build directory - required]\n  '\
    										'\t\t\t\t-l [profile level - optional (level 1-8, default:7)]\n'\
    										'\t\t\t\t-m [profile mode - optional (level 1-6, default:6)]\n'\
    										'\t\t\t\t-f [MIOPEN_FIND_ENFORCE mode - optional (level 1-5, default:1)]\n')
    exit()

if buildDir == '':
	buildDir_AMDOVX = '~/AMDOVX'
else:
	buildDir_AMDOVX = buildDir+'AMDOVX'

if profileLevel == 0:
	profileLevel = 7

if profileMode == 0:
	profileMode = 6

# Bring CaffeModels
caffeModels_dir = os.path.expanduser(buildDir_AMDOVX+'/caffeModels')
if(os.path.exists(caffeModels_dir)):
	print("\nCaffeModel Folder Exist\n")
else:
	os.system('(cd '+buildDir_AMDOVX+'; scp -r client@amdovx-file-server:~/caffeModels . )');
	if(os.path.exists(caffeModels_dir)):
		print("\nCaffeModel Retrived from the amdovx-file-server\n")
	else:
		print("\nERROR -- FILE SERVER CONNECTION FAILED, CHECK CONNECTION\n")
		exit()


# run caffe models
develop_dir = os.path.expanduser(buildDir_AMDOVX+'/develop')
if(os.path.exists(develop_dir)):
	os.system('(cd '+buildDir_AMDOVX+'; rm -rf develop)');

os.system('(cd '+buildDir_AMDOVX+'; mkdir develop)');

print("\nCaffe Models access ..\n")
for i in range(len(caffeModelConfig)):
	modelName, channel, height, width = caffeModelConfig[i]
	os.system('(cd '+develop_dir+'; mkdir '+modelName+')');
	os.system('(cd '+develop_dir+'/'+modelName+'; cp -r ../../caffeModels/'+modelName+' .)');


# run caffe2openvx flow
if profileMode == 6 or profileMode == 1 or profileMode == 4:
	for i in range(len(caffeModelConfig)):
		modelName, channel, height, width = caffeModelConfig[i]
		print "\n caffe2openvx -- ",modelName,"\n"
		if(modelName == 'xyznet' or modelName == 'xyznet_18-04'):
			x = 1
			print "\n",modelName," - Batch size ", x
			x = str(x)
			os.system('(cd '+develop_dir+'/'+modelName+'; mkdir build_'+x+')');
			os.system('(cd '+develop_dir+'/'+modelName+'/build_'+x+'; export PATH=$PATH:/opt/rocm/bin; export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/rocm/lib; caffe2openvx ../'+modelName+'/'+modelName+'.caffemodel '+x+' '+str(channel)+' '+str(height)+' '+str(width)+')');
			os.system('(cd '+develop_dir+'/'+modelName+'/build_'+x+'; export PATH=$PATH:/opt/rocm/bin; export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/rocm/lib; caffe2openvx ../'+modelName+'/'+modelName+'.prototxt '+x+' '+str(channel)+' '+str(height)+' '+str(width)+')');
			os.system('(cd '+develop_dir+'/'+modelName+'/build_'+x+'; cmake .; make)');
			os.system('(cd '+develop_dir+'/'+modelName+'/build_'+x+'; echo '+modelName+' - Batch size '+x+'  | tee -a ../../output.log)');
			os.system('(cd '+develop_dir+'/'+modelName+'/build_'+x+'; MIOPEN_FIND_ENFORCE='+str(miopenFind)+' ./anntest | tee -a ../../output.log)');
		else:
			for x in range(profileLevel):
				x = 2**x
				print "\n",modelName," - Batch size ", x
				x = str(x)
				os.system('(cd '+develop_dir+'/'+modelName+'; mkdir build_'+x+')');
				os.system('(cd '+develop_dir+'/'+modelName+'/build_'+x+'; export PATH=$PATH:/opt/rocm/bin; export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/rocm/lib; caffe2openvx ../'+modelName+'/'+modelName+'.caffemodel '+x+' '+str(channel)+' '+str(height)+' '+str(width)+')');
				os.system('(cd '+develop_dir+'/'+modelName+'/build_'+x+'; export PATH=$PATH:/opt/rocm/bin; export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/rocm/lib; caffe2openvx ../'+modelName+'/'+modelName+'.prototxt '+x+' '+str(channel)+' '+str(height)+' '+str(width)+')');
				os.system('(cd '+develop_dir+'/'+modelName+'/build_'+x+'; cmake .; make)');
				os.system('(cd '+develop_dir+'/'+modelName+'/build_'+x+'; echo '+modelName+' - Batch size '+x+'  | tee -a ../../output.log)');
				os.system('(cd '+develop_dir+'/'+modelName+'/build_'+x+'; MIOPEN_FIND_ENFORCE='+str(miopenFind)+' ./anntest | tee -a ../../output.log)');

	runAwk_csv = r'''awk 'BEGIN { net = "xxx"; bsize = 1; } / - Batch size/ { net = $1; bsize = $5; } /average over 100 iterations/ { printf("%-16s,%3d,%8.3f ms,%8.3f ms\n", net, bsize, $4, $4/bsize); }' '''+develop_dir+'''/output.log > '''+develop_dir+'''/caffe2openvx_profile.csv'''
	os.system(runAwk_csv);
	runAwk_txt = r'''awk 'BEGIN { net = "xxx"; bsize = 1; } / - Batch size/ { net = $1; bsize = $5; } /average over 100 iterations/ { printf("%-16s %3d %8.3f ms %8.3f ms\n", net, bsize, $4, $4/bsize); }' '''+develop_dir+'''/output.log > '''+develop_dir+'''/caffe2openvx_profile.txt'''
	os.system(runAwk_txt);

	orig_stdout = sys.stdout
	sys.stdout = open(develop_dir+'/caffe2openvx_profile.md','a')
	echo_1 = '| Model Name | Batch Size | Time/Batch (ms) | Time/Image (ms) |'
	print(echo_1)
	echo_2 = '|------------|------------|-----------------|-----------------|'
	print(echo_2)
	sys.stdout = orig_stdout
	runAwk_md = r'''awk 'BEGIN { net = "xxx"; bsize = 1; } / - Batch size/ { net = $1; bsize = $5; } /average over 100 iterations/ { printf("|%-16s|%3d|%8.3f|%8.3f\n", net, bsize, $4, $4/bsize); }' '''+develop_dir+'''/output.log | tee -a '''+develop_dir+'''/caffe2openvx_profile.md'''
	os.system(runAwk_md);


# run caffe2nnir2openvx no fuse flow
if profileMode == 6 or profileMode == 2 or profileMode == 4 or profileMode == 5:
	modelCompilerScripts_dir = os.path.expanduser(buildDir_AMDOVX+'/amdovx-modules/utils/model_compiler/python')
	for i in range(len(caffeModelConfig)):
		modelName, channel, height, width = caffeModelConfig[i]
		print "\n caffe2nnir2openvx --",modelName,"\n"
		if(modelName == 'xyznet' or modelName == 'xyznet_18-04'):
			x = 1
			print "\n",modelName," - Batch size ", x
			x = str(x)
			os.system('(cd '+develop_dir+'/'+modelName+'; mkdir nnir_build_'+x+')');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_build_'+x+'; python '+modelCompilerScripts_dir+'/caffe2nnir.py ../'+modelName+'/'+modelName+'.caffemodel . --input-dims '+x+','+str(channel)+','+str(height)+','+str(width)+')');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_build_'+x+'; python '+modelCompilerScripts_dir+'/nnir2openvx.py . .)');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_build_'+x+'; cmake .; make)');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_build_'+x+'; echo '+modelName+' - Batch size '+x+'  | tee -a ../../nnir_output.log)');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_build_'+x+'; MIOPEN_FIND_ENFORCE='+str(miopenFind)+' ./anntest weights.bin | tee -a ../../nnir_output.log)');
		else:
			for x in range(profileLevel):
				x = 2**x
				print "\n",modelName," - Batch size ", x
				x = str(x)
				os.system('(cd '+develop_dir+'/'+modelName+'; mkdir nnir_build_'+x+')');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_build_'+x+'; python '+modelCompilerScripts_dir+'/caffe2nnir.py ../'+modelName+'/'+modelName+'.caffemodel . --input-dims '+x+','+str(channel)+','+str(height)+','+str(width)+')');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_build_'+x+'; python '+modelCompilerScripts_dir+'/nnir2openvx.py . .)');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_build_'+x+'; cmake .; make)');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_build_'+x+'; echo '+modelName+' - Batch size '+x+'  | tee -a ../../nnir_output.log)');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_build_'+x+'; MIOPEN_FIND_ENFORCE='+str(miopenFind)+' ./anntest weights.bin | tee -a ../../nnir_output.log)');

	runAwk_csv = r'''awk 'BEGIN { net = "xxx"; bsize = 1; } / - Batch size/ { net = $1; bsize = $5; } /average over 100 iterations/ { printf("%-16s,%3d,%8.3f ms,%8.3f ms\n", net, bsize, $4, $4/bsize); }' '''+develop_dir+'''/nnir_output.log > '''+develop_dir+'''/caffe2nnir2openvx_noFuse_profile.csv'''
	os.system(runAwk_csv);
	runAwk_txt = r'''awk 'BEGIN { net = "xxx"; bsize = 1; } / - Batch size/ { net = $1; bsize = $5; } /average over 100 iterations/ { printf("%-16s %3d %8.3f ms %8.3f ms\n", net, bsize, $4, $4/bsize); }' '''+develop_dir+'''/nnir_output.log > '''+develop_dir+'''/caffe2nnir2openvx_noFuse_profile.txt'''
	os.system(runAwk_txt);

	orig_stdout = sys.stdout
	sys.stdout = open(develop_dir+'/caffe2nnir2openvx_noFuse_profile.md','a')
	echo_1 = '| Model Name | Batch Size | Time/Batch (ms) | Time/Image (ms) |'
	print(echo_1)
	echo_2 = '|------------|------------|-----------------|-----------------|'
	print(echo_2)
	sys.stdout = orig_stdout
	runAwk_md = r'''awk 'BEGIN { net = "xxx"; bsize = 1; } / - Batch size/ { net = $1; bsize = $5; } /average over 100 iterations/ { printf("|%-16s|%3d|%8.3f|%8.3f\n", net, bsize, $4, $4/bsize); }' '''+develop_dir+'''/nnir_output.log | tee -a '''+develop_dir+'''/caffe2nnir2openvx_noFuse_profile.md'''
	os.system(runAwk_md);

# run caffe2nnir2openvx with fuse flow
if profileMode == 6 or profileMode == 3 or profileMode == 5:
	modelCompilerScripts_dir = os.path.expanduser(buildDir_AMDOVX+'/amdovx-modules/utils/model_compiler/python')
	for i in range(len(caffeModelConfig)):
		modelName, channel, height, width = caffeModelConfig[i]
		print "\n caffe2nnir2openvx --",modelName,"\n"
		if(modelName == 'xyznet' or modelName == 'xyznet_18-04'):
			x = 1
			print "\n",modelName," - Batch size ", x 
			x = str(x)
			os.system('(cd '+develop_dir+'/'+modelName+'; mkdir nnir_fuse_build_'+x+')');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; python '+modelCompilerScripts_dir+'/caffe2nnir.py ../'+modelName+'/'+modelName+'.caffemodel . --input-dims '+x+','+str(channel)+','+str(height)+','+str(width)+')');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; python '+modelCompilerScripts_dir+'/nnir-update.py --fuse-ops 1 . .)');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; python '+modelCompilerScripts_dir+'/nnir2openvx.py . .)');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; cmake .; make)');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; echo '+modelName+' - Batch size '+x+'  | tee -a ../../nnir_fuse_output.log)');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; MIOPEN_FIND_ENFORCE='+str(miopenFind)+' ./anntest weights.bin | tee -a ../../nnir_fuse_output.log)');
		else:
			for x in range(profileLevel):
				x = 2**x
				print "\n",modelName," - Batch size ", x 
				x = str(x)
				os.system('(cd '+develop_dir+'/'+modelName+'; mkdir nnir_fuse_build_'+x+')');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; python '+modelCompilerScripts_dir+'/caffe2nnir.py ../'+modelName+'/'+modelName+'.caffemodel . --input-dims '+x+','+str(channel)+','+str(height)+','+str(width)+')');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; python '+modelCompilerScripts_dir+'/nnir-update.py --fuse-ops 1 . .)');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; python '+modelCompilerScripts_dir+'/nnir2openvx.py . .)');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; cmake .; make)');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; echo '+modelName+' - Batch size '+x+'  | tee -a ../../nnir_fuse_output.log)');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; MIOPEN_FIND_ENFORCE='+str(miopenFind)+' ./anntest weights.bin | tee -a ../../nnir_fuse_output.log)');

	runAwk_csv = r'''awk 'BEGIN { net = "xxx"; bsize = 1; } / - Batch size/ { net = $1; bsize = $5; } /average over 100 iterations/ { printf("%-16s,%3d,%8.3f ms,%8.3f ms\n", net, bsize, $4, $4/bsize); }' '''+develop_dir+'''/nnir_fuse_output.log > '''+develop_dir+'''/caffe2nnir2openvx_fuse_profile.csv'''
	os.system(runAwk_csv);
	runAwk_txt = r'''awk 'BEGIN { net = "xxx"; bsize = 1; } / - Batch size/ { net = $1; bsize = $5; } /average over 100 iterations/ { printf("%-16s %3d %8.3f ms %8.3f ms\n", net, bsize, $4, $4/bsize); }' '''+develop_dir+'''/nnir_fuse_output.log > '''+develop_dir+'''/caffe2nnir2openvx_fuse_profile.txt'''
	os.system(runAwk_txt);

	orig_stdout = sys.stdout
	sys.stdout = open(develop_dir+'/caffe2nnir2openvx_fuse_profile.md','a')
	echo_1 = '| Model Name | Batch Size | Time/Batch (ms) | Time/Image (ms) |'
	print(echo_1)
	echo_2 = '|------------|------------|-----------------|-----------------|'
	print(echo_2)
	sys.stdout = orig_stdout
	runAwk_md = r'''awk 'BEGIN { net = "xxx"; bsize = 1; } / - Batch size/ { net = $1; bsize = $5; } /average over 100 iterations/ { printf("|%-16s|%3d|%8.3f|%8.3f\n", net, bsize, $4, $4/bsize); }' '''+develop_dir+'''/nnir_fuse_output.log | tee -a '''+develop_dir+'''/caffe2nnir2openvx_fuse_profile.md'''
	os.system(runAwk_md);
	
# run caffe2nnir2openvx with fuse flow
if profileMode == 9:
	modelCompilerScripts_dir = os.path.expanduser(buildDir_AMDOVX+'/amdovx-modules/utils/model_compiler/python')
	for i in range(len(caffeModelConfig)):
		modelName, channel, height, width = caffeModelConfig[i]
		print "\n caffe2nnir2openvx --",modelName,"\n"
		if(modelName == 'xyznet' or modelName == 'xyznet_18-04'):
			x = 1
			print "\n",modelName," - Batch size ", x 
			x = str(x)
			os.system('(cd '+develop_dir+'/'+modelName+'; mkdir nnir_fuse_build_'+x+')');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; python '+modelCompilerScripts_dir+'/caffe2nnir.py ../'+modelName+'/'+modelName+'.caffemodel . --input-dims '+x+','+str(channel)+','+str(height)+','+str(width)+')');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; python '+modelCompilerScripts_dir+'/nnir-update.py -–convert-fp16 1 . .)');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; python '+modelCompilerScripts_dir+'/nnir2openvx.py . .)');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; cmake .; make)');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; echo '+modelName+' - Batch size '+x+'  | tee -a ../../nnir_fuse_output.log)');
			os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; MIOPEN_FIND_ENFORCE='+str(miopenFind)+' ./anntest weights.bin | tee -a ../../nnir_fuse_output.log)');
		else:
			for x in range(profileLevel):
				x = 2**x
				print "\n",modelName," - Batch size ", x 
				x = str(x)
				os.system('(cd '+develop_dir+'/'+modelName+'; mkdir nnir_fuse_build_'+x+')');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; python '+modelCompilerScripts_dir+'/caffe2nnir.py ../'+modelName+'/'+modelName+'.caffemodel . --input-dims '+x+','+str(channel)+','+str(height)+','+str(width)+')');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; python '+modelCompilerScripts_dir+'/nnir-update.py –-convert-fp16 1 . .)');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; python '+modelCompilerScripts_dir+'/nnir2openvx.py . .)');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; cmake .; make)');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; echo '+modelName+' - Batch size '+x+'  | tee -a ../../nnir_fuse_output.log)');
				os.system('(cd '+develop_dir+'/'+modelName+'/nnir_fuse_build_'+x+'; MIOPEN_FIND_ENFORCE='+str(miopenFind)+' ./anntest weights.bin | tee -a ../../nnir_fuse_output.log)');

	runAwk_csv = r'''awk 'BEGIN { net = "xxx"; bsize = 1; } / - Batch size/ { net = $1; bsize = $5; } /average over 100 iterations/ { printf("%-16s,%3d,%8.3f ms,%8.3f ms\n", net, bsize, $4, $4/bsize); }' '''+develop_dir+'''/nnir_fuse_output.log > '''+develop_dir+'''/caffe2nnir2openvx_fp16_profile.csv'''
	os.system(runAwk_csv);
	runAwk_txt = r'''awk 'BEGIN { net = "xxx"; bsize = 1; } / - Batch size/ { net = $1; bsize = $5; } /average over 100 iterations/ { printf("%-16s %3d %8.3f ms %8.3f ms\n", net, bsize, $4, $4/bsize); }' '''+develop_dir+'''/nnir_fuse_output.log > '''+develop_dir+'''/caffe2nnir2openvx_fp16_profile.txt'''
	os.system(runAwk_txt);

	orig_stdout = sys.stdout
	sys.stdout = open(develop_dir+'/caffe2nnir2openvx_fuse_profile.md','a')
	echo_1 = '| Model Name | Batch Size | Time/Batch (ms) | Time/Image (ms) |'
	print(echo_1)
	echo_2 = '|------------|------------|-----------------|-----------------|'
	print(echo_2)
	sys.stdout = orig_stdout
	runAwk_md = r'''awk 'BEGIN { net = "xxx"; bsize = 1; } / - Batch size/ { net = $1; bsize = $5; } /average over 100 iterations/ { printf("|%-16s|%3d|%8.3f|%8.3f\n", net, bsize, $4, $4/bsize); }' '''+develop_dir+'''/nnir_fuse_output.log | tee -a '''+develop_dir+'''/caffe2nnir2openvx_fp16_profile.md'''
	os.system(runAwk_md);
