#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

.PHONY : build debug test

REGISTRY ?= us.icr.io
NAMESPACE ?= dap-osc-dev
TAG ?= latest

build :
	docker build \
		. -t oso-harmonize-plugins:latest -t $(REGISTRY)/$(NAMESPACE)/oso-harmonize-plugins:$(TAG) -f Dockerfile --platform linux/s390x

debug : build
	docker build \
                . -t oso-harmonize-plugins-dev:latest -t $(REGISTRY)/$(NAMESPACE)/oso-harmonize-plugins-dev:$(TAG) -f Dockerfile.debug --platform linux/s390x

ifdef HARMONIZE_PLUGINS_TEST_RESULTS
VOL_OPTS ::= -v $(HARMONIZE_PLUGINS_TEST_RESULTS):/tests/results:rw,z
endif

test : debug
	docker run --rm \
		--workdir /tests \
		$(VOL_OPTS) \
		--platform linux/s390x \
		--entrypoint pytest \
		$(REGISTRY)/$(NAMESPACE)/oso-harmonize-plugins-dev:$(TAG) \
		-svvv
