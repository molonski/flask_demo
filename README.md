Welcome to Chris' Flask Demo
============================

This is a flask web app that makes use of a redis task queue and
jQueries' AJAX function to fulfill asynchronous tasks. It was designed
as the production test portal for a digital musical instrument company.
The site serves two purposes. It can generate a standard report on
batches of test data in order to assess production efficiency, and it
guides technicians through the procedure of running individual 
instrument tests.

### Installation

You can launch and review this project using Docker. First clone this repo:

`git clone https://github.com/molonski/flask_demo.git`

navigate into the project folder:

`cd flask_demo`

Then run either the development environment or the production environment.


### Development Environment

To review the web app using the flask development web server run 
the following command in the flask_demo directory:

`docker-compose up --build`

The development version uses four Docker containers, one for each
of the following: the python app, the postgres database, the redis
task queue, and the redis queue (rq) worker.

When docker containers are running you can view the app in a web 
browser at the follwing url: [http://localhost:5000/](http://localhost:5000/)

Use this command to halt the app:

`docker-compose down -v`



### Production Environment

The production environment includes a fifth docker container for 
an Nginx webserver, which unlike the flask development server, 
can handle a large volume of simultaneous requests. To start the 
production version run the following command:

`docker-compose -f docker-compose.prod.yml up --build`

The production container will take a longer to build, and it
can be viewed at this url: [http://localhost:1337/](http://localhost:1337/)

Use this command to halt the app:

`docker-compose -f docker-compose.prod.yml down -v`