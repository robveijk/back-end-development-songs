#!/usr/bin/make -f

.PHONY: db
db:
	docker run --name mongodb -p 27017:27017 -d mongodb/mongodb-community-server:latest

.PHONY: flask
flask:
	MONGODB_SERVICE=localhost flask --app app run --debugger --reload
	# MONGODB_SERVICE=localhost MONGODB_USERNAME=root MONGODB_PASSWORD=password flask --app app run --debugger --reload