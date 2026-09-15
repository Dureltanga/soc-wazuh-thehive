# SOC maison : Wazuh + TheHive + Cortex + réponse automatisée

Laboratoire d'un centre opérationnel de sécurité (SOC) monté de bout en bout, dans le cadre d'un projet de fin d'année en cybersécurité (cas d'étude d'une entreprise fictive SOLARIS).

La chaîne complète est démontrée : **détecter → organiser → enrichir → répondre.**

- **Wazuh** (SIEM) détecte les attaques sur des agents Windows et Linux.
- **TheHive** transforme chaque alerte critique en incident traçable.
- **Cortex** enrichit l'analyse (réputation d'IP, de fichiers…).
- **La réponse active de Wazuh** bannit automatiquement l'attaquant.

> Ce dépôt contient la **documentation et les fichiers de configuration** pour reconstruire le SOC. Il ne contient pas les machines virtuelles (trop volumineuses et contenant des secrets). En suivant ce guide, on rebâtit le laboratoire à l'identique.

## Architecture

| Machine | Rôle | Système | Ressources |
|---|---|---|---|
| Wazuh-SOC | SIEM (manager + indexeur + tableau de bord) | Ubuntu Server 24.04 | 8 vCPU, 8 Go RAM |
| TheHive-SOC | Gestion d'incidents + analyse (stack Docker) | Ubuntu Server 24.04 | 4 vCPU, 11 Go RAM |
| Serveur Windows | Machine surveillée (agent) | Windows Server 2022 | 2 vCPU, 4 Go RAM |
| Serveur Debian | Machine surveillée (agent, cible SSH) | Debian | 2 vCPU, 2 Go RAM |
| Kali | Machine d'attaque | Kali Linux | 2 vCPU, 2 Go RAM |

Toutes les machines sont sous VirtualBox, cartes réseau en mode pont.

## Prérequis

- VirtualBox
- Les images d'installation : Ubuntu Server 24.04, Debian, Kali Linux, Windows Server 2022 (évaluation)
- Une bonne dose de RAM sur l'hôte (16 Go minimum, 32 Go recommandé)

## Installation rapide

1. **Wazuh (SIEM)** — sur la VM Wazuh-SOC :
   ```bash
   curl -sO https://packages.wazuh.com/4.14/wazuh-install.sh
   sudo bash ./wazuh-install.sh -a
   ```
   Tableau de bord : `https://IP_WAZUH` (identifiants affichés en fin d'installation).

2. **Agents** — installer l'agent Wazuh sur le serveur Windows (MSI) et sur Debian (DEB), en pointant vers `IP_WAZUH`. Détails dans `docs/INSTALLATION.md`.

3. **TheHive + Cortex** — sur la VM TheHive-SOC :
   ```bash
   sudo sysctl -w vm.max_map_count=262144
   mkdir ~/thehive-stack && cd ~/thehive-stack
   # copier docker-compose.yml ici, puis remplacer le secret :
   # openssl rand -hex 32   -> coller dans le champ --secret
   docker compose up -d
   ```
   TheHive : `http://IP_THEHIVE:9000` — Cortex : `http://IP_THEHIVE:9001`

4. **Intégration Wazuh → TheHive** — ajouter le bloc `configs/ossec-integration.xml` dans `/var/ossec/etc/ossec.conf`, déposer `configs/custom-w2thive.py` et `configs/custom-w2thive` dans `/var/ossec/integrations/`, puis :
   ```bash
   sudo systemctl restart wazuh-manager
   ```

5. **Réponse automatisée** — ajouter le bloc `configs/ossec-active-response.xml` dans `ossec.conf`, puis redémarrer le manager. Sur la Debian : `sudo apt install -y iptables`.

## Tester

Depuis Kali, lancer une force brute SSH sur la Debian :
```bash
hydra -l victime -P /usr/share/wordlists/rockyou.txt ssh://IP_DEBIAN -t 4 -V
```
Résultats attendus :
- une alerte apparaît dans TheHive (onglet Alerts, préfixe `[Wazuh]`) ;
- l'IP de Kali est bannie dans le pare-feu de la Debian (`sudo iptables -L -n`) ;
- l'événement de réponse active est visible dans Wazuh (`rule.groups:active_response`).

## Documentation

- `docs/INSTALLATION.md` — installation détaillée, étape par étape.
- `docs/DEPANNAGE.md` — les difficultés rencontrées et leurs solutions.
- `configs/` — tous les fichiers de configuration.
- `screenshots/` — captures d'écran du SOC en fonctionnement.

## Sécurité

Tous les secrets de ce dépôt sont des **placeholders** (`VOTRE_CLE_API_THEHIVE`, `REMPLACER_PAR_UN_SECRET_64_CARACTERES`, etc.). Ne jamais committer de vraie clé, de vrai mot de passe ni de machine virtuelle.

## Auteur

Durel Tanga - projet de fin d'année, Mastère Cybersécurité, Systèmes & Réseaux.
