#!/usr/bin/env bash

LIB_DIR=".../lib"
IVY_JAR=".../ivy-2.5.0-rc1.jar"

java -jar $IVY_JAR \
     -ivy dependencies.xml \
     -sync \
     -retrieve "$LIB_DIR/[artifact]-[type]-[revision].[ext]"
