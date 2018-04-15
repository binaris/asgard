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

SLS := sudo docker run $(DOCKERARGS) -it --rm $(IMAGE)

FUNCTIONS := find-unavailable-instance-types patch-asg

DOCKER := sudo docker

.PHONY: build
build:
	$(DOCKER) build -t $(IMAGE) .

invoke-local-%:
	make invoke-$* INVOKE_ARGS=local

invoke-%: build
	$(SLS) invoke $(INVOKE_ARGS) -f $* -d $(data)

invoke-find-unavailable-instance-types: data='{ "region": "$(region)" }'

.PHONY: bash
bash: build
	$(DOCKER) run -it --rm $(DOCKERARGS) --entrypoint /bin/bash $(IMAGE)

.PHONY: deploy
deploy: build
	$(SLS) deploy

$(FUNCTIONS): %: deploy-% invoke-% invoke-local-% logs-%
.PHONY: $(FUNCTIONS)

logs-%: build
	$(SLS) logs -f $* -t

deploy-%: build
	$(SLS) deploy function -f $*

