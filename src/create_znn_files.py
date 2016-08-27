#!/usr/bin/env python

'''
 Python pipeline for creating ZNN files
 
 Author: Alex Riordan
      
 Description: script that reads parameters from main
    configuration file and creates ZNN configuration,
    network, and dataset.spec files accordingly
'''

import os, sys, shutil
import ConfigParser
from preprocessing import (is_labeled, get_labeled_split, split_labeled_directory,
                           put_labeled_at_end_of_path_if_not_there, remove_ds_store)
    
'''new_create_dataset_spec
 N.B. this method will cause issues if any non-ROI filenames contain '_ROI.'
 will also cause issues if files aren't .tif
 
 writes dataset.spec file and returns number of image/label pairs referenced therein 
'''
def create_dataset_spec(input_dir, output_dir, file_dict):
    f = open(output_dir + '/dataset.spec','w+') 

    #Build a list of absolute file paths, with index given by file_dict
    files = range(len(file_dict.keys())) 
    for fname, value in file_dict.items() :
        if value[1] == '' : 
            files[value[0] - 1] = (input_dir + '/' + fname)
        else:
            files[value[0] - 1] = (input_dir + '/' + value[1] + '/' + fname)
    
    files = [x for x in files if "_ROI." not in x] # remove all filepaths with '_ROI.'
    files = [x.replace('.tif','') for x in files] # remove .tif file extension
    files = [dockerize_path(x) for x in files]
    
    s = ''
    #Iterate over remaining list. Write dataset.spec file. Sample number of file corresponds to index in file_dict.
    #TODO: Forward pass: for .tif files without corresponding ROI files, should just have label be equal to orig. .tif file
    for fname in files:
        section_num = file_dict[fname.split('/')[-1] + '.tif'][0]
        stk_path = fname
        s = write_one_section_dataset_spec(s, section_num, '' + fname + '.tif', fname + '_ROI.tif')
    f.write(s)
    f.close()
    
    return len(files)

'''
 write_one_section_dataset_spec
 Helper method for create_dataset_spec
 Given a unique stk filename and its corresponding ROI file, creates one section of a ZNN dataset.spec file
'''
def write_one_section_dataset_spec(s, section_num, stk_path, roi_path):
    s += '[image ' + str(section_num) +']\n'
    s += 'fnames = ' + str(stk_path) + '\n'
    s += 'pp_types = standard3D\n'
    s += 'is_auto_crop = yes\n\n'

    s += '[label ' + str(section_num) +']\n'
    s += 'fnames = ' + str(roi_path) + '\n'
    s += 'pp_types = auto\n'
    s += 'is_auto_crop = yes\n\n'
    
    s += '[sample ' + str(section_num) +']\n'
    s += 'input = ' + str(section_num) + '\n'
    s += 'output = ' + str(section_num) + '\n\n'
    
    return s

'''
 dockerize_path
 Rewrites user-provided path to point to mounted directory in Docker container
 Assumes ConvnetCellDetection directory is mounted in 'znn-release' directory in Docker container
 N.B. Assumes that no subfolders of ConvnetCellDetection are named 'ConvnetCellDetection'
'''
def dockerize_path(user_path):
    s = user_path.split('ConvnetCellDetection')
    new_path = '../ConvnetCellDetection' + s[1]
    return new_path

'''
'''
def create_znn_config_file(output_dir, train_indices, val_indices, forward_indices, net_arch_fpath,
                           train_net_prefix, train_patch_size, learning_rate, momentum, num_iter_per_save,
                           max_iter, forward_net,forward_outsz, num_file_pairs):
    #copy default_znn_config.cfg from src to output_dir
    src_path = os.path.dirname(os.path.abspath(__file__))
    znn_config_path = output_dir + '/znn_config.cfg'
    shutil.copy(src_path + '/default_znn_config.cfg', znn_config_path)

    #use configParser to modify fields in new config file
    znn_cfg_parser = ConfigParser.SafeConfigParser()
    znn_cfg_parser.readfp(open(znn_config_path, 'r'))
    
    znn_cfg_parser.set('parameters','fnet_spec', dockerize_path(net_arch_fpath))
    znn_cfg_parser.set('parameters', 'fdata_spec', dockerize_path(output_dir + '/dataset_spec'))
    znn_cfg_parser.set('parameters', 'train_net_prefix', dockerize_path(train_net_prefix))
    znn_cfg_parser.set('parameters', 'train_range', train_indices)
    znn_cfg_parser.set('parameters', 'test_range', val_indices)
    znn_cfg_parser.set('parameters', 'train_outsz', train_patch_size)
    znn_cfg_parser.set('parameters', 'eta', learning_rate)
    znn_cfg_parser.set('parameters', 'momentum', momentum)
    znn_cfg_parser.set('parameters', 'Num_iter_per_save', num_iter_per_save)
    znn_cfg_parser.set('parameters', 'max_iter', max_iter)
    znn_cfg_parser.set('parameters', 'forward_range', forward_indices) #autoset as everything in input_dir
    znn_cfg_parser.set('parameters', 'forward_net', forward_net)
    znn_cfg_parser.set('parameters', 'forward_outsz', forward_outsz) #TODO: calculate forward_outsz automatically, based on field of view
    znn_cfg_parser.set('parameters', 'output_prefix', net_arch_fpath[:-4])
    with open(znn_config_path, 'wb') as configfile:
        znn_cfg_parser.write(configfile)

'''
Input: file_dict dictionary with keys = input_tif_file_names, values = (index, subdir for train/val/test split if applicable)
Output: string of comma-separated indices for training set, validation set, and files upon which to perform
    a forward pass (for znn_config.cfg)
'''
def get_train_val_forward_split_indices_as_str(file_dict) :
    pass
    train_indices = ''
    val_indices = ''
    forward_indices = ''
    no_subdirs = True
    for key, values in file_dict.items():
        if values[1] == 'training' and "_ROI." not in key:
            train_indices += str(values[0]) + ','
            no_subdirs = False
        if values[1] == 'validation' and "_ROI." not in key:
            val_indices += str(values[0]) + ','
            no_subdirs = False
        if "_ROI." not in key:
            forward_indices += str(values[0]) + ','
    if no_subdirs:
        train_indices = '1'
        val_indices = '1'
    if train_indices[-1] == ',':
        train_indices = train_indices[:-1]
    if val_indices[-1] == ',':
        val_indices = val_indices[:-1]
    if forward_indices[-1] ==',':
        forward_indices = forward_indices[:-1]
    return train_indices, val_indices, forward_indices

def copy_template_network_file():
    pass

def modify_network_conv_filter_size():
    pass

'''
'''
def modify_network_3D_to_2D_squashing_filter_size(net_file, filter_size):
    #find lines corresponding to squashing filter (search for first line that says "type max_filter")
    #below that are size Z,1,1 and
    # stride Z,1,1
    #we can assume that a (2+1)D network check has been run
    pass

'''
Returns dict where keys are file names of file_dir and values are the empty string ''
'''
def build_unlabeled_file_dict(file_dir):
    files = os.listdir(file_dir)
    remove_ds_store(files)
    file_dict = dict()
    file_dict.update(dict.fromkeys(files,''))
    return file_dict 

'''
Updates values in a dictionary to be a tuple with (integer_index, original_value)
'''
def add_indices_to_dict(fname_dict):
    index = 1 
    for fname, orig_value in fname_dict.items():
        fname_dict[fname] = (index,orig_value)
        index += 1 

'''
Gets input/output directories for either training data or forward pass
'''
def get_io_dirs(run_type):
    if run_type != 'forward' and run_type != 'training':
        raise Exception('run_type variable should be one of "forward" or "training"', run_type)
    input_dir = cfg_parser.get(run_type, run_type + '_input_dir')
    output_dir = cfg_parser.get(run_type, run_type + '_output_dir')
    return input_dir, output_dir
    
'''
Checks that depth of tif files in dataset is same across files and matches depth of network. 
'''
def check_tif_depth():
    pass


if __name__ == "__main__":
    '''Get user-specified information from main_config.cfg'''
    cfg_parser = ConfigParser.SafeConfigParser()
    cfg_parser.readfp(open('../main_config_ar.cfg', 'r'))
    img_width = cfg_parser.get('general', 'img_width')
    img_height = cfg_parser.get('general', 'img_height')
    net_arch_fpath = cfg_parser.get('network', 'net_arch_fpath')
    train_net_prefix = cfg_parser.get('training', 'training_net')
    train_patch_size = cfg_parser.get('training', 'patch_size')
    learning_rate = cfg_parser.get('training', 'learning_rate')
    momentum = cfg_parser.get('training', 'momentum')
    num_iter_per_save = cfg_parser.get('training', 'num_iter_per_save')
    max_iter = cfg_parser.get('training', 'max_iter')
    forward_net = cfg_parser.get('forward', 'forward_net')
    forward_outsz = cfg_parser.get('forward', 'forward_outsz')
    
    run_type = 'training' #this var will be set in pipeline.py
    
    '''Get and make user-specified input/output directories'''
    input_dir, output_dir = get_io_dirs(run_type)
    if not os.path.isdir(input_dir): 
        os.makedirs(input_dir)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    docker_dir = dockerize_path(output_dir)

    '''Build file name dictionary'''
    if is_labeled(input_dir):
        file_dict = get_labeled_split(input_dir)
    else:
        file_dict = build_unlabeled_file_dict(input_dir)
    add_indices_to_dict(file_dict)
    train_indices, val_indices, forward_indices = get_train_val_forward_split_indices_as_str(file_dict)
    
    print file_dict 
    
    '''Create znn files and put in output_dir'''
    num_file_pairs = create_dataset_spec(input_dir, output_dir, file_dict) #TODO: test training with Docker 
    create_znn_config_file(output_dir, train_indices, val_indices, forward_indices, net_arch_fpath,
                           train_net_prefix, train_patch_size, learning_rate, momentum, num_iter_per_save,
                           max_iter, forward_net,forward_outsz, num_file_pairs)
    
    # copy_template_network_file()
    # set_network_conv_filter_size()
    # set_network_max_filter_size()
    