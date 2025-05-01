import json
import re
import subprocess
import os.path
import os
import time
import tempfile
# from .cpg_client_wrapper import CPGClientWrapper
#from ..data import datamanager as data


def funcs_to_graphs(funcs_path):
    client = CPGClientWrapper()
    # query the cpg for the dataset
    print(f"Creating CPG.")
    graphs_string = client(funcs_path)
    # removes unnecessary namespace for object references
    graphs_string = re.sub(r"io\.shiftleft\.codepropertygraph\.generated\.", '', graphs_string)
    graphs_json = json.loads(graphs_string)

    return graphs_json["functions"]


def graph_indexing(graph):
    idx = int(graph["file"].split(".c")[0].split("/")[-1])
    del graph["file"]
    return idx, {"functions": [graph]}

# this has been renamed joern_parser. the new joern_parse function is a workaround for this original joern_parse function
def joern_parser(joern_path, input_path, output_path, file_name):
    out_file = file_name + ".bin"
    print("Parse Inputs:", joern_path,input_path,output_path)

    print("Attempted Command:", joern_path + "joern-parse", input_path, "--output", output_path + out_file, "--language", "ghidra")

    try:
        joern_parse_call = subprocess.run([joern_path + " joern-parse", input_path, "--output", output_path + out_file, "--language", "ghidra"],
                                      stdout=subprocess.PIPE, text=True, check=True, shell=True)
        print(str(joern_parse_call))

    except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr}")
    return out_file

# workaround function for joern-parse
def joern_parse(joern_path, input_path, output_path, output_file):
    output_file = output_file + ".bin"
    joern_parse_executable = os.path.join(joern_path, "joern-parse")  # Add the executable
    output_path = os.path.join(output_path, output_file)
    command = f"{joern_parse_executable} {input_path} --output {output_path} --language ghidra"
    
    print(f"Attempted Command: {command}")
    result = os.system(command)  # Execute the command
    if result != 0:
        print(f"Error: Command failed with exit code {result}")
        return None

    print(output_file)
    return output_file


def joern_create(joern_path, in_path, out_path, cpg_files):
    json_files = []

    # Ensure the output directory exists
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    dot_folders = []
    for cpg_file in cpg_files:
        out_folder = os.path.join(os.path.abspath(out_path), '-'.join(cpg_file.split('_')[:2]))
        dot_folders.append(out_folder)
        cpg_file_path = os.path.abspath(os.path.join(in_path, cpg_file))

        command = [
            joern_path + "joern-export",
            "--repr=cpg14", "--format=dot",
            "-o",out_folder,cpg_file_path]
        print(command)
        try:
            result = subprocess.run(command, capture_output=True, text=True, shell=True)

        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr}")

        if result.returncode != 0:
            print(f"Error running script for {cpg_file}: {result.stderr}")
        else:
            print(f"Successfully generated {out_folder}")

        # Clean up the temporary script file
    
    return dot_folders

def joern_create_cfg(joern_path, in_path, out_path, cfg_files):
    print("Creating CFGs")
    print("Joern Path: ", joern_path)
    print("Input Path: ", in_path)
    print("Output Path: ", out_path)
    print("CFG Files: ", cfg_files)
    json_files = []
    # Ensure the output directory exists
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    dot_folders = []
    for cfg_file in cfg_files:
        print(f"Processing CFG file: {cfg_file}")
        out_folder = os.path.join(os.path.abspath(out_path), '-'.join(cfg_file.split('_')[:2]))
        print("Out_Folder: ", out_folder)

        #out_folder = "/".join(out_folder.split("/")[:-1])

        dot_folders.append(out_folder)
        cfg_file_path = os.path.abspath(os.path.join(in_path, cfg_file))
        
        command = f"{joern_path}joern-export --repr=cfg --format=dot -o {out_folder} {cfg_file_path}"
    
        print(f"Command: {command}")
        try:
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            print(f"Command Output: {result.stdout}")
            print(f"Command Error (if any): {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr}")

        if result.returncode != 0:
            print(f"Error running script for {cfg_file}: {result.stderr}")
        else:
            print(f"Successfully generated {out_folder}")

        # Clean up the temporary script file

def joern_create_dfg(joern_path, in_path, out_path, dfg_files):
    print("Creating DFGs")
    print("Joern Path: ", joern_path)
    print("Input Path: ", in_path)
    print("Output Path: ", out_path)
    print("DFG Files: ", dfg_files)
    json_files = []
    # Ensure the output directory exists
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    dot_folders = []
    for dfg_file in dfg_files:
        print(f"Processing DFG file: {dfg_file}")
        out_folder = os.path.join(os.path.abspath(out_path), '-'.join(dfg_file.split('_')[:2]))
        print("Output Folder: ", out_folder)
        dot_folders.append(out_folder)
        dfg_file_path = os.path.abspath(os.path.join(in_path, dfg_file))
        
        command = f"{joern_path}joern-export --repr=ddg --format=dot -o {out_folder} {dfg_file_path}"

        print(f"Command: {command}")
        try:
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            print(f"Command Output: {result.stdout}")
            print(f"Command Error (if any): {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr}")

        if result.returncode != 0:
            print(f"Error running script for {dfg_file}: {result.stderr}")
        else:
            print(f"Successfully generated {out_folder}")

        # Clean up the temporary script file

def json_process(in_path, json_file):
    if os.path.exists(in_path+json_file):
        with open(in_path+json_file) as jf:
            cpg_string = jf.read()
            cpg_string = re.sub(r"io/.shiftleft/.codepropertygraph/.generated/.", '', cpg_string)
            cpg_json = json.loads(cpg_string)
            container = [graph_indexing(graph) for graph in cpg_json["functions"] if graph["file"] != "N/A"]
            return container
    return None

'''
def generate(dataset, funcs_path):
    dataset_size = len(dataset)
    print("Size: ", dataset_size)
    graphs = funcs_to_graphs(funcs_path[2:])
    print(f"Processing CPG.")
    container = [graph_indexing(graph) for graph in graphs["functions"] if graph["file"] != "N/A"]
    graph_dataset = data.create_with_index(container, ["Index", "cpg"])
    print(f"Dataset processed.")

    return data.inner_join_by_index(dataset, graph_dataset)
'''

# client = CPGClientWrapper()
# client.create_cpg("../../data/joern/")
# joern_parse("../../joern/joern-cli/", "../../data/joern/", "../../joern/joern-cli/", "gen_test")
# print(funcs_to_graphs("/data/joern/"))
"""
while True:
    raw = input("query: ")
    response = client.query(raw)
    print(response)
"""
