#!/bin/bash

main() {

    echo "Value of image: '$image'"
    echo "Value of cmd: '$cmd'"
    echo "Value of credentials: '$credentials'"

    DXBASEIMG=dnanexus/cwic-base:0.0.3

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

    dx_scripts=(
        mark-section
        dx-registry-login
        dx-save-cwic
        dx-start-cwic
        dx-save-project
        dx-reload-project
        dx-cwic-sub
        dx-find-cwic-jobs
    )
    v_scripts=""
    for i in ${dx_scripts[@]}; do
        v_scripts="$v_scripts -v /usr/local/bin/$i:/usr/local/bin/$i "
    done
 
    dx_home_dnanexus=(
        dnanexus-job.json
        environment
        credentials
        job_error.json
        job_input.json
    )
    v_home_dnanexus=""
    for i in ${dx_home_dnanexus[@]}; do
        v_home_dnanexus="$v_home_dnanexus -v /home/dnanexus/$i:/home/dnanexus/$i "
    done

    # prevents confidential files from saving with docker commit
    # incl in /home/dnanexus in case HOME is accidentally set to it
    v_dont_save="
        -v /scratch:/scratch
        -v /tmp/.dummy0:/home/cwic/.dnanexus_config
        -v /tmp/.dummy1:/home/cwic/.docker
        -v /tmp/.dummy2:/home/dnanexus/.dnanexus_config
        -v /tmp/.dummy3:/home/dnanexus/.docker"

    enable_fuse="--device /dev/fuse
        --cap-add SYS_ADMIN
        --cap-add MKNOD
        --security-opt apparmor=unconfined"

    opts="--init
        $v_scripts
        $v_home_dnanexus
        $v_dont_save
        $enable_fuse
        -v /var/run/docker.sock:/var/run/docker.sock
        --entrypoint /usr/local/bin/dx-start-cwic
        --workdir /home/cwic
        -e HOME=/home/cwic
        --name cwic"

    mark-section "starting Docker container"
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
