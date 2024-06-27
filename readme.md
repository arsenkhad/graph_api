# GraphAPI

**GraphAPI** is an API for working with graphs, stored in DOT and aDOT[^1] format.

This API was created to be used as part of university project. This means this project won't be heavily maintained and will probably stay in in it's current state. Given project will use only a few of requests, provided by this API, so most of it might contain serious bugs and flaws. Please, do not consider using this app in production, it was created for learning purposes only.

## Description

This app is made on FastAPI framework. It was written for specific use case, where graphs represent projects and nodes represent project stages. Project and node information is stored in database, and DOT files contain information on graph edges.

Graphs are interacted with via custom `Graph` and `Vertex` classes, which also were created as part of university project. They implement custom parsing from/to `.gv` files. It can lead to some possible bugs and problems with existing DOT files.

## Getting started

App can be run as it is or as docker image, but either way there must be created several enviroment variables. Here is an example of `.env` file with required variables:
```
SQLALCHEMY_DATABASE_URL=postgresql://postgres:password@host/database
SECRET_KEY=very_secure_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
SAVE_DIRECTORY=/graphs/
```

For Docker you can create `.env` file in root of this project and pass it to `docker run` with option `--env-file` as in example below.

Docker also requires binding directory for graph files in your image (`/graphs` by default. Check Dockerfile to change it.) with directory on your server, so graph files wouldn't be deleted between sessions. It can be achieved with `-v` option.

### Example of Docker image build and run 
```
docker build --tag=graph_api .
docker run -p 80:80 -v $(pwd)/graphs:/graphs --env-file .env graph_api
```

### API Requests
To get a full list of possible API requests in your browser go to `/docs` page of running app[^2].

## To be implemented
- `docker-compose.yml` file for easier setup and use of secrets instead of some eviroment variables.
- **User creation.** Currently API works with existing users only.

[^1]: **aDOT**, i.e. advanced DOT, is a DOT modification. Created in Bauman University for computation graphs and other scientific usages.
[^2]: **Standart FastAPI feature**. For more information check [this page](https://fastapi.tiangolo.com/features/#automatic-docs).
