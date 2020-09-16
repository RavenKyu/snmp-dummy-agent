FROM python:3.7.7-alpine3.11

RUN apk add --no-cache --virtual .build-deps gcc musl-dev

RUN mkdir -p /src/snmp-dummy-agent
ADD snmp-dummy-agent/requirements.txt /src
RUN pip install -r /src/requirements.txt

# MIB 파일 복사
RUN mkdir -p /usr/share/snmp/mibs
ADD mibs /usr/share/snmp/mibs

# MIB 파일 컴파일
RUN mibdump.py --mib-source /usr/share/snmp/mibs MY-MIB

ADD snmp-dummy-agent /src/snmp-dummy-agent

WORKDIR /src/snmp-dummy-agent