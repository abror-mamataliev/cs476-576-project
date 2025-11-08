from base64 import b64encode
from os.path import exists

from decouple import config
from requests import ConnectTimeout, post


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
        execution_target = input(
            "\nEnter execution target (\"edge\" or \"cloud\"). Default is \"edge\": "
        ).strip().lower()
        if execution_target == "":
            execution_target = "edge"
            break

        if execution_target in ("edge", "cloud"):
            break

        print("Invalid input. Please enter <Edge> or <Cloud>.")
        continue

    # Gather deadline
    while True:
        deadline = input("\nEnter workload deadline (in milliseconds). Default is 1000: ").strip()
        if deadline == "":
            deadline = 1000
            break

        if not deadline.isdigit() or int(deadline) <= 0:
            print("Invalid input. Please enter a positive integer for the deadline.")
        else:
            deadline = int(deadline)
            break

    # Gather image path
    while True:
        image_path = input("\nEnter image path: ").strip()
        if exists(image_path):
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
    raspberry_pi_url = config('RASPBERRY_PI_URL')

    # Get the simulation parameters from the user
    execution_target, deadline, image_path = get_input()
    timeout = config('MAX_TIMEOUT', default=10, cast=int)

    print("\nBeginning simulation...\n")

    with open(image_path, "rb") as img_file:
        image_bytes = img_file.read()
        image = b64encode(image_bytes).decode("utf-8")

    try:
        response = post(raspberry_pi_url, json={'device': execution_target, 'body': {'image': image}}, timeout=timeout)
        response_json = response.json()
        response_json['stats']['deadline_met'] = response_json['stats']['latency'] <= int(deadline)
        print("Simulation Results:")
        print(response_json)
    except ConnectTimeout as e:
        print(f"Error: Connection to Raspberry Pi timed out: {e}")
    except Exception as e:
        print(f"An error occurred during the simulation: {e}")


if __name__ == "__main__":
    main()
