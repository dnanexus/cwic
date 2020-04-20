# CWIC - Cloud Workstation in Container (DNAnexus Platform App)

## What does this app do?

This app provides an interactive analysis environment for the users. The environment can be customized, saved, and used to execute commands in a non-interactive manner.

The user's environment is set up in a Docker container. It can be accessed by running the app with the **--ssh** or **--allow-ssh** flags. The changes made in the workspace, such as installing packages, adding files, configuration, etc., can be saved as a Docker image and pushed to your private Docker registry. This image can be accessed and used in subsequent app runs.

If a bash command is passed on the input, the app will run in a non-interactive batch mode and execute the command in the (most recently saved) user's Docker environment. The default DNAnexus public image ([dnanexus/cwic-base](https://hub.docker.com/r/dnanexus/cwic-base)) will be pulled and loaded if the user's registry doesn't contain a cwic image or the credentials input file is not available.

DNAnexus project in which the app is run is mounted in the environment using [dxfuse](https://github.com/dnanexus/dxfuse) and so the files in the project are accessible directly as local files in the workspace without the need of manual download and upload.  Cwic environment provides scripts for syncing up the remote project with the local mount point, e.g. the command "dx-save-project" saves the locally created files in the platform (syncing is done automatically by dxfuse every 5 minutes) and "dx-load-project" refreshes the mount so that new files added to the project by the platform are visible locally in the cwic workspace environment.

## What are typical use cases for this app?

* Use a file-based, portable, interactive analysis environment familiar to HPC users
  - Access DNAnexus files through a familiar file system interface without any extra upload or download commands
  - Configure your environment the way you like it and save it in an external, versioned container registry
  - Restart your work on the cloud, local HPC, or your laptop

* Scale out and parallelize your interactive analysis with a single command
  - A single qsub-like command lets you scale out on DNAnexus cloud infrastructure
  - Under the hood,  you launch a fleet of workers that pull the most recent docker image from the registry configured in the credential file, execute the specified command on the worker, and output the results to cloud storage


## What are the inputs?

The app takes three optional inputs:

* `image` - a Docker image name to be loaded. If it is not provided, and no credentials file with Docker registry access data is provided, a default DNAnexus image dnanexus/cwic-base will be used. If credentials to a Docker registry are supplied, it will first check if there is an image specific to the user and project available in that registry (&lt;registry&gt;/&lt;organization&gt;/dx-cwic-&lt;dnanexus-project-id&gt;\_&lt;dnanexus-user-id&gt;:latest) and use this image if available. Such images named after the project and user are created and pushed to your private registry when the command "dx-save-cwic" is run in the workspace. The provided image should contain dxfuse and docker if the work in that image will have to be saved and a mounted project will need to be accessed.

* `cmd` - A command to be run in the user's environment (Docker image). If "image" is provided, the command will be run in the container run from that image (see the description of the "image" input). The command is evaluated using a bash shell, which will expand wildcards and shell variables.

* `credentials` - a file storing an access token and user login information to a Docker registry where a Docker image representing the user's cwic instance will be stored and retrieved. It can also store an optional DNAnexus user API token that will be used to log the user into the DNAnexus platform in the cwic container.

An example of the credentials file format is:

```
{
    "docker_registry": {
        "registry": "docker.io",    # registry name, e.g. docker.io or quay.io
        "username": "myusername",   # registry login name
        "organization": "dnanexus", # optional, defaults to the value of the "username" field above
        "token": "ABC-124-DEF-456"  # API token generated on the registry website. Quay.io refers to this as 'encrypted password'
    },
    "dnanexus": {
        "token": "5137864179ABDC"   # optional, DNAnexus user's API token
    }
}
```

The app was tested with the"docker.io" and "quay.io" registries.

### Special note on credentials files

You can keep your credentials secret by storing your credential file in a separate project that only you can VIEW:

Project A: Only you, the app runner, have VIEW access or higher to this project. Store the credentials file in this project.

Project B: The shared project you want to transfer files to and from. Run the app in this project and use the credentials file from Project A as the input for the `credentials` argument.

Only those with VIEW access to Project A can see the contents of the credentials file in Project B. Note that admins in Project B can still SSH into a job running in Project B.

## What does this app output?

The app doesn't return any outputs. If files are created as a result of running the `command` they should be placed in the /project directory so that they are automatically uploaded to the project and available after the job finishes running. The command "dx-save-project" is run after the command execution to enforce the files upload to the project; in an interactive environment the user should run the command when they want to immediately upload files created in the locally mounted project to the project on the platform.

## Examples

The command below will run the cwic instance started from the DNAnexus Docker image dnanexus/cwic-base. Since no "credentials" file is provided, the changes the user makes in the cwic container environment cannot be saved in a private Docker registry:

```
$ dx run app-cwic --ssh
```

Like above, the command below will run cwic started from the DNAnexus image dnanexus/cwic-base and since "credentials" file is given when the user runs "dx-save-cwic" in the Docker container, the environment will be saved as a new Docker layer added to the image the app was started from and pushed to the Docker registry specified in "credentials":

```
$ dx run app-cwic --ssh \
    -icredentials=my_cred_project:credentials.json \
```

Like above, this command will run the cwic instance, execute the "ls -l" command, and exit:

```
$ dx run app-cwic \
    -icredentials=my_cred_project:credentials.json \
    -icmd="ls -l /project"
```

This command will run cwic and execute the "ls -l" command in the image provided:

```
$ dx run app-cwic \
    -icredentials=my_cred_project:credentials.json \
    -icmd="ls -l" \
    -iimage="mydockeruser/myimage:0.0.1"
```

