#!/usr/bin/env python

#########################################################
#
# Creates an experiment directory for cell detection pipeline 
#
# Author: Alex Riordan
#
# Description: creates a user-specified directory with
#              training/test/validation subdirectories and
#              an autopopulated main_config.cfg file 
#
# Usage: dir_name is user-specified directory, should be an absolute path
#    
#
################################################################

import os, shutil, ConfigParser

def create_experiment_directory(dir_name):
    if not os.path.exists(dir_name):
            os.makedirs(dir_name)
    else:
        raise AssertionError('Directory already exists.\n Choose a different name for your new experiment directory. ', dir_name)
    os.makedirs(dir_name + '/labeled/test')
    os.makedirs(dir_name + '/labeled/training')
    os.makedirs(dir_name + '/labeled/validation')

def copy_main_config(dir_name):
    src_path = os.path.dirname(os.path.abspath(__file__)) 
    shutil.copy(src_path + '/main_config.cfg', dir_name)
    config_path = dir_name + '/main_config.cfg'
    
    cfg_parser = ConfigParser.SafeConfigParser()
    cfg_parser.readfp(open(config_path, 'r'))
    
    cfg_parser.set('general','data_dir', dir_name + '/labeled')
    cfg_parser.set('general','downsample_dir', dir_name + '_downsampled')
    cfg_parser.set('general','preprocess_dir', dir_name + '_preprocessed/labeled')
    cfg_parser.set('general','postprocess_dir', dir_name + '_postprocessed')
    
    repo_path = src_path.split('ConvnetCellDetection')[0] + 'ConvnetCellDetection/celldetection_znn'
    cfg_parser.set('network','net_arch_fpath', repo_path + '/N1.znn')
    
    cfg_parser.set('training','training_input_dir', dir_name + '_preprocessed/labeled')
    cfg_parser.set('training','training_output_dir', dir_name + '_preprocessed/labeled/training_output')
    cfg_parser.set('training','training_net_prefix', dir_name + '_preprocessed/labeled/training_output/N1')
    
    cfg_parser.set('forward','forward_net', dir_name + '_preprocessed/labeled/training_output/N1_current.h5')
    cfg_parser.set('forward','forward_input_dir', dir_name + '_preprocessed/labeled')
    cfg_parser.set('forward','forward_output_dir', dir_name + '_preprocessed/labeled/training_output')
    
    with open(config_path, 'wb') as configfile:
        cfg_parser.write(configfile)
        
        
def main(dir_name = '/Users/sergiomartinez/Documents/ConvnetCellDetection/data/new_expt'):
    create_experiment_directory(dir_name)
    copy_main_config(dir_name)
    print 'new experiment directory', dir_name, 'successfully created.'
    
if __name__ == "__main__":
    main()
