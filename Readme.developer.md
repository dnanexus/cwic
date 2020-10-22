# CWIC Developer Documentation

This Readme describes how to contribute to the development of CWIC. The source code of the app is available at https://github.com/dnanexus/cwic. 

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
2. by creating (e.g. based on the CWIC Dockerfile) and specifying your image from a Docker registry in the `dx run` command:

```
dx run cwic -iimage=org/repo:latest
```

Alternatively, to make your image a default one and skip the need to use the `image` option, assign the `DXBASEIMG` variable in the [app script](https://github.com/dnanexus/cwic/blob/main/src/code.sh) to your image (by default it is set to `dnanexus/cwic-base`). This requires of course building the applet in you project and using it instead of cwic.

### CWIC scripts

Scripts are located at [/cwic/resources/usr/local/bin/](https://github.com/dnanexus/cwic/tree/main/resources/usr/local/bin). Since they are in the app's resources/ directory, they are all copied to /usr/local/bin/ in the App Execution Environment in which the job runs. They are kept outside of the Docker image and bind-mounted (using `docker run -v` option) into the Docker container during at runtime in order to keep the possibility to update them independently of Docker images.

The Docker container entrypoint [dx-start-cwic](https://github.com/dnanexus/cwic/blob/main/resources/usr/local/bin/dx-start-cwic) checks whether the user provided DNAnexus API token in `credentials` and uses them to log the user into the Platform. If the token is not available the job's token is used in the CWIC Docker environment. A token is needed so that the project can be mounted in CWIC, by default in a read-only mode since the write mode is experimental and under development. If the app is run in a batch, non-interactive mode (with `cmd`), the command is executed with `eval` at the end of the script.

When CWIC is started a Docker container is run in the DNAnexus Application Execution environment and the user is sshed into that container. This is done when a `dx-load-cwic` command is executed in the [.bash_profile](https://github.com/dnanexus/cwic/blob/main/resources/home/dnanexus/.bash_profile) file. This script also starts [byobu](https://www.byobu.org/), which is a terminal multiplexer based on tmux.

### App script

The main script of the app performs input validation and invokes the `docker run` command to start the Docker container.

## CWIC dependencies

When developing CWIC it is useful to have Docker installed on your local computer in order to test building and executing the Docker image.

## Development and testing

Submit a pull request when you are ready to have your code reviewed. Always write tests for any new code you add and update tests for any code you modify. Integration and unit tests are stored in the /test/ directory of the app. Integration tests build a temporary applet and run it with different input parameters in a  project that can be specified by setting the `DX_CWIC_PROJECT_ID` environment variable (if the variable is not set, a private DNAnexus project for CWIC tests is used). To run the tests execute:

```
dx login
export DX_CWIC_PROJECT_ID=project-xxxx
python3 test/test_cwic.py
```

## Creating a custom CWIC applet

You can fork the code, update it and change it according to your specific needs, and build your own CWIC applet in a selected project. To do it, login to the Platform, select the project and execute in the root directory of CWIC:

```
dx build
```

Then you can run your applet with:

```
dx run my-cwic-app --ssh
```

For more information on how to build a DNAnexus applications visit [the app build process guide](https://documentation.dnanexus.com/developer/apps/app-build-process).

To update the Docker image, run from the CWIC root directory:

```
docker build -t org/repo:latest docker/
```

and push it to your Docker registry:

```
docker push org/repo:latest
```

## More information

Detailed information on how to use CWIC is available in the [official DNAnexus documentation](https://documentation.dnanexus.com/developer/cloud-workstations/cwic).
