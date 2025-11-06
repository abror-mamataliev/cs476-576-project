import os
import requests
import subprocess


def get_input():
    """
    Gathers the simulations parameters from the user

    Returns:
        execution_target: where the workdload will be executed -> string
        deadline: Time in milliseconds in which the workload must be completed by -> int
        image_path: File path to the image that will be sent to the workload -> string
    """

    # Gather execution target
    while True:
        execution_target = input("\nEnter execution target (Edge or Cloud): ").strip().lower()
        if execution_target in ("edge", "cloud"):
            break
        print("Invalid input. Please enter <Edge> or <Cloud>.")

    # Gather deadline
    while True:
        deadline = input("\nEnter workload deadline (in milliseconds): ").strip()
        if deadline.isdigit() and int(deadline) > 0:
            break
        print("Invalid input. Please enter a positive integer for the deadline.")

    # Gather image path
    while True:
        image_path = input("\nEnter image path: ").strip()
        if os.path.exists(image_path):
            break
        print("File does not exist. Please enter a valid image path.")

    # Display configuration 
    print("\n--- Simulation Configuration ---")
    print(f"Target: {execution_target}")
    print(f"Deadline: {deadline} ms")
    print(f"Image: {image_path}")
    print("-------------------------------")

    return execution_target, deadline, image_path


def main():
    # Placeholders
    pi_address = "..."
    cloud_address = "..."

    # Get the simulation parameters from the user
    execution_target, deadline, image_path = get_input()

    print("\nBeginning simulation...\n")

    # Read image file and prepare for sending
    with open(image_path, "rb") as img_file:
        image = img_file.read()

    # Execution target is edge
    if execution_target == "edge":
        # Run the image classification docker workload on this machine to simulate edge computing
        result = run_workload_on_edge(dockerfile_path, picture_file_path)

        # Send the results of the workload to the Rasp. Pi so it can finish its logging
        send_workload_results_to_pi(pi_address, result["status"], result["classification"])

    # Execution target is cloud
    else:
        # Tell Rasp. Pi to send the image to the cloud server so it can run the workload
        run_workload_on_cloud(pi_address,
                              cloud_address)  # Will the cloud server already have the dockerfile, or should we send it to the server from here?

    # Need to somehow get results/logs from Rasp. Pi still
    # get_results_from_pi()

    # Need to do calculations on results/logs from the Rasp. Pi
    # 'deadline' input variable will be used in here along with results from get_results_from_pi()
    # output_final_results()


if __name__ == "__main__":
    main()
