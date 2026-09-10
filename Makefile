#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#

.PHONY : build 

TAG ?= 2.4.4.3-ubi98

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

.PHONY: pip-compile
pip-compile: requirements.constraints.txt requirements.txt requirements.build.txt

.PHONY: generate
generate: pip-compile

build :
	podman build \
		. -t oso-harmonize-plugins:$(TAG) -f Dockerfile --platform linux/s390x 

