from base64 import b64encode
from os.path import exists

from decouple import config
from requests import ConnectTimeout, post


def get_input():
    """
    Gathers the simulations parameters from the user

    Returns:
        execution_target: where the workdload will be executed -> string ("edge", "cloud", or "comparison")
        deadline: Time in milliseconds in which the workload must be completed by -> int
        image_path: File path to the image that will be sent to the workload -> string
    """
    while True:
        execution_target = input(
            "\nEnter execution target (\"edge\", \"cloud\", or \"comparison\"). Default is \"edge\": "
        ).strip().lower()
        if execution_target == "":
            execution_target = "edge"
            break

        if execution_target in ("edge", "cloud", "comparison"):
            break

        print("Invalid input. Please enter \"edge\", \"cloud\", or \"comparison\".")
        continue

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

    while True:
        image_path = input("\nEnter image path: ").strip()
        if exists(image_path):
            break

        print("File does not exist. Please enter a valid image path.")

    print("\n--- Simulation Configuration ---")
    print(f"Target: {execution_target}")
    print(f"Deadline: {deadline} ms")
    print(f"Image: {image_path}")
    print("-------------------------------")

    return execution_target, deadline, image_path


def format_results(response_json, deadline):
    """
    Format results in a user-friendly way instead of raw JSON.
    
    Args:
        response_json: Response from Raspberry Pi
        deadline: Deadline in milliseconds
    """
    result = response_json.get('result', {})
    response = result.get('response', {})
    image = response_json.get('image', {})
    stats = response_json.get('stats', {})
    
    print("\n" + "="*60)
    print("CLASSIFICATION RESULT")
    print("="*60)
    if 'digit' in response:
        print(f"Predicted Digit: {response['digit']}")
        print(f"Confidence: {response['confidence']:.1%}")
    print(f"Status: {'Success' if result.get('status_code') == 200 else 'Failed'}")
    
    print("\n" + "-"*60)
    print("IMAGE INFORMATION")
    print("-"*60)
    print(f"Format: {image.get('format', 'unknown')}")
    print(f"Size: {image.get('size', 0):.2f} KB")
    
    print("\n" + "-"*60)
    print("PERFORMANCE STATISTICS")
    print("-"*60)
    print(f"Execution Target: {stats.get('device', 'unknown').upper()}")
    print(f"Latency: {stats.get('latency', 0):.2f} ms")
    print(f"Deadline: {deadline} ms")
    print(f"Deadline Met: {'YES' if stats.get('deadline_met') else 'NO'}")


def generate_recommendation(stats, deadline):
    """
    Generate recommendation based on latency and deadline compliance.
    
    Args:
        stats: Dictionary with 'device', 'latency', 'deadline_met'
        deadline: Deadline in milliseconds
    
    Returns:
        Recommendation string
    """
    latency = stats['latency']
    device = stats['device']
    deadline_met = stats.get('deadline_met', False)
    
    if deadline_met:
        if device == 'edge':
            return (
                "RECOMMENDATION: Use Edge Computing\n"
                f"   • Meets deadline ({latency:.2f}ms < {deadline}ms)\n"
                "   • Fast response time\n"
                "   • Lower latency for real-time applications\n"
                "   • Better for time-sensitive workloads"
            )
        else:
            return (
                "RECOMMENDATION: Cloud Computing\n"
                f"   • Meets deadline ({latency:.2f}ms < {deadline}ms)\n"
                "   • Consider edge for even faster response\n"
                "   • Cloud may have higher network latency"
            )
    else:
        if device == 'edge':
            return (
                "RECOMMENDATION: Edge Computing Failed Deadline\n"
                f"   • Exceeded deadline ({latency:.2f}ms > {deadline}ms)\n"
                "   • Consider optimizing workload\n"
                "   • Or increase deadline requirement"
            )
        else:
            return (
                "RECOMMENDATION: Cloud Computing Failed Deadline\n"
                f"   • Exceeded deadline ({latency:.2f}ms > {deadline}ms)\n"
                "   • Try edge computing for faster response\n"
                "   • Or increase deadline requirement\n"
                "   • Network latency may be the issue"
            )


def run_comparison(deadline, image_path, raspberry_pi_url, timeout):
    """
    Run workload on both edge and cloud, then compare results.
    
    Args:
        deadline: Deadline in milliseconds
        image_path: Path to image file
        raspberry_pi_url: URL of Raspberry Pi
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary with 'edge' and 'cloud' results
    """
    print("\n" + "="*60)
    print("RUNNING COMPARISON: Edge vs Cloud")
    print("="*60)
    
    with open(image_path, "rb") as img_file:
        image_bytes = img_file.read()
        image = b64encode(image_bytes).decode("utf-8")
    
    results = {}
    
    for device in ['edge', 'cloud']:
        print(f"\nTesting {device.upper()} device...")
        try:
            response = post(raspberry_pi_url, json={'device': device, 'body': {'image': image}}, timeout=timeout)
            response_json = response.json()
            response_json['stats']['deadline_met'] = response_json['stats']['latency'] <= int(deadline)
            results[device] = response_json
            if response_json.get('result', {}).get('status_code') == 200:
                print(f"   {device.upper()} completed successfully")
            else:
                print(f"   {device.upper()} completed with errors")
        except ConnectTimeout as e:
            print(f"   Error: Connection to {device} device timed out: {e}")
            results[device] = None
        except Exception as e:
            print(f"   Error testing {device}: {e}")
            results[device] = None
    
    return results


def print_comparison(results, deadline):
    """Print side-by-side comparison of edge vs cloud results."""
    print("\n" + "="*60)
    print("EDGE vs CLOUD COMPARISON")
    print("="*60)
    
    edge_result = results.get('edge')
    cloud_result = results.get('cloud')
    
    if edge_result and cloud_result:
        edge_stats = edge_result.get('stats', {})
        cloud_stats = cloud_result.get('stats', {})
        edge_response = edge_result.get('result', {}).get('response', {})
        cloud_response = cloud_result.get('result', {}).get('response', {})
        
        print(f"\n{'Metric':<30} {'Edge':<15} {'Cloud':<15}")
        print("-" * 60)
        print(f"{'Latency (ms)':<30} {edge_stats.get('latency', 0):<15.2f} {cloud_stats.get('latency', 0):<15.2f}")
        print(f"{'Deadline Met':<30} {'YES' if edge_stats.get('deadline_met') else 'NO':<15} {'YES' if cloud_stats.get('deadline_met') else 'NO':<15}")
        
        if 'digit' in edge_response:
            print(f"{'Predicted Digit':<30} {edge_response.get('digit', 'N/A'):<15} {cloud_response.get('digit', 'N/A'):<15}")
            print(f"{'Confidence':<30} {edge_response.get('confidence', 0):<15.1%} {cloud_response.get('confidence', 0):<15.1%}")
        
        print("\n" + "-"*60)
        print("OVERALL RECOMMENDATION")
        print("-"*60)
        
        edge_met = edge_stats.get('deadline_met', False)
        cloud_met = cloud_stats.get('deadline_met', False)
        edge_latency = edge_stats.get('latency', float('inf'))
        cloud_latency = cloud_stats.get('latency', float('inf'))
        
        if edge_met and cloud_met:
            if edge_latency < cloud_latency:
                print("RECOMMENDATION: Use EDGE Computing")
                print(f"   • Edge is faster ({edge_latency:.2f}ms vs {cloud_latency:.2f}ms)")
                print(f"   • Both meet deadline ({deadline}ms)")
                print("   • Edge provides lower latency for real-time applications")
            else:
                print("RECOMMENDATION: Use CLOUD Computing")
                print(f"   • Cloud is faster ({cloud_latency:.2f}ms vs {edge_latency:.2f}ms)")
                print(f"   • Both meet deadline ({deadline}ms)")
                print("   • Cloud may be more cost-effective for this workload")
        elif edge_met and not cloud_met:
            print("RECOMMENDATION: Use EDGE Computing")
            print(f"   • Only edge meets deadline ({edge_latency:.2f}ms < {deadline}ms)")
            print(f"   • Cloud exceeded deadline ({cloud_latency:.2f}ms > {deadline}ms)")
            print("   • Edge is the only viable option for this deadline")
        elif not edge_met and cloud_met:
            print("RECOMMENDATION: Use CLOUD Computing")
            print(f"   • Only cloud meets deadline ({cloud_latency:.2f}ms < {deadline}ms)")
            print(f"   • Edge exceeded deadline ({edge_latency:.2f}ms > {deadline}ms)")
            print("   • Cloud is the only viable option for this deadline")
        else:
            print("RECOMMENDATION: Neither meets deadline")
            print(f"   • Edge: {edge_latency:.2f}ms (exceeded by {edge_latency - deadline:.2f}ms)")
            print(f"   • Cloud: {cloud_latency:.2f}ms (exceeded by {cloud_latency - deadline:.2f}ms)")
            print("   • Consider optimizing workload or increasing deadline requirement")
    elif edge_result:
        print("\nOnly Edge results available (Cloud failed)")
        format_results(edge_result, deadline)
    elif cloud_result:
        print("\nOnly Cloud results available (Edge failed)")
        format_results(cloud_result, deadline)
    else:
        print("\nBoth Edge and Cloud tests failed")
    
    print("="*60 + "\n")


def main():
    raspberry_pi_url = config('RASPBERRY_PI_URL')
    execution_target, deadline, image_path = get_input()
    timeout = config('MAX_TIMEOUT', default=10, cast=int)

    if execution_target == "comparison":
        results = run_comparison(deadline, image_path, raspberry_pi_url, timeout)
        print_comparison(results, deadline)
        return

    print("\nBeginning simulation...\n")

    with open(image_path, "rb") as img_file:
        image_bytes = img_file.read()
        image = b64encode(image_bytes).decode("utf-8")

    try:
        response = post(raspberry_pi_url, json={'device': execution_target, 'body': {'image': image}}, timeout=timeout)
        response_json = response.json()
        response_json['stats']['deadline_met'] = response_json['stats']['latency'] <= int(deadline)
        
        format_results(response_json, int(deadline))
        
        print("\n" + "="*60)
        print("RECOMMENDATION")
        print("="*60)
        recommendation = generate_recommendation(response_json['stats'], int(deadline))
        print(recommendation)
        print("="*60 + "\n")
        
    except ConnectTimeout as e:
        print(f"Error: Connection to Raspberry Pi timed out: {e}")
    except Exception as e:
        print(f"An error occurred during the simulation: {e}")


if __name__ == "__main__":
    main()
