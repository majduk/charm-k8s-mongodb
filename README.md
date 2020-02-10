
Juju Charm for Mon on Kubernetes
==================================

CI Badges
---------

Click on each badge for more details.

| Branch | Build Status | Coverage |
|--------|--------------|----------|
| master | [![Build Status (master)](https://travis-ci.org/majduk/charm-k8s-mongodb.svg?branch=master)](https://travis-ci.org/majduk/charm-k8s-mongodb.svg?branch=master) | [![Coverage Status](https://coveralls.io/repos/github/majduk/charm-k8s-mongodb/badge.svg?branch=master)](https://coveralls.io/github/majduk/charm-k8s-mongodb?branch=master) |


Overview
---------

Mongo for Juju CAAS

Usage
---------

To use, first pull in dependencies via `git submodule`:

```bash
git submodule init
git submodule update
```

Then, deploy the charm with an appropriate image resource:

```bash
juju --debug deploy . --resource mongodb-image=mongo:3.1 --resource mongodb-sidecar-image=mongo-sidecar:3.1
```


