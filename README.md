# SNMP Dummy Agent
SNMP v2c Agent 예제 코드를 도커로 돌려 볼 수 있다.
* `src/mibs/MY-MIB` 파일을 참고하여 간단한 쿼리 가능

## Docker
### Build
```bash
docker build -t snmp-dummy-agent:latest .
```
### Run
```bash
docker run -it -p 11611:161/udp snmp-dummy-agent:latest
```

## Test
* __CLI__ 환경에서 테스트 하려면 `net-snmp`를 설치
* __GUI__ 환경에서 테스트 하려면 `mib-browser` 설치
   
### Walk
```bash
$ snmpwalk -v 2c -c public 127.0.0.1:11611 .1
SNMPv2-SMI::enterprises.42.1.0 = INTEGER: 0
SNMPv2-SMI::enterprises.42.2.0 = STRING: "My Description [0]"
SNMPv2-SMI::enterprises.20408.3.1.8.1.1.1.1.109.121.45.110.109.115 = Hex-STRING: 00 00 00 00 00 00
SNMPv2-SMI::enterprises.20408.3.1.8.1.1.1.1.109.121.45.110.109.115 = No more variables left in this MIB View (It is past the end of the MIB tree)
```

### Get
```bash
# MY-MIB을 `~/.snmp/mibs:/usr/local/share/snmp/mibs:/usr/share/snmp/mibs` 중 한 곳에 넣거나 위치를 지정해야 한다.

$ snmpget -m $(pwd)/src/mibs/MY-MIB -v 2c -c public 127.0.0.1:11611 MY-MIB::testCount.0
MY-MIB::testCount.0 = INTEGER: 0

$ snmpget -m $(pwd)/src/mibs/MY-MIB -v 2c -c public 127.0.0.1:11611 MY-MIB::testDescription.0
MY-MIB::testDescription.0 = STRING: "My Description [0]"
```

### Set
```bash
# 바뀌기 전의 값 확인.
$ snmp-dummy-agent git:(master) ✗ snmpget -m $(pwd)/src/mibs/MY-MIB -v 2c -c public 127.0.0.1:11611 MY-MIB::testCount.0
MY-MIB::testCount.0 = INTEGER: 0

# i(Integer) 타입으로 값 100을 저장
# Community는 write용으로 지정한 `private` 사용
$ snmpset -m $(pwd)/src/mibs/MY-MIB -v 2c -c private 127.0.0.1:11611 MY-MIB::testCount.0 i 100
MY-MIB::testCount.0 = INTEGER: 100

# 바뀐 값을 확인
$ snmp-dummy-agent git:(master) ✗ snmpget -m $(pwd)/src/mibs/MY-MIB -v 2c -c public 127.0.0.1:11611 MY-MIB::testCount.0
MY-MIB::testCount.0 = INTEGER: 100
```