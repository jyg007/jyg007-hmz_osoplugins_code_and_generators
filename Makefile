REGISTRY_URL 	?= us.icr.io
REGISTRY_NS	= dap-osc-dev

sidecars	:= frontend_sidecar backend_sidecar
run_sidecars	:= $(addprefix run-,$(sidecars))
test_sidecars	:= $(addprefix test-,$(sidecars))

$(sidecars):
	docker build \
		--build-arg BUILD_TIME_SECRET=$(BUILD_TIME_SECRET) \
		--build-arg OLD_BUILD_TIME_SECRET=$(OLD_BUILD_TIME_SECRET) \
		--build-context common-src=src/common \
		src/$@ -t $@:latest -t $(REGISTRY_URL)/$(REGISTRY_NS)/$@:latest -f Dockerfile
	if [ -n '$(DEBUG)' ]; then \
		docker build \
			--build-arg COMPONENT=$@ \
			src/$@ -t $@-dev:latest -t $(REGISTRY_URL)/$(REGISTRY_NS)/$@-dev:latest -f Dockerfile.debug; \
	fi

$(run_sidecars):
	DEBUG=1 $(MAKE) $(@:run-%=%)
	docker run --rm --entrypoint /bin/bash -it $(REGISTRY_URL)/$(REGISTRY_NS)/$(@:run-%=%)-dev:latest -- $(RUN_ARGS)

$(test_sidecars):
	DEBUG=1 RUN_ARGS=/app-root/run-unit-tests.sh $(MAKE) run-$(@:test-%=%)
