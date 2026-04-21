# PalmTree
## Created by Xuezixiang Li, Yu Qu, and Heng Yin
## Fork of original source by Shacha Parker

This fork of PalmTree has been modified to work without BinaryNinja, and instead uses the Ghidra and Joern tools.

##### Requirements:
Ghidra should be installed and a project should be created that encompasses this folder. Joern should be installed and a path to its CLI should be provided in bin_cpg_extraction.py.

Be sure to satisfy all import statements in bin_cpg_extraction.py, its related files, and train_palmtree.py.

A library of binary files is necessary to train the model.

##### Setup:

File paths/folders are all given as relative. If they are not found when the program is found, they have to be changed to an absolute path. Relevant files that use paths are:
- train_palmtree.py
- bin_cpg_extraction.py
- control_flow_gen.py
- dataflow_gen.py

The old version of control flow graph generator still exists for reference.

To run PalmTree training in /src, one has to first acquire disassembled binary files. Place a library of binary files in /src/data/input, and run bin_cpg_extraction. It should generate files in both /intermediary_files and /output.

Then, run train_palmtree, which if you have enough computer resources, should output a trained model for use in tasks like BCSD.


## Original README.md

# 🌴PalmTree

This is the official repository for 🌴PalmTree, which is a pre-train Language model for assembly. We will actively update it.
Currently supported platforms: x86

You can find pre-trained PalmTree model [here](https://drive.google.com/file/d/1yC3M-kVTFWql6hCgM_QCbKtc1PbdVdvp/view?usp=sharing)

please consider citing our paper
Xuezixiang Li, Yu Qu, and Heng Yin, "PalmTree: Learning an Assembly Language Model for Instruction Embedding", [CCS'2021]

```
@inproceedings{li2021palmtree,
  title={Palmtree: learning an assembly language model for instruction embedding},
  author={Li, Xuezixiang and Qu, Yu and Yin, Heng},
  booktitle={Proceedings of the 2021 ACM SIGSAC Conference on Computer and Communications Security},
  pages={3236--3251},
  year={2021}
}
```


## Acknowledgement:

This implementation is based on [bert-pytorch](https://github.com/codertimo/BERT-pytorch), we add our training tasks for CFGs and DFGs.

## Requirements:
- cuda >= 10.1
- pytorch >= 1.3.1
- binary ninja (optional, for dataset generation)

## Updates

### extrinsic evaluations
We released code for extrinsic evaluations.

Extrinsic evluations including:
- Gemini
- EKALVYA

### intrinsic evaluations
Intrinsic evlautions including:
- Opcode Outlier detection
- Operand Outlier detection
- Basicblock matching

### Dataset generator

dataflow_gen.py: generate dataflow dataset for PalmTree model via Binary Ninja and Binary ninja mid-level IR. 
control_flow_gen.py: generate control flow dataset for PalmTree model using Binary Ninja API.

### Dataset format
TXT files. Data-flow and control-flow graph will be sampled by random walk algorithm. And then splitted into instruction pairs.
For a given instruction sequence
```
push rbp
mov rbp, rsp
sub rsp, 0x20
```
Two lines of instruction pairs will be generated:
```
push rbp    mov rbp rsp
mov rbp rsp sub rsp 0x20
```
In detail:
```
push\<SPACE\>rbp<\t>mov\<SPACE\>rbp\<SPACE\>rsp<\n>
```
## TODO:

- Support more binary tools (Ghidra, IDA pro, etc.)
- Support Docker
