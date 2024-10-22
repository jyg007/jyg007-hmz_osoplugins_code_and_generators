.PHONY : build debug

REGISTRY_URL 	?= registry.control23.dap.local
REGISTRY_NS	= oso

build :
	docker build \
		. -t oso-harmonzie-plugins:latest -t $(REGISTRY_URL)/$(REGISTRY_NS)/oso-harmonize-plugins:latest -f Dockerfile

debug : build
	docker build \
                . -t oso-harmonzie-plugins-dev:latest -t $(REGISTRY_URL)/$(REGISTRY_NS)/oso-harmonzie-plugins-dev:latest -f Dockerfile.debug

