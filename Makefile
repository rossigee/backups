VERSION=2.7.0

test:
	docker build . -t rossigee/backups:test && \
	docker push rossigee/backups:test

dockerhub:
	docker build . -t rossigee/backups:${VERSION} && \
	docker push rossigee/backups:${VERSION}

deb:
	rm -rf deb_dist
	python3 setup.py --command-packages=stdeb.command bdist_deb

