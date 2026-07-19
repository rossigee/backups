VERSION=2.9.1

test:
	docker build . -t rossigee/backups:test && \
	docker push rossigee/backups:test

dockerhub:
	docker build . -t rossigee/backups:${VERSION} && \
	docker push rossigee/backups:${VERSION}

deb:
	dpkg-buildpackage -us -uc -b

