"""
Helper util to get the relevant file name from a repo based on the search pattern in a log file
Args:
    file (str): Path to the file containing the passnames

Returns:
    dumps the relevant files for each passname in the file

Example usage:
    python getPassInfo.py passnames.txt pattern repo_path1 repo_path2 ...
To get the relevant filenames in MLIR repo for the (unique) passes in a log file
"""
import re
import pandas as pd
import sys
import subprocess
from concurrent.futures import ProcessPoolExecutor
import os

def get_repo_name(repo_path):
    result = subprocess.run(
        ['git', '-C', repo_path, 'remote', '-v'],
        stdout=subprocess.PIPE,
        text=True
    )
    if result.stdout:
        remote_url = result.stdout.split()[1]
        repo_name = os.path.basename(remote_url).replace('.git', '')
        return repo_name
    return os.path.basename(repo_path)

def get_relevant_files(args):
    passname, repo_paths = args
    cpp_files = set()
    h_files = set()
    mlir_files = set()
    td_files = set()
    other_files = set()

    for repo_path in repo_paths:
        repo_name = get_repo_name(repo_path)
        result = subprocess.run(
            ['git', '-C', repo_path, 'grep', '-e', passname],
            stdout=subprocess.PIPE,
            text=True
        )
        for line in result.stdout.splitlines():
            file_path = line.split(':')[0]
            prefixed_file_path = f"{repo_name}::{file_path}"
            if prefixed_file_path.endswith('.cpp'):
                cpp_files.add(prefixed_file_path)
            elif prefixed_file_path.endswith('.h'):
                h_files.add(prefixed_file_path)
            elif prefixed_file_path.endswith('.mlir'):
                mlir_files.add(prefixed_file_path)
            elif prefixed_file_path.endswith('.td'):
                td_files.add(prefixed_file_path)
            else:
                other_files.add(prefixed_file_path)

    return passname, list(cpp_files), list(h_files), list(mlir_files), list(td_files), list(other_files)

def extract_passnames(filename, pattern):
    passnames = []
    with open(filename, 'r') as file:
        for line in file:
            match = re.search(rf'// -----// {pattern} (.+?) \((.+?)\) //----- //', line)
            if match:
                passnames.append((match.group(1), match.group(2)))
    return passnames

def create_dataframe(passnames):
    df = pd.DataFrame(passnames, columns=['passname', 'mlir-passname'])
    return df

def main(filename, pattern, repo_paths):
    passnames = extract_passnames(filename, pattern)
    df = create_dataframe(passnames)

    try:
        with ProcessPoolExecutor() as executor:
            results = list(executor.map(get_relevant_files, [(p[1], repo_paths) for p in set(passnames)]))
    finally:
        pass

    cpp_files_dict = {passname: '\n'.join(cpp_files) for passname, cpp_files, _, _, _, _ in results}
    h_files_dict = {passname: '\n'.join(h_files) for passname, _, h_files, _, _, _ in results}
    mlir_files_dict = {passname: '\n'.join(mlir_files) for passname, _, _, mlir_files, _, _ in results}
    td_files_dict = {passname: '\n'.join(td_files) for passname, _, _, _, td_files, _ in results}
    other_files_dict = {passname: '\n'.join(other_files) for passname, _, _, _, _, other_files in results}

    df['cpp_files'] = df['mlir-passname'].map(cpp_files_dict)
    df['h_files'] = df['mlir-passname'].map(h_files_dict)
    df['mlir_files'] = df['mlir-passname'].map(mlir_files_dict)
    df['td_files'] = df['mlir-passname'].map(td_files_dict)
    df['other_files'] = df['mlir-passname'].map(other_files_dict)

    base_name = os.path.splitext(os.path.basename(filename))[0]
    output_file = f'{base_name}.xlsx'
    df.to_excel(output_file, index=False)
    print(f"DataFrame has been written to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python getPassInfo.py <filename> <pattern> <repo_path1> <repo_path2> ...")
        sys.exit(1)
    filename = sys.argv[1]
    pattern = sys.argv[2]
    repo_paths = sys.argv[3:]
    main(filename, pattern, repo_paths)
