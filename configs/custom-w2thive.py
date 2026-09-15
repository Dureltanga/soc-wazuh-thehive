#!/var/ossec/framework/python/bin/python3
# Script d'integration Wazuh -> TheHive
# A placer dans /var/ossec/integrations/custom-w2thive.py
# Droits : chmod 750 ; proprietaire root:wazuh
import sys, json, uuid
from thehive4py.api import TheHiveApi
from thehive4py.models import Alert

alert_file = sys.argv[1]
api_key    = sys.argv[2]
hive_url   = sys.argv[3]

with open(alert_file) as f:
    alert = json.load(f)

api = TheHiveApi(hive_url, api_key)
rule  = alert.get("rule", {})
agent = alert.get("agent", {})
level = rule.get("level", 0)
desc  = rule.get("description", "Alerte Wazuh")
aname = agent.get("name", "inconnu")
aip   = agent.get("ip", "n/a")

hive_alert = Alert(
    title=f"[Wazuh] {desc}",
    tlp=2,
    tags=["wazuh", f"level:{level}", f"agent:{aname}"],
    description=f"Agent: {aname} ({aip})\nNiveau: {level}\n\n{json.dumps(alert, indent=2)}",
    type="wazuh_alert",
    source="Wazuh",
    sourceRef=str(uuid.uuid4())[0:6],
    severity=2 if level < 12 else 3,
)
api.create_alert(hive_alert)
sys.exit(0)
