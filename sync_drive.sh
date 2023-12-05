#!/bin/bash

# Initialize largest partition size and name
largest_size=0
largest_partition=""

# Read each line from lsblk output
while IFS= read -r line; do
    # Extract necessary fields
    name=$(echo "$line" | cut -d ' ' -f 1)
    size=$(echo "$line" | cut -d ' ' -f 2)
    mountpoint=$(echo "$line" | cut -d ' ' -f 3)
    type=$(echo "$line" | cut -d ' ' -f 4)

    # Continue only if it's an unmounted partition
    if [[ "$type" == "part" && -z "$mountpoint" ]]; then
        # Convert size to a comparable number (bytes)
        size_bytes=$(numfmt --from=iec "$size")

        # Check if this partition is the largest found so far
        if (( size_bytes > largest_size )); then
            largest_size=$size_bytes
            largest_partition="/dev/$name"
        fi
    fi
done < <(lsblk -nr -o NAME,SIZE,MOUNTPOINT,TYPE)

# Output the largest unmounted partition
if [[ -n "$largest_partition" ]]; then
    echo "Largest unmounted partition: $largest_partition"
else
    echo "No unmounted partitions found."
fi

if [[ "$largest_partition" == *"EFI"* ]]; then
    echo "Aborting due to EFI partition."
    exit 1
fi


mounted_path=$(udisksctl mount -b $largest_partition | awk '{print $NF}')
echo $mounted_path
if [[ "$mounted_path" == *"EFI"* ]]; then
    udisksctl unmount -b $largest_partition
    echo "Aborting due to EFI partition."
    exit 1
fi
sudo mkdir $mounted_path/music
sudo rsync -rv --ignore-existing --remove-source-files /home/dev/crec/* $mounted_path/music | /home/dev/env/bin/python /home/dev/cymatic-rec/set_export.py
udisksctl unmount -b $largest_partition
echo "Sync Complete"

# If a partition is found, mount it
# if [ -n "$LARGEST_PARTITION" ]; then
#     MOUNT_POINT="/mnt/$LARGEST_PARTITION"
#     echo "Mounting /dev/$LARGEST_PARTITION at $MOUNT_POINT"
#     mkdir -p "$MOUNT_POINT"
#     mount "/dev/$LARGEST_PARTITION" "$MOUNT_POINT"
# else
#     echo "No unmounted partitions found."
# fi
