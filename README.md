# Edge vs Cloud Computing Framework

## The Problem

Applications such as **autonomous drones**, **health monitoring devices**, and **IoT systems** require strict real-time guarantees when processing sensor data. Traditional cloud computing introduces unpredictable delays due to network round-trips, making it unsuitable for certain time-sensitive tasks. On the other hand, edge computing processes data closer to the source, significantly reducing latency but at the cost of reduced compute resources.

A key challenge is understanding **when and how** edge vs. cloud computing should be utilized in practice. Without this understanding, critical systems may either waste resources or fail to meet deadlines.

## The Solution

Our solution is a framework that helps determine whether a latency-sensitive application can rely on cloud computing or requires edge processing. Our framework combines **simulation with real-world validation** to give evidence-based guidance.

We implemented a real-world simulation using a **Raspberry Pi** that behaves as a sensor sending arbitrary readings (image of a written number) to a remote server (the cloud) or to an edge device (the user's machine) and measures the end-to-end latency for the workload to be completed. This allows the collection of latency data under real-world network conditions.

The latency data, along with the results of the workload, are used to determine whether cloud computing is sufficient, or if edge computing is necessary.

## Setup Instructions

### 1. Downloading the Workload

Pull the sample Docker image to your edge and cloud devices by running:

```bash
docker pull ghcr.io/abror-mamataliev/cs476-576-project-workload:latest
```

If you wish to test your own Docker image, make sure it exposes port `5000` and implements the same API as described in `src/workload/run.py`.

### 2. Setting up the Raspberry Pi

1. Clone this GitHub repository to your Raspberry Pi
2. Navigate to the `src/rpi/` folder
3. Copy the file `.env.example` to `.env`
4. Add the following environment variables to the `.env` file:
   - `EDGE_DEVICE_URL` - URL where your edge workload container is running (e.g., `http://localhost:5010/run`)
   - `CLOUD_DEVICE_URL` - URL where your cloud workload container is running (e.g., `http://your-cloud-server-ip:5010/run`)

### 3. Setting up Your Machine/Edge Device

1. Clone this repository to your machine/edge device
2. In the project root folder, copy the file `.env.example` to `.env`
3. Add the following environment variables to the `.env` file:
   - `RASPBERRY_PI_URL` - URL where your Raspberry Pi Flask server is running (e.g., `http://raspberry-pi-ip:5000/run/`)
   - `MAX_TIMEOUT` - (Optional) How long an HTTP request will wait before timing out in seconds (default: 10)

### 4. Running the Simulation

1. **On your Raspberry Pi**, navigate to the `src/rpi/` folder and start the Flask server:
   ```bash
   cd src/rpi/
   python run.py
   ```

2. **On your edge and cloud devices**, run the Docker container:
   ```bash
   docker run --name cs476-576-project-workload -p 5010:5000 ghcr.io/abror-mamataliev/cs476-576-project-workload:latest
   ```
   > **Note:** If using your own Docker image, replace the image name accordingly. The container must expose port 5000 and implement a POST `/run` endpoint that accepts a JSON body with an `image` field (base64-encoded) and returns a JSON response with `digit` and `confidence` fields.

3. **On your machine/edge device**, navigate to the project root folder and run:
   ```bash
   python simulate.py
   ```

4. You will be prompted to enter the following:
   
   - **Execution target** - Choose where to run the workload:
     - `cloud` → Runs the workload on the cloud server
     - `edge` → Runs the workload on your local machine (default)
     - `comparison` → Runs the workload on both cloud and edge for direct comparison
   
   - **Deadline** (in milliseconds) - The time limit for workload completion
     > **Default:** 1000ms if left empty
   
   - **Image file path** - Path to an image file for the workload to process
     - Example: `test.jpg`
     - The image should contain a handwritten digit (0-9) for classification

5. The simulation will display the results including:
   - **Classification Result**: The predicted digit and confidence level
   - **Image Information**: Image format and size
   - **Performance Statistics**: Latency, deadline status, and execution target
   - **Recommendation**: Based on whether deadlines were met:
     - If the workload meets the deadline on cloud → Cloud computing is recommended
     - If the workload fails on cloud but succeeds on edge → Edge computing is recommended
     - If the workload fails on both → Neither option is sufficient; consider optimization or increasing the deadline

### 5. Interpreting the Results

After running the simulation, analyze the output to understand your workload's performance under different computing scenarios. Use the provided recommendations to make informed decisions about deploying your applications on edge or cloud infrastructure based on latency requirements and resource availability.

For comparison mode, you'll see a side-by-side analysis showing which platform performs better for your specific deadline requirements.
