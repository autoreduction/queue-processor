#!/bin/bash

if sudo -n true 2>/dev/null; then
    exit 0
else
    exit 1
fi