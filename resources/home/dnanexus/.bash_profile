source ~/environment
source ~/.bashrc

if [[ -z $BYOBU_BACKEND ]]; then
    if [[ -f /run/shm/dx_job_monitor_started ]]; then
        byobu
    else
        touch /run/shm/dx_job_monitor_started
        byobu new-session -n "${DX_JOB_ID:-unknown_dx_job}" "tail -n +1 -f -q dx_stdout dx_stderr" \; new-window -n DNAnexus 'bash --login'
    fi
else
    /etc/update-motd.d/dx-motd
fi

eval "$(register-python-argcomplete dx|sed 's/-o default//')"

if ! grep -q "sudo dx-load-cwic" ~/.bashrc; then
    # Adding a call to run the CWIC loading script to ~/.bashrc so that CWIC
    # is loaded when a new byobu (tmux) window is opened, e.g. with ctrl a c.
    # A check is made if we are in a tmux session otherwise "source ~/.bashrc" 
    # at the top of this script (~/.bash_profile) will attach the CWIC docker
    # container and prevent loading byobu.
    echo 'if { [ "$TERM" = "screen" ] && [ -n "$TMUX" ]; } then sudo dx-load-cwic; fi' >> ~/.bashrc
    sudo dx-load-cwic
fi
