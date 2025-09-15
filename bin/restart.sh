#!/usr/bin/env bash
cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && source utils.sh || exit

bash stop.sh 2> /dev/null

bash start.sh

