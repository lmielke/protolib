
# Feature Development Guidelines
We follow a feature driven development approach. Each feature is a standalone solution that can be implemented independently. It should be easy to integrate features into the overall software stack. Features can be of low, medium or high complexity (assembly index).
- Low: core functionality solution for a professional user, no convenience features such as I/O
- Medium: core functionality solution for a experienced user, with simple convenience features for I/O such as a simple shell interface or similar
- Moderate: extended functionality for experienced users, with a simple I/O interface (i.e. shell interface), convenience features, and documentation
- High: extended functionality for mainstream users, with a full I/O interface (i.e. web interface), error handling, and documentation

# Project background
The project generally uses Python, JavaScript and HTML/CSS to implement custom features. It praises itself for its flexible low cost solutions, by implmenting mainly open source solutions while keeping teams efficient, small and agile.


#Feature:  __''__, Assembly Index: 
Hello everybody, these are the instructions for feature __''__. 

## General Instructionns to follow while completing the feature.
A: Planning Phase
0. Read the instructions carefully and understand the feature.
1. Start analyzing the requirement. (Who?, Where?, What?, When?, How? and Why?!)
2. Ask the sponsor for clarification if needed.
3. Discuss the feature with the team focussing on responsibilities and how to best implement the feature.
4. Step by step, plan the general implementation steps and assign responsibilities.

B: Implementation Phase
1. Sort the tasks in a useful implementation order (i.e. dependencies, priority, ...).
2. Ask your relevant team member to implement the assigned sub-task.

# Description of feature 

    # UNITTEST
unittest is a feature, that should be implemented as a standalone solution. It intends to find all files in a given directory. The user should be able to limit the search using some regex like filter condition.
The files should be returned as a list of full paths.
The unittest uses the following steps:
1. Get starting path
2. loop through all files in the directory and all subdirectories
3. get files with specified file_name
