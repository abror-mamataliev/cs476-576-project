import os
import requests

"""
    TO DO LIST AND NOTES TO SELF:
        1) Implement function to initiate/run the workload locally when execution target is edge
            - I think it would be called within take_and_send_picture()
            - Would this be the function that would send the workload results back to the Pi?
        
        2) Make sure communication between this script and Pi is all good
            - Flask server on Pi with /capture, /get_image, /send_to_cloud endpoints?
            - Need Rasp. Pi's address and Cloud servers address for take_and_send_picture()

        3) Final output function?
            - Computes stats based off the logs recieved from the Pi
            - Outputs stats to user, and makes reccomendation on whether or not to use Edge or Cloud

        4) Add retry logic for HTTP requests in take_and_send_picture()?

        5) When and where to receive logs/results from the Pi?

        - Pi needs to log:
            request start time
            response time
            runtime
            success/failure
            probably other things too

        - JSON for log formatting?

        - Pi will need these end points i think:
            /capture -> capture image
            /get_image -> send image back to edge device/simulate.py
            /send_to_cloud -> send image to cloud server
	        /log_results -> accept workload results from edge device/simulate.py
	        /get_logs -> return logs for edge device/simulate.py to compute stats/recommendations for final output to user
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



def take_and_send_picture(pi_address, cloud_address, execution_target):
    """
    Tells the Rasperry Pi to take a picture and to send it to the execution target

    Args:
        pi_address: IP or hostname of the Pi -> str
        cloud_address: IP/hostname of server the pi might send the image to -> str
        execution_target: Where the Pi will be told to send the image to -> str
    """

    print("\nCommunicating with Rasperry Pi.\n") 
    
    # Tells Rasperry Pi to capture the image
    try:
        print("\tTelling Rasp. Pi to take a picture\n")
        # Sending HTTP get request to Rasp. Pi at port 5000, hitting /capture endpoint
        requests.get(f"http://{pi_address}:5000/capture", timeout=5)
    except Exception as e:
        print(f"\t\nError: Unable to tell Rasperry Pi to capture image: {e}\n")
        return None

    # Receive the image to this machien
    if execution_target == "edge":
        try:
            print("\tTelling Rasp. Pi to send the picture to this machine\n")
            # send GET request to Rasp. Pi for it to send image to this machine
            img_response = requests.get(f"http://{pi_address}:5000/get_image", timeout=5)
        except Exception as e:
            print(f"\t\nError: Unable to receive image from Rasperry Pi:: {e}\n")
            return None
        
        # Defining a local path where the image will be saved
        image_file_path = "/tmp/latest_image.jpg"
        
        # Open the file path for writing in binary mode, then write the image to it
        with open(image_file_path, "wb") as f:
            f.write(img_response.content)

        # TODO: implement a function that will run the workload on this machine:
        # runtime = run_docker_locally(dockerfile_path, image_file_path)
    
    # Tell Rasp. Pi to send image to cloud server
    elif execution_target == "cloud":
        try:
            print("\tTelling Rasp. Pi to send the picture to the cloud server\n")
            # Tells Rasperry Pi to push image to cloud server
            requests.post(f"http://{pi_address}:5000/send_to_cloud", json={"cloud_address": cloud_address}, timeout=5)
        except Exception as e:
            print(f"\t\nError: Unable to tell Pi to send image to cloud: {e}\n")
            return None
        
    # Need to somehow get results/logs from pi still
    
def main():

    # Get the simulation parameters from the user
    execution_target, deadline, dockerfile_path = get_input()

    print("\nBeginning simulation...\n")

    # Tell the Raspery Pi to take a picture, and where to send it to
    take_and_send_picture(pi_address, cloud_address, execution_target)

if __name__ == "__main__":
    main()