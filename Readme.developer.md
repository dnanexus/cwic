# CWIC - developer documentation

Detailed information on CWIC is available in the [DNAnexus official documentation](https://documentation.dnanexus.com/developer/cloud-workstations/cwic).

The source code of the app is available at https://github.com/dnanexus/cwic and it is open source. This Readme describes how to contribute to the development of the app. You can also change the app code according to your specific needs and build your own CWIC app or applet; for more information on how to build a DNAnexus app visit [the app build process guide](https://documentation.dnanexus.com/developer/apps/app-build-process).

## App components

There are three main components in the app code base:
- [Dockerfile](https://github.com/dnanexus/cwic/blob/main/docker/Dockerfile), which defines the environment for CWIC.
- [CWIC scripts](https://github.com/dnanexus/cwic/tree/main/resources/usr/local/bin), which add functionality to CWIC such as the ability to save (snapshot) Docker container (`dx-save-cwic`) or launch the app in batch from inside an interactive CWIC session (`dx-cwic-sub`).
- [src/code.sh](https://github.com/dnanexus/cwic/blob/main/src/code.sh), the main app script that preforms input validation and invokes the `docker run` command to start the Docker container.



### Docker environment

A default CWIC Docker image contains:
- dxpy
- dxfuse
- Docker

and a few additional useful packages.

There are two ways to modify the Docker environment for CWIC:
1. by running the app and saving your changed environment with `dx-save-cwic`, which runs `docker commit` and pushes the new image to the Docker registry specified in the `credentials` app input.
2. by modifying the Dockerfile, push the Docker image to your Docker registry and then specifying your image with the `dx run` command:

```
dx run cwic -iimage=org/repo:latest
```

Alternatively, to make your image a default one and skip the need to use the `image` option, assign the `DXBASEIMG` variable in the [app script](https://github.com/dnanexus/cwic/blob/main/src/code.sh) to your image (by default it is set to `dnanexus/cwic-base`). This requires of course building the applet in and using it instead of cwic.

### CWIC scripts

Scripts are located at [/cwic/resources/usr/local/bin/](https://github.com/dnanexus/cwic/tree/main/resources/usr/local/bin). Since they are in the app's resources/ directory, they are all copied to /usr/local/bin/ in the worker's LXC container. They are kept outside of the Docker image and bind-mounted (using `docker run -v` option) into the Docker container when the app is run in order to keep the possibility to update them independently of Docker images.

### App script

