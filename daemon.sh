#!/bin/bash
# Run the email categorizer as a daemon process

# Navigate to script directory
cd "$(dirname "$0")"

# Function to check if the process is already running
is_running() {
    pgrep -f "python3 email_categorizer.py" > /dev/null
    return $?
}

# Start the daemon
start_daemon() {
    if is_running; then
        echo "Email categorizer is already running"
    else
        echo "Starting email categorizer daemon..."
        nohup python3 email_categorizer.py > /dev/null 2>&1 &
        echo "Daemon started with PID $!"
    fi
}

# Stop the daemon
stop_daemon() {
    if is_running; then
        echo "Stopping email categorizer daemon..."
        pkill -f "python3 email_categorizer.py"
        echo "Daemon stopped"
    else
        echo "Email categorizer is not running"
    fi
}

# Check daemon status
status_daemon() {
    if is_running; then
        echo "Email categorizer is running"
    else
        echo "Email categorizer is not running"
    fi
}

# Process command line arguments
case "$1" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        stop_daemon
        sleep 2
        start_daemon
        ;;
    status)
        status_daemon
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
