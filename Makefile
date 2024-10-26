.PHONY: build

download:
	# Download models and binaries
	src/scripts/install_ffmpeg.sh && \
	src/scripts/install_retalking.sh && \
	python ./src/scripts/download_models.py && \
	source .venv/bin/activate && \
	pip install pydub -t ./src/layers/pydub/python/lib/python3.12/site-packages/ && \
	pip install ffmpeg -t ./src/layers/ffmpeg/python/lib/python3.12/site-packages/ && \
	pip install requests -t ./src/layers/requests/python/lib/python3.12/site-packages/


bootstrap:
	# Bootstrap cdk
	cd ./src && \
	cdk bootstrap

build:
	# Build container
	cd ./src/retalking && \
	docker build -f Dockerfile.retalking -t retalking:1.0 .

synth:
	# Synthesize  CDK
	source .venv/bin/activate && \
	cd src && \
	cdk synth

deploy:
	# Deploy CDK
	source .venv/bin/activate && \
	cd src && \
	cdk deploy --require-approval=never SageMakerSupportingInfraStack && \
	python scripts/upload_models.py && \
	python scripts/upload_retalking_image.py && \
	cdk deploy --require-approval=never SageMakerEndpointsStack && \
	cdk deploy --require-approval=never VisualDubbingLipsyncCdkStack

destroy:
	# Destroy CDK
	source .venv/bin/activate && \
	cd src && \
	cdk destroy --all
