import os
import sys

def download_repo(repo_url, destination_dir):
    repo_name = os.path.basename(repo_url)
    repo_dir = os.path.join(destination_dir, repo_name)
    print("Téléchargement du dépôt : " + repo_name)
    os.chdir(destination_dir)
    os.system("git clone " + repo_url)

if len(sys.argv) != 3:
    print("Usage: python script.py fichier_source destination_dir")
    sys.exit(1)

liens_github_file = sys.argv[1]
destination_dir = sys.argv[2]

with open(liens_github_file) as f:
    urls = f.read().splitlines()

for url in urls:
    if "github.com" in url:
        download_repo(url, destination_dir)
