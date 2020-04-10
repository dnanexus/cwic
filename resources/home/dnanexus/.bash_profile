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

echo; sudo dx-load-cwic
