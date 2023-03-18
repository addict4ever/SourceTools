import re
import sys

# Vérifier que les arguments sont bien passés en entrée
if len(sys.argv) != 3:
    print("Usage: python extract_github_links.py <source_file> <destination_file>")
    sys.exit(1)

# Récupérer les noms de fichiers source et destination à partir des arguments
source_file = sys.argv[1]
destination_file = sys.argv[2]

# Lire le contenu du fichier source
with open(source_file) as f:
    content = f.read()

# Trouver tous les liens https dans le contenu du fichier
github_links = re.findall('https?://github.com/[\w-]+/[\w-]+(?:/[\w-]+)*', content)

# Écrire les liens GitHub dans le fichier destination
with open(destination_file, "w") as f:
    for link in github_links:
        f.write(link + "\n")
