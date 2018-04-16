ifneq ("$(wildcard ~/.aws/credentials)","")
  PROFILE = $(if $(AWS_PROFILE), --profile=$(AWS_PROFILE), )
  AWS_ACCESS_KEY_ID      ?=  $(shell aws configure get aws_access_key_id $(PROFILE))
  AWS_SECRET_ACCESS_KEY  ?=  $(shell aws configure get aws_secret_access_key $(PROFILE))
  export AWS_ACCESS_KEY_ID
  export AWS_SECRET_ACCESS_KEY
endif

IMAGE := binaris/asgard

DOCKERARGS := -e AWS_ACCESS_KEY_ID=$(AWS_ACCESS_KEY_ID) \
	-e AWS_SECRET_ACCESS_KEY=$(AWS_SECRET_ACCESS_KEY)

FUNCTIONS := find-unavailable-instance-types patch-asg exclude-subnets

DOCKER := sudo docker

SLS := $(DOCKER) run $(DOCKERARGS) -t --rm $(IMAGE)

stage ?= dev

.PHONY: build
build:
	$(DOCKER) build -t $(IMAGE) .

.PHONY: lint
lint: build
	$(DOCKER) run $(DOCKERARGS) -t --rm --entrypoint pep8 $(IMAGE) *.py

invoke-local-%: build
	$(SLS) invoke local $(INVOKE_ARGS) -f $* -p input.json $(data) -s $(stage)

invoke-%: build
	$(SLS) invoke $(INVOKE_ARGS) -f $* $(data) -s $(stage) -p input.json

invoke-find-unavailable-instance-types: data='-d { "region": "$(region)" }'

.PHONY: bash
bash: build
	$(DOCKER) run -it --rm $(DOCKERARGS) --entrypoint /bin/bash $(IMAGE)

update-functions: deploy-find-unavailable-instance-types deploy-patch-asg

.PHONY: deploy
deploy: build
	$(SLS) deploy -s $(stage)

$(FUNCTIONS): %: deploy-% invoke-% invoke-local-% logs-%
.PHONY: $(FUNCTIONS)

logs-%: build
	$(SLS) logs -f $* -t -s $(stage)

deploy-%: build
	$(SLS) deploy function -f $* -s $(stage)

remove: build
	$(SLS) remove -s $(stage)

