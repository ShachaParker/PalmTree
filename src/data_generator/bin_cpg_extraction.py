import os
import re
import json
import shutil
# import utils.process as process
from cpg_generator import joern_create_dfg, joern_create_cfg, joern_parse, joern_create
import configs
import pydot
import html
# from normalize import hierarchical_normalization
import numpy as np
from sklearn.preprocessing import OneHotEncoder
#from transformers import RobertaTokenizer, RobertaModel
import torch

# PATHS = configs.Paths()
# FILES = configs.Files()
# DEVICE = FILES.get_device()
flag = True

def get_matching_files(root_dir):
    has_dirs = any(os.path.isdir(os.path.join(root_dir, name)) for name in os.listdir(root_dir))
    if not has_dirs:
        # If no directories are present, return the files in the root directory
        return [os.path.join(root_dir, name) for name in os.listdir(root_dir) if os.path.isfile(os.path.join(root_dir, name))]
    renamed_paths = set()

    for subdir, _, files in os.walk(root_dir):
        # Get the name of the parent directory
        parent_dir = os.path.basename(subdir)
        # Check if the parent directory matches the pattern
        
        for file in files:
            new_file_name = f"{parent_dir}/{file}" if not file.startswith(f"{parent_dir}-") else file
            original_file_path = os.path.join(subdir, file)
            new_file_path = os.path.join(root_dir, new_file_name)

            # Track the moved file path
            renamed_paths.add(new_file_path)

    return list(renamed_paths)

def extract_cpgs_from_files(files, output_dir):
    """Extract CPGs from the list of files and store them in the output directory."""
    # context = configs.Create()

    # all of these are relative paths that may need to be changed to absolute paths
    # joern and joern_cli must be installed somewhere, and linked to int the below assignment
    joern_cli_dir = '/...path-to/joern/joern-cli/'
    cpg_files = []
    inputPath = f"./data/input/curl/focus/"
    intermediatePath = f'./data/intermediary_output/curl/'
    CFGOutput = f"./data/output/cfg"
    DFGOutput = f"./data/output/dfg"
    CPGFiles = 'cpg'

    # override: files becomes inputPath
    files = get_matching_files(inputPath)

    print("Input source:", inputPath)

    
    for file in files:
        print(f"Processing file: {file}")
        file_name = file.split('/')[-1]
        # Create CPG
        # if file_name.startswith("x86-clang-O3-"):
        cpg_file = joern_parse(joern_cli_dir, inputPath + file_name, intermediatePath, f"{file_name}_{CPGFiles}")
        print(f"CPG file created: {cpg_file}")
        cpg_files.append(cpg_file)
    
    
    cpg_files = [f for f in os.listdir(intermediatePath)]

    #dot_folders = joern_create(joern_cli_dir, intermediatePath, outputPath, cpg_files)


    joern_create_cfg(joern_cli_dir, intermediatePath, CFGOutput, cpg_files)
    joern_create_dfg(joern_cli_dir, intermediatePath, DFGOutput, cpg_files)

    #joern_create(joern_cli_dir, inputPath, intermediatePath, cpg_files)

    # Windows
    # dot_folders = [f for f in os.listdir("data\\dot_graph\\")]

    # Mac/Linux
    # dot_folders = [f for f in os.listdir("data/dot_graph/")]

    return

def clean_label(label):
    return html.unescape(label)

def fix_orders(graph):
    nodes = graph.get_nodes()
    edges = graph.get_edges()
    
    old_to_new_mapping = {}
    new_node_number = 0

    for node in nodes:
        old_node_number = node.get_name().strip('"')
        old_to_new_mapping[old_node_number] = str(new_node_number)
        new_node_number += 1

    for node in nodes:
        old_node_number = node.get_name().strip('"')
        new_node_number = old_to_new_mapping[old_node_number]
        node.set_name(new_node_number)
    
    updated_edges = []
    for edge in edges:
        old_source = edge.get_source().strip('"')
        old_destination = edge.get_destination().strip('"')
        new_source = old_to_new_mapping[old_source]
        new_destination = old_to_new_mapping[old_destination]
        edge_type = edge.get_label().strip('"').split(':')[0]
        updated_edges.append((new_source, new_destination, edge_type))
    
    return graph, updated_edges

def edge_processing(edges, num_nodes):
    edge_index = []
    edge_type = []
    edge_type_mapping = {"AST": 0, "CFG": 1, "DDG": 2, "NCS": 3}

    for edge in edges:
        src = int(edge[0])
        dst = int(edge[1])  
        e_type = edge_type_mapping[edge[2]]
        edge_index.append([src, dst])
        edge_type.append(e_type)

    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    edge_type = torch.tensor(edge_type, dtype=torch.long)

    return edge_index, edge_type

def extract_label_for_encoding(label):
    return label[0]

def one_hot_encode_labels(labels, onehot_encoder):
    extracted_labels = [extract_label_for_encoding(label) for label in labels]
    onehot_encoded = onehot_encoder.transform(np.array(extracted_labels).reshape(-1, 1))
    last_tokens = [label[-1] for label in labels if label[-1].startswith('pos')]
    global_label_encoder.fit(last_tokens)

    structured_labels = []
    for original_label, one_hot_encoded in zip(labels, onehot_encoded):
        one_hot_encoded_str = ''.join(map(str, one_hot_encoded.astype(int)))

        # Extract tokens for CodeBERT: all except the first and potentially the last
        main_tokens = original_label[1:-1]  # All tokens except the first and last
        
        # Handle the last token for label encoding or pass-through
        last_token = original_label[-1]
        if last_token.startswith('pos'):
            if flag == False:
                print(global_label_encoder.transform([last_token])[0])
                flag = True
            last_token_encoded = str(global_label_encoder.transform([last_token])[0])
        else:
            last_token_encoded = None  # No encoding, will be passed as is to CodeBERT
        
        structured_labels.append((one_hot_encoded_str, " ".join(main_tokens), last_token, last_token_encoded))
    
    return structured_labels


def concatenate_embeddings_with_encodings(structured_labels, codebert_embeddings):
    concatenated_embeddings = []
    
    for i, (one_hot_encoded_str, _, last_token, last_token_encoded) in enumerate(structured_labels):
        # Convert the one-hot encoded string back to a vector
        one_hot_encoded_vector = np.array(list(map(int, one_hot_encoded_str)), dtype=np.float32)
        
        # Get the embedding from CodeBERT
        embedding_vector = codebert_embeddings[i].cpu().numpy()  # Convert to NumPy array
        
        # Handle the last token: either include the label-encoded value or pass it as is
        if last_token_encoded is not None:
            label_encoded_value = np.array([float(last_token_encoded)], dtype=np.float32)
            combined_vector = np.concatenate([one_hot_encoded_vector, embedding_vector, label_encoded_value])
        else:
            # Include the last token's embedding from CodeBERT, as it was part of the input
            combined_vector = np.concatenate([one_hot_encoded_vector, embedding_vector])
        
        concatenated_embeddings.append(combined_vector)
    
    return np.array(concatenated_embeddings)

def add_ncs_edges(graph):
    # Identify AST leaves
    ast_leaves = []
    for node in graph.get_nodes():
        node_name = node.get_name()
        # Check if the node has outgoing edges
        out_edges = [edge for edge in graph.get_edges() if edge.get_source() == node_name]
        if len(out_edges) == 0:  # No outgoing edges means it's a leaf
            ast_leaves.append(node)

    # Add NCS edges between neighboring AST leaves
    for i in range(len(ast_leaves) - 1):
        src = ast_leaves[i].get_name()
        dst = ast_leaves[i + 1].get_name()
        graph.add_edge(pydot.Edge(src, dst, label="NCS"))  # Assuming NCS edges are red

    return graph


def preprocess_labels(labels):
    # Extract the main tokens that will be passed to CodeBERT
    main_tokens = [item[1] for item in labels]
    inputs = tokenizer(main_tokens, return_tensors='pt', padding=True, truncation=True)
    return inputs

def get_embeddings(inputs):
    inputs = {key: value.to(device) for key, value in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state

def extract_first_tokens_and_labels(dot_folders):
    first_tokens = []
    all_labels_by_file = {}
    
    for d in dot_folders:
        for root, _, files in os.walk(os.path.join("dot_graph", d)):
            for f in files:
                dot = os.path.join(root, f)
                graphs = pydot.graph_from_dot_file(dot)
                graph = graphs[0]
                nodes = graph.get_nodes()
                print(graph.get_name())
                cleaned_node_labels = [clean_label(node.get_label().strip('"')) for node in nodes]
                
                # Call hierarchical_normalization once
                level1, level2, level3, level4 = hierarchical_normalization(cleaned_node_labels, "x86")  # Example architecture
                
                all_levels = level1 + level2 + level3 + level4
                file_labels = {
                    'level1': level1,
                    'level2': level2,
                    'level3': level3,
                    'level4': level4
                }
                
                all_labels_by_file[(root, f)] = file_labels
                for label in level1:
                    first_token = extract_label_for_encoding(label)
                    first_tokens.append(first_token)

    return list(set(first_tokens)), all_labels_by_file

def save_embeddings(embeddings, base_folder, level):
    for idx, embedding in enumerate(embeddings):
        torch.save(embedding.cpu(), os.path.join(base_folder, f'node_embeddings_level{level}_{idx}.pt'))

def fit_global_one_hot_encoder(labels):
    print(labels)
    onehot_encoder = OneHotEncoder(handle_unknown = 'ignore')
    onehot_encoder.fit(np.array(labels).reshape(-1, 1))
    print(onehot_encoder.categories_)
    return onehot_encoder


def normalize_graphs(dot_folders):
    first_tokens, all_labels_by_file = extract_first_tokens_and_labels(dot_folders)
    global_onehot_encoder = fit_global_one_hot_encoder(first_tokens)

    tokenizer = RobertaTokenizer.from_pretrained('microsoft/codebert-base')
    model = RobertaModel.from_pretrained('microsoft/codebert-base')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)

    for (root, f), labels_dict in all_labels_by_file.items():
        dot = os.path.join(root, f)
        architecture = root.split('/')[-1].split('-')[0]
        graphs = pydot.graph_from_dot_file(dot)
        graph = graphs[0]
        graph = add_ncs_edges(graph)
        graph, edges = fix_orders(graph)
        nodes = graph.get_nodes()
        edge_indexes, edge_types = edge_processing(edges, len(nodes))
        
        # One-hot encode all levels
        structured_level1 = one_hot_encode_labels(labels_dict['level1'], global_onehot_encoder)
        structured_level2 = one_hot_encode_labels(labels_dict['level2'], global_onehot_encoder)
        structured_level3 = one_hot_encode_labels(labels_dict['level3'], global_onehot_encoder)
        structured_level4 = one_hot_encode_labels(labels_dict['level4'], global_onehot_encoder)

        # Map node names to encoded labels
        node_name_to_label_level1 = {node.get_name(): label for node, label in zip(nodes, structured_level1)}
        node_name_to_label_level2 = {node.get_name(): label for node, label in zip(nodes, structured_level2)}
        node_name_to_label_level3 = {node.get_name(): label for node, label in zip(nodes, structured_level3)}
        node_name_to_label_level4 = {node.get_name(): label for node, label in zip(nodes, structured_level4)}

        # Preprocess labels with CodeBERT
        inputs_level1 = preprocess_labels(structured_level1)
        inputs_level2 = preprocess_labels(structured_level2)
        inputs_level3 = preprocess_labels(structured_level3)
        inputs_level4 = preprocess_labels(structured_level4)

        # Get embeddings
        embeddings_level1 = get_embeddings(inputs_level1)
        embeddings_level2 = get_embeddings(inputs_level2)
        embeddings_level3 = get_embeddings(inputs_level3)
        embeddings_level4 = get_embeddings(inputs_level4)

        final_embeddings_level1 = concatenate_embeddings_with_encodings(structured_level1, embeddings_level1)
        final_embeddings_level2 = concatenate_embeddings_with_encodings(structured_level2, embeddings_level2)
        final_embeddings_level3 = concatenate_embeddings_with_encodings(structured_level3, embeddings_level3)
        final_embeddings_level4 = concatenate_embeddings_with_encodings(structured_level4, embeddings_level4)

        # Save embeddings
        output_folder = os.path.join("output", root, graph.get_name().strip('"'))
        os.makedirs(output_folder, exist_ok=True)
        save_embeddings(final_embeddings_level1, output_folder, 1)
        save_embeddings(final_embeddings_level2, output_folder, 2)
        save_embeddings(final_embeddings_level3, output_folder, 3)
        save_embeddings(final_embeddings_level4, output_folder, 4)


        base_folder = os.path.join("embeddings", d, graph.get_name().strip('"'))
        os.makedirs(base_folder, exist_ok=True)

        with open(os.path.join(base_folder, 'level1.txt'), 'w') as file:
            for node, label in zip(nodes, structured_level1):
                file.write(f"{node.get_name()} {label}\n")
        
        with open(os.path.join(base_folder, 'level2.txt'), 'w') as file:
            for node, label in zip(nodes, structured_level2):
                file.write(f"{node.get_name()} {label}\n")
        
        with open(os.path.join(base_folder, 'level3.txt'), 'w') as file:
            for node, label in zip(nodes, structured_level3):
                file.write(f"{node.get_name()} {label}\n")
        
        with open(os.path.join(base_folder, 'level4.txt'), 'w') as file:
            for node, label in zip(nodes, structured_level4):
                file.write(f"{node.get_name()} {label}\n")

        torch.save(edge_indexes, os.path.join(output_folder, 'edge_index.pt'))
        torch.save(edge_types, os.path.join(output_folder, 'edge_type.pt'))

    


if __name__ == "__main__":
    # Define the directory, pattern, and output directory
    #   directory = os.path.join('data', 'bin_input', 'openssl-1.1.1a')
    
    # this path is relative and may need to be changed to absolute
    directory = './data/input'
    
    # pattern = r".*64-gcc-O2"
    # pattern = r".*"
    output_dir = os.path.join("data", "cpg")
    
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    
    # Get the matching files
    matching_files = get_matching_files(directory)
    print(f"Found {len(matching_files)} matching files.")
    
    # tokenizer = RobertaTokenizer.from_pretrained('microsoft/codebert-base')
    # model = RobertaModel.from_pretrained('microsoft/codebert-base')

    # Check if GPU is available
    #device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    #model.to(device)
    # Extract CPGs from the matching files
    dot_folders = extract_cpgs_from_files(matching_files, output_dir)
    print("CPG extraction completed.")
    #extract graphs from
    # normalize_graphs(dot_folders)