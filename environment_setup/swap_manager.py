#!/usr/bin/python3

import os
import sys
import shutil
import subprocess

# Configurable variables
SPARE_THRESHOLD = 0.10  # Percentage of free space to keep as spare (e.g., 10%)
MAX_SWAP_LIMIT_GB = 64  # Maximum swap file size in GB
MIN_SWAP_SIZE_GB = 1    # Minimum swap file size in GB

def show_current_swap():
    """Display detailed swap information with each swap file listed separately in GB."""
    print("Current swap status:")

    swap_files = subprocess.check_output("cat /proc/swaps", shell=True).decode().splitlines()
    print("\nIndividual Swap Files:")
    swap_details = []
    for line in swap_files[1:]:  # Skip the header line
        parts = line.split()
        path = parts[0]
        size_gb = int(parts[2]) / (1024 ** 2)  # Convert kB to GB
        swap_details.append((path, size_gb))
        print(f"  Path: {path}, Size: {size_gb:.2f} GB")

    swap_info = subprocess.check_output("cat /proc/meminfo | grep Swap", shell=True).decode().splitlines()
    print("\nTotal Swap Information:")
    for line in swap_info:
        key, value_kb = line.split(':')
        value_gb = int(value_kb.strip().split()[0]) / (1024 ** 2)  # Convert kB to GB
        print(f"{key}: {value_gb:.2f} GB")

    return swap_details

def check_free_space():
    """Calculate the maximum allowable swap size based on available space and spare threshold."""
    _, _, free = shutil.disk_usage("/")
    free_gb = free // (1024 ** 3)  # Convert free space to GB
    max_allocatable_swap = int(free_gb * (1 - SPARE_THRESHOLD))
    max_swap_size = min(max_allocatable_swap, MAX_SWAP_LIMIT_GB)
    return max_swap_size

def resize_swap(swap_file, size_gb):
    """Resize the swap file to the exact specified size in GB."""
    if size_gb == 0:
        confirm = input(f"Are you sure you want to delete the swap file {swap_file}? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Deletion canceled.")
            return
        print(f"Deleting swap file {swap_file}...")
        os.system(f"sudo swapoff {swap_file}")
        os.system(f"sudo rm {swap_file}")
        print(f"Swap file {swap_file} deleted.")
    else:
        print(f"Resizing {swap_file} to {size_gb} GB...")
        os.system(f"sudo swapoff {swap_file}")
        os.system(f"sudo rm {swap_file}")
        os.system(f"sudo fallocate -l {size_gb}G {swap_file}")
        os.system(f"sudo chmod 600 {swap_file}")
        os.system(f"sudo mkswap {swap_file}")
        os.system(f"sudo swapon {swap_file}")
        print(f"Swap file {swap_file} resized to {size_gb} GB.")

def create_new_swap(new_swap_file, size_gb):
    """Create a new swap file with the specified size in GB."""
    print(f"Creating a new swap file {new_swap_file} with {size_gb} GB...")
    os.system(f"sudo fallocate -l {size_gb}G {new_swap_file}")
    os.system(f"sudo chmod 600 {new_swap_file}")
    os.system(f"sudo mkswap {new_swap_file}")
    os.system(f"sudo swapon {new_swap_file}")
    print(f"New swap file {new_swap_file} of {size_gb} GB created.")

def main():
    swap_details = show_current_swap()

    max_swap_size = check_free_space()
    print(f"\nMaximum allowable swap size based on available space: {max_swap_size} GB")
    print(f"Minimum allowable swap size: {MIN_SWAP_SIZE_GB} GB")

    choice = input("Do you want to resize an existing swap file (1) or create a new swap file (2)? Enter 1 or 2: ").strip()
    if choice not in ['1', '2']:
        print("Invalid choice. Exiting.")
        sys.exit(1)

    if choice == '1':
        if not swap_details:
            print("No active swap files found to resize.")
            sys.exit(1)

        if len(swap_details) == 1:
            # Only one swap file, automatically select it
            selected_swap_file = swap_details[0][0]
            print(f"\nOnly one swap file found: {selected_swap_file}")
        else:
            # Multiple swap files, prompt user to select one
            print("\nAvailable swap files:")
            for idx, (path, size_gb) in enumerate(swap_details, start=1):
                print(f"{idx}. Path: {path}, Size: {size_gb:.2f} GB")
            
            try:
                file_choice = int(input("Select the swap file number to resize: ").strip())
                selected_swap_file = swap_details[file_choice - 1][0]
            except (IndexError, ValueError):
                print("Invalid selection. Exiting.")
                sys.exit(1)

        try:
            size_gb = int(input("Enter the desired swap size in GB (enter 0 to delete): ").strip())
        except ValueError:
            print("Invalid size entered. Exiting.")
            sys.exit(1)

        # Validate size
        if size_gb < 0 or (size_gb > max_swap_size and size_gb != 0):
            print(f"Swap size must be between 0 (to delete) and {max_swap_size} GB, considering spare space. Exiting.")
            sys.exit(1)

        resize_swap(selected_swap_file, size_gb)
        report_action = f"Resized swap file {selected_swap_file} to {size_gb} GB." if size_gb > 0 else f"Deleted swap file {selected_swap_file}."

    elif choice == '2':
        new_swap_file = "/swapfile2"
        try:
            size_gb = int(input("Enter the desired size for the new swap file in GB: ").strip())
        except ValueError:
            print("Invalid size entered. Exiting.")
            sys.exit(1)

        if size_gb < MIN_SWAP_SIZE_GB or size_gb > max_swap_size:
            print(f"Swap size must be between {MIN_SWAP_SIZE_GB} and {max_swap_size} GB, considering spare space. Exiting.")
            sys.exit(1)

        create_new_swap(new_swap_file, size_gb)
        report_action = f"Created new swap file {new_swap_file} of {size_gb} GB."

    print("\nAction completed. Updated swap information:")
    show_current_swap()
    print("\nSummary:", report_action)


if __name__ == "__main__":
    main()
