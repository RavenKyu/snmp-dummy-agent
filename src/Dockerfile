FROM python:3.7.7-alpine3.11

# ==============================================================================
# 타임존 설정
RUN apk add tzdata && \
    cp /usr/share/zoneinfo/Asia/Seoul /etc/localtime && \
    echo "Asia/Seoul" > /etc/timezone

# ==============================================================================
# 빌드 및 의존성 파일 설치
# 빌드 의존성 설치
RUN apk add --no-cache --virtual .build-deps gcc musl-dev
# snmp-dummy-agent python 의존 모듈 설치
RUN mkdir -p /src/snmp-dummy-agent
ADD snmp-dummy-agent/requirements.txt /src
RUN pip install -r /src/requirements.txt

# ==============================================================================
# MIB 파일
# MIB 파일 복사
RUN mkdir -p /usr/share/snmp/mibs
ADD mibs /usr/share/snmp/mibs
# MIB 파일 컴파일
RUN mibdump.py --mib-source /usr/share/snmp/mibs MY-MIB

# ==============================================================================
# snmp-dummy-agent 빌드, 설치
ADD . /src
WORKDIR /src
RUN python setup.py install

# ==============================================================================
# 설치파일 정리
RUN apk del .build-deps
WORKDIR /
RUN rm -rf /src

EXPOSE 161/udp

# ==============================================================================
ENTRYPOINT ["python" , "-m", "snmp-dummy-agent"]