import subprocess
import os


def get_unmounted_drives():
    command = "lsblk -o NAME,LABEL,MOUNTPOINT,FSTYPE -P"
    result = subprocess.run(command, shell=True,
                            text=True, capture_output=True)
    lines = result.stdout.strip().split("\n")

    unmounted_drives = []
    for line in lines:
        if 'MOUNTPOINT=""' in line:
            parts = line.split()
            name = [part.split("=")[1].strip('"')
                    for part in parts if part.startswith("NAME")][0]
            label = [part.split("=")[1].strip('"')
                     for part in parts if part.startswith("LABEL")][0]
            fstype = [part.split("=")[1].strip('"')
                      for part in parts if part.startswith("FSTYPE")][0]

            if fstype:  # Only consider partitions with a filesystem
                unmounted_drives.append((name, label))
    print(unmounted_drives)
    return unmounted_drives


def mount_drives(drives):
    base_mount_path = "/mnt/"
    for drive, label in drives:
        if label == 'EFI':
            continue
        mount_point = os.path.join(base_mount_path, label)
        if not os.path.exists(mount_point):
            os.makedirs(mount_point)

        mount_command = f"mount /dev/{drive} /mnt/drive"
        result = subprocess.run(mount_command, shell=True,
                                text=True, capture_output=True)
        if result.returncode == 0:
            print(f"Mounted /dev/{drive} at /mnt/drive")
        else:
            print(f"Failed to mount /dev/{drive}: {result.stderr}")


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
