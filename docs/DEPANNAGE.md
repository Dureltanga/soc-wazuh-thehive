# Dépannage : difficultés rencontrées et solutions

Problèmes réellement rencontrés lors du montage, avec leur solution. Cette liste fait gagner beaucoup de temps à qui refait le laboratoire.

## Installation Ubuntu

**Le disque paraît trop petit après installation.**
Cause : le volume logique LVM n'utilise qu'une partie du disque par défaut.
Solution : à l'écran de partitionnement, éditer `ubuntu-lv` et fixer la taille au maximum disponible.

## TheHive / Docker

**TheHive ne démarre pas, les conteneurs redémarrent en boucle.**
Cause la plus fréquente : mémoire insuffisante.
Solution : porter la VM à 11 Go de RAM ; garder `MAX_HEAP_SIZE=512M` pour Cassandra.

**Elasticsearch s'arrête juste après le démarrage.**
Causes : permissions du volume de données et paramètre noyau trop bas.
Solution : utiliser des volumes gérés par Docker (déjà le cas dans le `docker-compose.yml`) et exécuter :
```bash
sudo sysctl -w vm.max_map_count=262144
```

**Les conteneurs démarrent dans le désordre.**
Cause : TheHive démarre avant que Cassandra/Elasticsearch soient prêts.
Solution : les `healthcheck` et `depends_on: condition: service_healthy` du `docker-compose.yml` règlent ça. Démarrer d'abord les bases si besoin :
```bash
docker compose up -d cassandra elasticsearch
# attendre "healthy" via : docker compose ps
docker compose up -d thehive cortex
```

**TheHive refuse de démarrer : "application secret is too short".**
Cause : le secret HS256 doit faire au moins 256 bits.
Solution : générer un secret de 64 caractères et le mettre dans le champ `--secret` :
```bash
openssl rand -hex 32
```

**Erreur 500 dans TheHive après changement de mot de passe.**
Cause : le compte interne `kibanaserver`/comptes de service désynchronisés.
Solution : régénérer tous les mots de passe internes avec l'outil Wazuh puis redémarrer les services (voir l'outil `wazuh-passwords-tool.sh`).

**Démarrage lent après un reboot.**
Bonne pratique : arrêter proprement la stack avant d'éteindre la VM :
```bash
cd ~/thehive-stack && docker compose down
sudo shutdown now
```

## Agents Wazuh

**Un agent apparaît déconnecté après un changement de réseau.**
Cause : adressage dynamique, l'IP du manager a changé.
Solution : corriger `<address>` dans la config de l'agent, puis redémarrer son service.
- Windows : `C:\Program Files (x86)\ossec-agent\ossec.conf` puis `Restart-Service WazuhSvc`
- Debian : `/var/ossec/etc/ossec.conf` puis `sudo systemctl restart wazuh-agent`

## Réponse active

**Le bannissement ne se fait pas.**
Cause fréquente : `iptables` absent sur la machine cible (Debian récente).
Solution : `sudo apt install -y iptables`. Vérifier ensuite pendant une attaque :
```bash
sudo watch -n 2 iptables -L -n   # l'IP de l'attaquant doit apparaître en DROP
```

## Attaques

**La force brute RDP échoue toujours ("freerdp: connection failed").**
Cause : le module RDP d'Hydra est expérimental et le service est souvent filtré.
Solution : privilégier la détection SSH (Debian) et les échecs de connexion Windows, plus fiables pour la démonstration.

**Le brute force SSH est coupé au bout de quelques essais ("Connection reset by peer").**
Cause : le serveur SSH limite les connexions simultanées.
Solution : ralentir Hydra :
```bash
hydra -l victime -P rockyou.txt ssh://IP_DEBIAN -t 1 -W 1 -V
```
