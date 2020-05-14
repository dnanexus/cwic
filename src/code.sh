#!/bin/bash

main() {

    echo "Value of image: '$image'"
    echo "Value of cmd: '$cmd'"
    echo "Value of credentials: '$credentials'"

    DXBASEIMG=dnanexus/cwic-base:0.0.2

    mark-section "checking if cwic will be run interactively or in non-interactive batch mode"

    if [ -z "$cmd" ]; then
        echo "Will start interactive Docker container"
        INTERACTIVE=1

        allow_ssh=$(jq .allowSSH /home/dnanexus/dnanexus-job.json)
        if [[ -z "$allow_ssh" || "$allow_ssh" == null ]]; then
            echo "ERROR: job not run with the ssh flag on and command is not provided."
            echo "ERROR: run it with --ssh to execute cwic interactively or pass a command string in \"cmd\" to execute the comand and exit."
            exit 1
        fi
    fi

    if [ -n "$credentials" ]; then
        mark-section "downloading credentials"
        dx download "$credentials" -o credentials
    fi

    if [ -f /home/dnanexus/credentials ] && [ "$(jq '.docker_registry' /home/dnanexus/credentials)" != null ]; then
        source /usr/local/bin/dx-registry-login
        mark-section "determining image name we will use"

        if [ -n "$image" ]; then
            if docker pull $image; then
                echo "Using Docker image name: $image"
            fi
        else
            # Check if user has a custom image in the registry; if not, use DNAnexus base image
            DXUSER=$(jq .launchedBy /home/dnanexus/dnanexus-job.json | tr -d '"')
            CUSTOM_USER_IMG=$(echo "$REGISTRY_ORGANIZATION/dx-cwic-${DX_PROJECT_CONTEXT_ID}_${DXUSER}:latest" | tr '[:upper:]' '[:lower:]')
            if [ -n "${REGISTRY}" ]; then
                CUSTOM_USER_IMG="$REGISTRY/$CUSTOM_USER_IMG"
            fi
            echo "Attempting to download user's custom Docker image $CUSTOM_USER_IMG"
            if docker pull $CUSTOM_USER_IMG; then
                image=$CUSTOM_USER_IMG
            else
                echo "$CUSTOM_USER_IMG not found, using DNAnexus base image $DXBASEIMG"
                image=$DXBASEIMG
            fi
        fi
    else
        if [ -n "$image" ]; then
            if docker pull $image; then
                echo "Using Docker image name: $image"
            fi
        else
            image=$DXBASEIMG
            if [[ $INTERACTIVE == 1 ]]; then
                echo "WARNING: Credentials to a Docker registry were not provided. You won't be able to save and push changes made in your interactive container session"
            fi
        fi
    fi

    # Create an empty scratch directory in the LXC container and
    # bind-mount it into the Docker container. Mounted directories
    # will *not* be saved in the Docker layer when "docker commit" is run.
    mkdir /scratch

    mark-section "starting Docker container"
    # * The options:
    #     -v /usr/local/bin/*:/usr/local/bin/*:ro
    #   are needed to access registry cwic scripts in the container
    # * The option:
    #     -v /var/run/docker.sock:/var/run/docker.sock
    #   is needed to access Docker deamon from the host in the container
    # * The option:
    #     -v /home/dnanexus/*:/home/dnanexus/*:ro \
    #   gives us access to input files and dx-specific variables & files
    #   and doesn not save these files with docker commit
    # * The option:
    #     -v /tmp/.dummy:/home/dnanexus/.dnanexus_config
    #   prevents /home/dnanexus/.dnanexus_config from saving with docker commit
    # * The options:
    #     --device /dev/fuse \
    #     --cap-add SYS_ADMIN \
    #     --cap-add MKNOD \
    #     --security-opt apparmor=unconfined \
    #   are needed for fuse mounting projects in the running container

    opts="--init
        -v /scratch:/scratch
        -v /usr/local/bin/mark-section:/usr/local/bin/mark-section
        -v /usr/local/bin/dx-registry-login:/usr/local/bin/dx-registry-login
        -v /usr/local/bin/dx-save-cwic:/usr/local/bin/dx-save-cwic
        -v /usr/local/bin/dx-start-cwic:/usr/local/bin/dx-start-cwic
        -v /usr/local/bin/dx-save-project:/usr/local/bin/dx-save-project
        -v /usr/local/bin/dx-find-cwic-jobs:/usr/local/bin/dx-find-cwic-jobs
        -v /usr/local/bin/dx-reload-project:/usr/local/bin/dx-reload-project
        -v /home/dnanexus/dnanexus-job.json:/home/dnanexus/dnanexus-job.json:ro
        -v /home/dnanexus/environment:/home/dnanexus/environment:ro
        -v /home/dnanexus/.docker:/home/dnanexus/.docker
        -v /tmp/.dummy:/home/dnanexus/.dnanexus_config
        -v /home/dnanexus/credentials:/home/dnanexus/credentials
        -v /var/run/docker.sock:/var/run/docker.sock
        --device /dev/fuse
        --cap-add SYS_ADMIN
        --cap-add MKNOD
        --security-opt apparmor=unconfined
        --entrypoint /usr/local/bin/dx-start-cwic
        --name cwic"

    set -x
    if [[ -n "$cmd" ]]; then
       docker run $opts $image "$cmd"
    else
       docker run -id $opts $image /bin/bash
    fi
    set +x

    if [[ $INTERACTIVE == 1 ]]; then
        # We need to print Docker container logs if the container is run in detached, interactive mode
        docker logs cwic

        echo "Cwic interactive mode loaded. Run \"dx ssh $DX_JOB_ID\" to start."

        while true; do
            sleep 600
        done
    fi
}
