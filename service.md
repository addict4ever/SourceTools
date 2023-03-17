Ce code permet de lister les services Windows installés sur un ordinateur 
en affichant différentes informations 
telles que leur nom, leur description, leur statut et leur type de démarrage.
Il utilise l'API Windows de gestion de la base de registre pour parcourir la 
clé de registre "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services" et lire 
les informations des sous-clés correspondant à chaque service.
La couleur est utilisée pour afficher le statut, 
le type de démarrage et le nom des services. 
Le jaune est utilisé pour le nom, 
le violet pour la description, 
le rouge pour le statut et le vert pour le type de démarrage.
