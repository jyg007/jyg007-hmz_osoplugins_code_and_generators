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
TAG ?= 2.2.3-ubi97

ifdef PIP_UPGRADE
PIP_COMPILE_UPGRADE := --upgrade
endif

PIP_COMPILE = CUSTOM_COMPILE_COMMAND='make pip-compile' pip-compile --quiet --strip-extras --allow-unsafe --generate-hashes $(PIP_COMPILE_UPGRADE)
requirements.constraints.txt: pyproject.toml
	$(PIP_COMPILE) \
		--build-deps-for wheel \
		--extra dependencies \
		--extra test \
		--output-file $@ $<

requirements.txt: requirements.constraints.txt pyproject.toml
	$(PIP_COMPILE) \
		--extra dependencies \
		--output-file $@ \
		--constraint $^

requirements.build.txt: requirements.constraints.txt pyproject.toml
	$(PIP_COMPILE) \
		--only-build-deps \
		--build-deps-for wheel \
		--output-file $@ \
		--constraint $^

hack/requirements.dev.txt: pyproject.toml
	$(PIP_COMPILE) \
		--extra dev \
		--output-file $@ $<

.PHONY: pip-compile
pip-compile: requirements.constraints.txt requirements.txt requirements.build.txt

.PHONY: generate
generate: pip-compile

build :
	podman build \
		. -t oso-harmonize-plugins:latest -t oso-harmonize-plugins:$(TAG) -f Dockerfile --platform linux/s390x 

debug : build
	podman build \
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
