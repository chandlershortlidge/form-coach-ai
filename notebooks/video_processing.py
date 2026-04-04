


import base64
import os 
import cv2



"""VIDEO PROCESSING PIPELINE"""

def create_video_name_and_save_to_files(filepath_in: str, frames: list) -> str:
    basename = os.path.basename(filepath_in) # takes path and returns basename (video_name.mp4)
    split_text = basename.split(".") # splits basename into list
    video_name = split_text[0] # returns first item on that list
    for i, frame in enumerate(frames):
        cv2.imwrite(f"/Users/chandlershortlidge/Desktop/Ironhack/fitness-form-coach/data/processed/processed-images/{video_name}_{i}.jpg", frame) 
        # cv2.imwrite is where the frame gets saved to disk
    print(f"Saved to processed-images/{video_name}")
    print("Video name:", video_name)
    return video_name

# def save_video_frames(filepath_in, frames):
#     video_name = create_video_name(filepath_in)

def analyze_video(filepath_in: str, max_seconds: int, frame_count: int) -> list[str]:
    frames = extract_video_frames(filepath_in, max_seconds, frame_count)
    video_name = create_video_name_and_save_to_files(filepath_in, frames)
    encoded_frames = []
    for i in range(frame_count):
        filepath = f"/Users/chandlershortlidge/Desktop/Ironhack/fitness-form-coach/data/processed/processed-images/{video_name}_{i}.jpg"
        encoded = base_encoder(filepath)
        encoded_frames.append(encoded)

    return encoded_frames


# if your video is 30fps and you want a frame every 2 seconds, that's every 60 frames (2 × 30).
# interval_seconds = max_seconds / extracted_frame_count
# Interval_frames = interval_seconds * native_fps

def extract_video_frames(filepath_in: str, max_seconds: int, frame_count: int) -> list:
    frames = []
    current_frame = 0
    cap = cv2.VideoCapture(filepath_in) # opens the video like open('file.txt'). cap is now the video object 
    native_fps = cap.get(cv2.CAP_PROP_FPS) # cap prop fps gets the native frame rate of the recording
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    actual_duration = total_frames / native_fps
    effective_seconds = min(max_seconds, actual_duration)
    interval_seconds = effective_seconds / frame_count 
    # ex: 0.66 interval secionds = 10 max seconds / 15 desired frames
    frame_interval = interval_seconds * native_fps 
    # 20  = 0.66 * 30 native fps 
    max_frames = int(native_fps * effective_seconds)
    # calculate the max frames in a video. eg: 30fps * 10 seconds = 300 max frames
    targets = [int(i * frame_interval) for i in range(frame_count)]
    while current_frame < max_frames:
        success, frame = cap.read()
        if not success:
            break
        if current_frame in targets:
            frames.append(frame)
        
        current_frame += 1
    cap.release() # closes the tile
    
    print(f"Frames processed: {frame_count}, ({effective_seconds}s cap)")
    
    return frames


# create a base64 encoder so taht we can send images to the model API. 
# the model API communicates via JSON. JSON is text. You can't put raw images bytes into JSON.
# So you encode the bytes into a text string which can be decoded by the model.
def base_encoder(filepath_in: str) -> str:
    with open(filepath_in, 'rb') as image_file:
        # read the binary data
        binary_data = image_file.read()

        # encode as base 64
        base64_data = base64.b64encode(binary_data)

        # convert to string 
        base64_string = base64_data.decode('utf-8')
        
        # print or use base64 string as needed
        return base64_string


