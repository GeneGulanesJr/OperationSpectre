#!/bin/bash
JAVA_OPTS="-Xmx2g -Djava.awt.headless=true"
if [ "$1" = "--headless" ]; then
    shift
    exec java $JAVA_OPTS -jar /opt/burpsuite/burpsuite_community.jar "$@"
else
    exec java -jar /opt/burpsuite/burpsuite_community.jar "$@"
fi