# SNMP Dummy Agent
## Docker
### Build
```bash
docker build -t snmp-dummy-agent:latest .
```
### Run
```bash
docker run -it -p 11611:161/udp snmp-dummy-agent:latest
```
