VERSION=2.5.0

test:
	docker build . -t rossigee/backups:test && \
	docker push rossigee/backups:test

dockerhub:
	docker build . -t rossigee/backups:${VERSION} && \
	docker push rossigee/backups:${VERSION}

