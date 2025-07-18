#  ThreatQueryX - Multi-Platform Threat Hunting Query Builder
A cross-platform desktop GUI tool that helps security analysts build and customize threat hunting queries for platforms like:
- AQL (QRadar)
- Elasticsearch
- Microsoft Defender

The tool loads pre-defined YAML templates and allows you to select parameters such as IPs, ports, and time ranges—building valid queries dynamically without writing syntax by hand.

##  Features
-  Template-based Query Generation (via YAML files).
-  Dynamic Field Loading based on platform.
-  Time Range Selection & Navigation.
-  Platform-specific output (AQL, KQL, Elastic DSL).
-  Validation of input fields (e.g., IPs, integers).

## File structure
```
.
├── docs
│   ├── document.pdf
│   ├── document.tex
│   └── stix.png
├── pictures
│   ├── app.png
│   └── failed_logins_gui.png
├── README.md
├── requirements.txt
├── src
│   ├── cli.py
│   ├── gui.py
│   ├── __init__.py
│   └── main.py
├── templates
│   ├── defender.yaml
│   ├── elastic.yaml
│   └── qradar.yaml
└── utils
    ├── configuration.py
    └── generate_queries.py
```

## Requirements
- Python >= 3.0.
- External dependencies as listed in `requirements.txt`.

## Template Format (YAML)
```yaml
failed_logins:
  description: "Search for authentication failures with optional filters."
  base: "SELECT * FROM events"
  required_fields:
    - "logsourcename(logsourceid) ILIKE 'Windows%'"
    - "qidname(qid) = 'Authentication Failure'"
  optional_fields:
    username:
      pattern: "username = '{value}'"
      help: "The username to filter on (e.g., admin)"
    source_ip:
      pattern: "sourceip = '{value}'"
      help: "sourceip address of the login attempt"
      validation: "ip"
```

Each template (e.g., `failed_logins`) defines the structure of a query, where `base` represents the foundational query logic. The `required_fields` specify mandatory parameters necessary to construct an effective query and are typically determined by the implementer during the template design phase. The `optional_fields` section allows the template to support additional user-defined input to customize the search. 

Each `optional_fields` must include a `pattern` (used for input validation) and a `help` text, which provides guidance on the field's purpose. This is particularly useful in CLI mode or automated workflows. For Defender queries, an optional `post_pipeline` allows you to toggle between raw event searches and structured, aggregated results (e.g., counts grouped by relevant fields). 

Finally, the `validation` block, defines the backend checks to ensure the provided input adheres to expected formats or values. For more practical examples, see the `Usage` section. 

### Adding New Templates
To add a new template, simply append a new entry string using the same structure to the appropriate YAML file (e.g., templates/elastic.yaml). No code changes are required

##  Pending Features
- Add integration with a yamlbuilder to automate threat-hunting templates using ML/AI on a local setup.
- Save custom query profiles based on current threat-landscape that can be easily translated into queries.

##  Usage

### GUI:
```python3
python3 src.main
```

```bash
  _   _                    _                                   
 | |_| |__  _ __ ___  __ _| |_ __ _ _   _  ___ _ __ _   ___  __
 | __| '_ \| '__/ _ \/ _` | __/ _` | | | |/ _ \ '__| | | \ \/ /
 | |_| | | | | |  __/ (_| | || (_| | |_| |  __/ |  | |_| |>  < 
  \__|_| |_|_|  \___|\__,_|\__\__, |\__,_|\___|_|   \__, /_/\_\
                                 |_|                |___/      

Welcome to the application! 
Enjoy using the app, and feel free to share any feature requests or feedback!
Version 1.0.0 olofmagn

? Choose interface mode: (Use arrow keys)
   CLI (terminal)
 » GUI (graphical)
   Quit

```

<img src="pictures/app.png" alt="app gui" width="400"/>

Example of autogenerated query using the template `failed_logins` for the platform `qradar`:

<img src="pictures/failed_logins_gui.png" alt="app gui" width="400"/>

### CLI:

```python3
python3 -m src.main
```

```bash
  _   _                    _                                   
 | |_| |__  _ __ ___  __ _| |_ __ _ _   _  ___ _ __ _   ___  __
 | __| '_ \| '__/ _ \/ _` | __/ _` | | | |/ _ \ '__| | | \ \/ /
 | |_| | | | | |  __/ (_| | || (_| | |_| |  __/ |  | |_| |>  < 
  \__|_| |_|_|  \___|\__,_|\__\__, |\__,_|\___|_|   \__, /_/\_\
                                 |_|                |___/      

Welcome to the application! 
Enjoy using the app, and feel free to share any feature requests or feedback!
Version 1.0.0 olofmagn

? Choose interface mode: (Use arrow keys)
 » CLI (terminal)
   GUI (graphical)
   Quit

? Choose a platform to use: (Use arrow keys)
   defender - Microsoft Defender for Endpoint
   elastic - Elastic SIEM
 » qradar - IBM QRadar
   Quit

Choose a template to use: (Use arrow keys)
 » failed_logins - Search for authentication failures with optional filters.
   firewall_block - Detect firewall blocks by protocol and port.
   rce_attempts - Detect potential remote command execution attempts in logs.
   powershell_execution - Find suspicious PowerShell execution events.
   rdp_loopback_traffic - Detect RDP (port 3389) traffic involving loopback addresses (127.0.0.0/8) using Event ID 5156.
   builtin_account_enabled - Detect when built-in accounts like Guest, DefaultAccount, or Administrator are enabled.

? Choose interface mode: CLI (terminal)
? Choose a platform to use: qradar - IBM QRadar
? Choose a template to use: failed_logins - Search for authentication failures with optional filters.

Search for authentication failures with optional filters.

username (The username to filter on (e.g., admin)): admin
source_ip (sourceip address of the login attempt): 127.0.0.1
Time range (default '10 MINUTES'): 30 minutes

Generated Query:

SELECT * FROM events WHERE logsourcename(logsourceid) ILIKE 'Windows%' AND qidname(qid) = 'Authentication Failure' AND username = 'admin' AND sourceip = '127.0.0.1' LAST 30 MINUTES
```

##  License
This project is open-source and licensed under the MIT License. See the LICENSE file for details.
