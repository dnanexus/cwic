# CWIC Developer Documentation

This Readme describes how to contribute to the development of CWIC. The source code of the app is available at https://github.com/dnanexus/cwic. You can also fork the code, change it according to your specific needs and build your own CWIC app or applet; for more information on how to build a DNAnexus app visit [the app build process guide](https://documentation.dnanexus.com/developer/apps/app-build-process).

Detailed information on how to use CWIC is available in the [DNAnexus official documentation](https://documentation.dnanexus.com/developer/cloud-workstations/cwic) and the Readme of the app.

## App components

There are three main components in the app code base:
- [Dockerfile](https://github.com/dnanexus/cwic/blob/main/docker/Dockerfile), which defines the Docker environment for CWIC.
- [CWIC scripts](https://github.com/dnanexus/cwic/tree/main/resources/usr/local/bin), which add functionality to CWIC such as the ability to save (snapshot) a running Docker container (`dx-save-cwic`) or launch the app in batch from inside an interactive CWIC session (`dx-cwic-sub`). It also includes the Docker entrypoint `dx-start-cwic`.
- [src/code.sh](https://github.com/dnanexus/cwic/blob/main/src/code.sh), the main app script.

### Docker environment

A default CWIC Docker image contains:
- dxpy
- dxfuse
- Docker

and a few additional useful packages.

There are two ways in which you can modify the Docker environment for CWIC:
1. by running the app and saving your changed environment with `dx-save-cwic`, which runs `docker commit` and pushes the new image to the Docker registry specified in the `credentials` app input.
2. by modifying the Dockerfile, push the Docker image to your Docker registry and then specifying your image with the `dx run` command:

```
dx run cwic -iimage=org/repo:latest
```

Alternatively, to make your image a default one and skip the need to use the `image` option, assign the `DXBASEIMG` variable in the [app script](https://github.com/dnanexus/cwic/blob/main/src/code.sh) to your image (by default it is set to `dnanexus/cwic-base`). This requires of course building the applet in you project and using it instead of cwic.

### CWIC scripts

Scripts are located at [/cwic/resources/usr/local/bin/](https://github.com/dnanexus/cwic/tree/main/resources/usr/local/bin). Since they are in the app's resources/ directory, they are all copied to /usr/local/bin/ in the App Execution Environment in which the job runs. They are kept outside of the Docker image and bind-mounted (using `docker run -v` option) into the Docker container during at runtime in order to keep the possibility to update them independently of Docker images.

The Docker container entrypoint [dx-start-cwic](https://github.com/dnanexus/cwic/blob/main/resources/usr/local/bin/dx-start-cwic) checks whether the user provided DNAnexus API token in `credentials` and uses them to log the user into the Platform. If the token is not available the job's token is used in the CWIC Docker environment. A token is needed so that the project can be mounted in CWIC, by default in a read-only mode since the write mode is experimental and under development. If the app is run in a batch, non-interactive mode (with `cmd`), the command is executed with `eval` at the end of the script.

When CWIC is started a Docker container is run in the DNAnexus Application Execution environment and the user is sshed into that container. This is done when a `dx-load-cwic` command is executed in the [.bash_profile](https://github.com/dnanexus/cwic/blob/main/resources/home/dnanexus/.bash_profile) file. This script also starts [byobu](https://www.byobu.org/), which is a terminal multiplexer based on tmux.

### App script

The main script of the app preforms input validation and invokes the `docker run` command to start the Docker container.

## CWIC dependencies

When developing CWIC is it useful to have Docker installed on your local computer in order to test building and executing the Docker image.

## Testing


