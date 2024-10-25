#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

.PHONY : build debug

REGISTRY_URL 	?= registry.control23.dap.local
REGISTRY_NS	= oso

build :
	docker build \
		. -t oso-harmonzie-plugins:latest -t $(REGISTRY_URL)/$(REGISTRY_NS)/oso-harmonize-plugins:latest -f Dockerfile

debug : build
	docker build \
                . -t oso-harmonzie-plugins-dev:latest -t $(REGISTRY_URL)/$(REGISTRY_NS)/oso-harmonize-plugins-dev:latest -f Dockerfile.debug

