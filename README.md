## Installation and Setup

### Building the Docker Containers

This step will build the necessary Docker containers as defined in your `docker-compose.yml` file.

```bash
docker-compose build
```

### Running the Containers

This command starts up all the services defined in your `docker-compose.yml` file. It will also start the web app.

```bash
docker-compose up
```

(Include any additional steps or commands that might be necessary for your specific application.)

## Accessing the Application

### Local Development

- Access the web app locally at `http://localhost:5001`

### Production

- The app is hosted on AWS and can be accessed at `http://51.20.254.179:5001`
