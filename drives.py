import subprocess


def get_disk_space():
    try:
        # Define the command
        command = "df -h ~/crec/ | awk 'NR==2 {print $2, $3, $4}'"

        # Run the command
        result = subprocess.check_output(command, shell=True, text=True)

        # Strip the newline character at the end and return
        disk_space = list(
            map(float, result.strip().replace('G', '').split(' ')))
        return {
            'total': disk_space[0],
            'used': disk_space[1],
            'free': disk_space[2],
            'percent_full': round(((disk_space[0]-disk_space[2]) / disk_space[0])*100, 2)
        }
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        return None
