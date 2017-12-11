#!/bin/bash
mkdir ~/rpmbuild
mkdir ~/rpmbuild/SOURCES
tar -czf ~/rpmbuild/SOURCES/autoreduce-mq.tgz ./autoreduce-mq
rpmbuild -ba ./SPECS/autoreduce-mq.spec
