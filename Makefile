#!/usr/bin/make -f

.PHONY: db
db:
	docker run --name mongodb -p 27017:27017 -d mongodb/mongodb-community-server:latest
