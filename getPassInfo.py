import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor

def get_relevant_files(passname):
    result = subprocess.run(
        ['git', 'grep', '-e', passname],
        stdout=subprocess.PIPE,
        text=True
    )
    files = set()
    for line in result.stdout.splitlines():
        file_path = line.split(':')[0]
        if file_path.endswith('.cpp'):
            files.add(file_path)
    return passname, list(files)

def get_unique_lines(file, pattern):
    unique_lines = set()
    with open(file, 'r') as f:
        for line in f:
            if re.search(pattern, line):
                unique_lines.add(line.strip())
    return list(unique_lines)

def main(file):
    with open(file, 'r') as f:
        // Read the passnames from the file


        passnames = [line.strip() for line in f]

    with ProcessPoolExecutor() as executor:
        results = executor.map(get_relevant_files, passnames)

    for passname, files in results:
        print(f"Relevant files for: {passname}")
        print(','.join(files))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python getPassInfo.py <file>")
        sys.exit(1)
    main(sys.argv[1])