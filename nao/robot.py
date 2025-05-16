import requests
import paramiko
from naoqi import ALProxy
import os
import time
from robot_IP import robot_IP

def send_audio(file_path, server_url):
    with open(file_path, 'rb') as f:
        files = {'audio': (file_path, f, 'audio/wav')}  # must use 'audio' as the key
        response = requests.post(server_url, files=files)
    
    return response.json()['score']
 
# CONFIGURE THESE:
SERVER_URL = "http://localhost:5000/chat"  # Replace with your actual server IP
robot_PORT = 9559

# Initialize the proxies
record = ALProxy("ALAudioRecorder", robot_IP, robot_PORT)
tts = ALProxy("ALAnimatedSpeech", robot_IP, robot_PORT)
memory = ALProxy("ALMemory", robot_IP, robot_PORT)

# File paths
record_path = '/data/home/nao/recordings/recorded_audio.wav'
local_path = os.getcwd()  # Current directory to save the file locally

# Memory keys for head buttons
sensors = {
    "head_middle": "Device/SubDeviceList/Head/Touch/Middle/Sensor/Value",
    "right_foot": "Device/SubDeviceList/RFoot/Bumper/Left/Sensor/Value"
}

tts.say('Hi, I am Ada. Please press my head to start recording your movie review or my right foot to quit this program!')

recording = False
last_button_state = 0  # Store previous state

try:
    while True:
        current_button_state = memory.getData(sensors["head_middle"])

        exit_button = memory.getData(sensors["right_foot"])

        if exit_button == 1.0:
            tts.say('Goodbye my friend!')
            break

        # Detect rising edge: was 0, now 1
        if current_button_state == 1.0 and last_button_state == 0.0:
            if not recording:
                tts.say('Recording!')
                record.startMicrophonesRecording(record_path, 'wav', 16000, (0, 0, 1, 0))
                recording = True
            else:
                tts.say('Stopping recording!')
                record.stopMicrophonesRecording()

                tts.say('Processing...')
                # get the recording from the robot
                robot_username = 'nao'
                robot_password = 'nao'
                
                try:
                    # Connect to the robot via SSH
                    ssh_client = paramiko.SSHClient()
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh_client.connect(robot_IP, username=robot_username, password=robot_password)

                    # Create SFTP session
                    sftp = ssh_client.open_sftp()

                    # Download the file from the robot to the local machine
                    local_audio_path = os.path.join(local_path, 'recorded_audio.wav')
                    sftp.get(record_path, local_audio_path)

                    # Close the SFTP session and SSH client
                    sftp.close()
                    ssh_client.close()

                except Exception as e:
                    print("File transfer failed:", e)
                    exit(1)

                # send to server
                score = float(send_audio(local_audio_path, SERVER_URL))
                print(score)
                
                # make Ada say score
                sentiment = 'positive'
                if score < 0.5:
                    sentiment = 'negative'
                tts.say('The score of the review is ' + str(round(score, 3)) + ' which makes the sentiment ' + sentiment)
                
                recording = False

        # Update last button state and sleep a bit to avoid high CPU usage
        last_button_state = current_button_state
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Script interrupted manually.")
