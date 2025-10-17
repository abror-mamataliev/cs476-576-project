import os
import requests
import time
import subprocess

"""
    TO DO LIST AND NOTES TO SELF:

        1) Make sure communication between this script and Pi is all good
            - Flask server on Pi with /capture, /get_image, /send_to_cloud endpoints?
            - Need Rasp. Pi's address and Cloud servers address for take_and_send_picture()

        2) Implement a final output function?
            - Computes stats based off the logs recieved from the Pi
            - Outputs stats to user, and makes reccomendation on whether or not to use Edge or Cloud

        3) Implement retry logic for HTTP requests?

        4) Implement get_results_from_pi()
			- Would receive the logs/stats tracked by the Pi so we can make a final output for the user

        - Pi needs to log:
            start time -> begin when it sends the picture to the execution target
            response time -> end when it receives the workload results from the execution target
            runtime -> total time taken 
            probably other things too

        - JSON for log formatting?

        - Pi will need these end points i think:
            /capture -> capture image
            /get_image -> send image back to edge device/simulate.py
            /send_to_cloud -> send image to cloud server
	        /log_results -> accept workload results from edge device/simulate.py
	        /get_logs -> return logs for edge device/simulate.py to compute stats/recommendations for final output to user
			And maybe more

        - Cloud server questions:
            - Will the cloud server send the results of its workload directly to the Rasp. Pi
                or will it send it back to this script, which will then send it to the Pi?

            - Will the cloud server have the Dockerfile already on it, or will this script need
                to send it the Dockerfile when the execution_target == "cloud"
"""

def get_input():
    """
    Gathers the simulations parameters from the user

    Returns:
        execution_target: where the workdload will be executed -> string
        deadline: Time in milliseconds in which the workload must be completed by -> int
        dockerfile_path: File path to the dockerfile that will act as the workload -> string
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

    # Gather Dockerfile path
    while True:
        dockerfile_path = input("\nEnter Dockerfile path: ").strip()
        dockerfile_path = os.path.abspath(dockerfile_path)
        if os.path.exists(dockerfile_path):
            break
        print("File does not exist. Please enter a valid Dockerfile path.")

    # Display configuration 
    print("\n--- Simulation Configuration ---")
    print(f"Target: {execution_target}")
    print(f"Deadline: {deadline} ms")
    print(f"Dockerfile: {dockerfile_path}")
    print("-------------------------------")

    return execution_target, deadline, dockerfile_path




def pi_take_picture(pi_address):
    """
    Tells the Raspberry Pi to take a picture and to send it to this machine
    Saves the picture to a local file path

    Args:
        pi_address: IP or hostname of the Pi -> str
    
    Returns:
        picture_file_path: The file path to the image we received from the Rasp. Pi -> string
    """
    
    # Tells Raspberry Pi to capture the image
    try:
        print("\tTelling Rasp. Pi to take a picture...\n")
        # Sending HTTP get request to Rasp. Pi at port 5000, hitting /capture endpoint
        requests.get(f"http://{pi_address}:5000/capture", timeout=5)
    except Exception as e:
        print(f"\t\nError: Unable to tell Raspberry Pi to capture image: {e}\n")
        return None    

    # Tells Raspberry Pi to send image to this machine
    try:
        print("\tTelling Rasp. Pi to send picture to this machine...\n")
        # Sending HTTP get request to Rasp. Pi at port 5000, hitting /get_image endpoint
        img_response = requests.get(f"http://{pi_address}:5000/get_image", timeout=5)
    except Exception as e:
        print(f"\t\nError: Unable to tell Raspberry Pi to send image to this machine: {e}\n")
        return None        
    
    # File path to the image we got from the Rasp. Pi
    picture_file_path = "/tmp/latest_image.jpg"
    with open(picture_file_path, "wb") as f: # Open the file to binary write
        f.write(img_response.content) # Write image into that file

    return picture_file_path




def run_workload_on_edge(dockerfile_path, picture_file_path):
    """
        Runs the image classification workload in a Docker container on this edge device

        Args:
            dockerfile_path: File path to the Dockerfile -> string
            picture_file_path: File path to the picture received from Rasp. Pi -> string

        Returns:
            dict: {
                status: Whether or not picture could be classified -> "success" or "fail"
                classification: What the result of the workload is if it succeeded -> string
            }
    """

    # Run the image classification workload on this machine to simulate edge computing
    print("\nRunning workload locally to simulate edge computing...\n")

    # The name for the docker image that we'll build
    image_tag = "edge_workload_image"

    # Sanity checks
    # Not sure if this ones really necessary as we already check if path exists in get_input()
    if not os.path.exists(dockerfile_path):
        print(f"\t\nError: Dockerfile not found at path: {dockerfile_path}")
        return {"status": "fail", "classification": "Dockerfile not found at path: {dockerfile_path}"}
    if not os.path.exists(picture_file_path):
        print(f"\t\nError: Image not found at path: {picture_file_path}")
        return {"status": "fail", "classification": "Image not found at path: {picture_file_path}"}

    print(f"\n[Edge device] Building Docker image from {dockerfile_path}...\n")

    try:
        # Build the Docker image
        subprocess.run(
            ["docker", "build", "-t", image_tag, "-f", dockerfile_path, "."], # Run this command in the shell
            check=True, # If command fails, raise CalledProcessError
            stdout=subprocess.PIPE, # capture standard output
            stderr=subprocess.PIPE # capture standard errors
        )
    except subprocess.CalledProcessError as e:
        return {"status": "fail", "classification": f"Build failed: {e.stderr.decode()}"}

    print(f"\n[Edge device] Running workload on {picture_file_path}...\n")

    # Run the container
    try:
        # Run shell command
        result = subprocess.run(
            [
                "docker", "run", "--rm", # Start a container from an image, --rm removes the container once its done running
                "-v", f"{os.path.abspath(picture_file_path)}:/input_image.jpg", # Mounts a file from this machine into the container’s filesystem
                image_tag # Name of the image
            ],
            capture_output=True, # Captures stdout and stderr from the container
            text=True, # Decodes output as a string
            check=True # If Docker fails, raisese CalledProcessError
        )

        return{
            "status": "success",
            "classification": result.stdout.strip()
        }
    
    except subprocess.CalledProcessError as e:
        return {
            "status": "fail",
            "classification": f"Execution failed: {e.stderr}"
        }
    



def run_workload_on_cloud(pi_address, cloud_address):
    """
        Tells Rasp. Pi to send the picture it took to cloud server

        Args:
            pi_address: IP or hostname of the Pi -> str
            cloud_address: IP or hostname of the cloud server -> str
    """

    # Should we also send the Dockerfile to the cloud server? Or will it already have the Dockerfile?

    try:
        print("\tTelling Rasp. Pi to send the picture to the cloud server...\n")
        # Tells Raspberry Pi to push image to cloud server
        requests.post(f"http://{pi_address}:5000/send_to_cloud", json={"cloud_address": cloud_address}, timeout=5)
    except Exception as e:
        print(f"\t\nError: Unable to tell Pi to send picture to cloud: {e}\n")
        return None




def send_workload_results_to_pi(pi_address, status, classification):
    """
        Sends the results of the edge-computed workload to the Rasp. Pi as json
        
        Args:
            pi_address: IP or hostname of the Pi -> str
            status: Whether or not picture could be classified -> "success" or "fail"
            classification: What the result of the workload is if it succeeded -> string
    """
    
    print("\nSending results of the workload to Raspberry Pi...\n")
    try:
        requests.post(
            f"http://{pi_address}:5000/receive_results",
            json={"status": status, "classification": classification}
        )
    except Exception as e:
        print(f"\t\nError: Could not send results back to Pi: {e}\n")




def main():

    # Placeholders
    pi_address = "..."
    cloud_address = "..."

    # Get the simulation parameters from the user
    execution_target, deadline, dockerfile_path = get_input()

    print("\nBeginning simulation...\n")

    # Tell Rasp. Pi to capture image, store it locally on this machine
    picture_file_path = pi_take_picture(pi_address)
    if not picture_file_path:
        print("\t\nFailed to get image from Raspberry Pi\n")
        return
    
    # Execution target is edge
    if execution_target == "edge":
        # Run the image classification docker workload on this machine to simulate edge computing
        result = run_workload_on_edge(dockerfile_path, picture_file_path)

        # Send the results of the workload to the Rasp. Pi so it can finish its logging
        send_workload_results_to_pi(pi_address, result["status"], result["classification"])

    # Execution target is cloud
    else:
        # Tell Rasp. Pi to send the image to the cloud server so it can run the workload
        run_workload_on_cloud(pi_address, cloud_address)    # Will the cloud server already have the dockerfile, or should we send it to the server from here?

    # Need to somehow get results/logs from Rasp. Pi still
    # get_results_from_pi()

    # Need to do calculations on results/logs from the Rasp. Pi
    # 'deadline' input variable will be used in here along with results from get_results_from_pi()
    # output_final_results()

if __name__ == "__main__":
    main()
