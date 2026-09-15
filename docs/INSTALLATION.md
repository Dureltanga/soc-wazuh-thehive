# Installation détaillée

## 1. Les machines virtuelles (VirtualBox)

Créer 5 VM, carte réseau en **mode pont** pour chacune :

- **Wazuh-SOC** : Ubuntu Server 24.04, 8 Go RAM, 50 Go disque.
- **TheHive-SOC** : Ubuntu Server 24.04, 11 Go RAM, 50 Go disque.
- **Serveur Windows** : Windows Server 2022 (édition Desktop Experience), 4 Go RAM, 50 Go.
- **Serveur Debian** : Debian, 2 Go RAM, 20 Go.
- **Kali** : Kali Linux, 2 Go RAM.

> Piège disque Ubuntu : à l'installation, étendre le volume logique (LVM) à la taille maximale, sinon `/` n'utilise qu'une partie du disque.

## 2. Wazuh (VM Wazuh-SOC)

```bash
sudo apt update && sudo apt install -y curl
curl -sO https://packages.wazuh.com/4.14/wazuh-install.sh
sudo bash ./wazuh-install.sh -a
```

À la fin, noter le mot de passe `admin`. Récupérer l'IP : `ip a`. Ouvrir `https://IP_WAZUH`.

## 3. Agents

### Serveur Windows (PowerShell administrateur)
```powershell
Invoke-WebRequest -Uri https://packages.wazuh.com/4.x/windows/wazuh-agent-4.14.5-1.msi -OutFile $env:tmp\wazuh-agent
msiexec.exe /i $env:tmp\wazuh-agent /q WAZUH_MANAGER='IP_WAZUH' WAZUH_AGENT_NAME='Serveur-Windows'
Start-Service -Name WazuhSvc
```

### Serveur Debian
```bash
wget https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_4.14.5-1_amd64.deb
sudo WAZUH_MANAGER='IP_WAZUH' WAZUH_AGENT_NAME='Serveur-Debian' dpkg -i ./wazuh-agent_4.14.5-1_amd64.deb
sudo systemctl daemon-reload && sudo systemctl enable --now wazuh-agent
# service SSH cible + compte de test :
sudo apt install -y openssh-server iptables
sudo useradd -m victime && echo 'victime:MotDePasse!' | sudo chpasswd
```

Vérifier dans le tableau de bord Wazuh (Endpoints) que les deux agents sont **actifs**.

## 4. TheHive + Cortex (VM TheHive-SOC)

Installer Docker (dépôt officiel), puis :
```bash
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
mkdir ~/thehive-stack && cd ~/thehive-stack
# copier docker-compose.yml ici
openssl rand -hex 32            # copier le resultat dans le champ --secret du fichier
docker compose up -d
```

Patienter 2 à 4 minutes (Cassandra est lente). Vérifier : `docker compose ps` (tout doit être `healthy`/`Up`).

- TheHive : `http://IP_THEHIVE:9000` — compte par défaut `admin@thehive.local` / `secret` (à changer).
- Cortex : `http://IP_THEHIVE:9001` — initialiser la base et créer le super-admin.

Dans TheHive : activer la licence Community, créer l'organisation `SOLARIS`, un compte analyste, et un **compte de service** (type Service) dont on génère la **clé API**.

## 5. Intégration Wazuh → TheHive (VM Wazuh-SOC)

```bash
sudo apt install -y python3-pip
sudo /var/ossec/framework/python/bin/pip3 install thehive4py==1.8.1
# copier les deux fichiers d'integration :
sudo cp custom-w2thive.py /var/ossec/integrations/
sudo cp custom-w2thive     /var/ossec/integrations/
sudo chmod 750 /var/ossec/integrations/custom-w2thive*
sudo chown root:wazuh /var/ossec/integrations/custom-w2thive*
```

Ajouter le bloc `ossec-integration.xml` dans `/var/ossec/etc/ossec.conf` (remplacer `IP_THEHIVE` et `VOTRE_CLE_API_THEHIVE`), puis :
```bash
sudo systemctl restart wazuh-manager
```

## 6. Réponse automatisée (VM Wazuh-SOC)

Ajouter le bloc `ossec-active-response.xml` dans `ossec.conf`, puis :
```bash
sudo systemctl restart wazuh-manager
```

## 7. Test de bout en bout (depuis Kali)

```bash
hydra -l victime -P /usr/share/wordlists/rockyou.txt ssh://IP_DEBIAN -t 4 -V
```

Vérifier : alerte `[Wazuh]` dans TheHive, IP bannie dans `iptables` sur la Debian, événement `rule.groups:active_response` dans Wazuh.
