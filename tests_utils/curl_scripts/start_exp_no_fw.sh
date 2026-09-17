#! /bin/bash -x

# start an experiment (id 123, user named test), without firmware, (using default idle firmware)


curl -X POST http://localhost:8080/exp/start/123/test; echo
