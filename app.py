import streamlit as st
import cv2
from streamlit_webrtc import WebRtcMode,VideoTransformerBase, webrtc_streamer
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import base64
from openai import OpenAI
import requests
from prompts import PROMPT_TEXT
import json
from dotenv import load_dotenv
import os
from io import BytesIO

with open('configs.json', 'r') as f:
    config = json.load(f)
# For hidding the menu bar in the screen
hide_menu="""
<style>
#MainMenu {
    visibility:hidden;
}

</style>
"""

# Authenticate user
def authenticate(username, password):
    users= config.get("users")
    if username in users and users[username] == password:
        return True
    return False

def load_config_value():
    # Load environment variable from .env and store it in system variable
    load_dotenv()
    st.session_state.app_title= os.environ.get("TITLE")
    st.session_state.api_key=os.environ.get("OPENAI_API_KEY")
    st.session_state.gpt_model=os.environ.get("GPT_MODEL")
    return True

class VideoTransformer(VideoTransformerBase):
    def __init__(self):
        self._last_frame = None

    def transform(self, frame):
        self._last_frame = frame.to_ndarray(format="bgr24")
        return self._last_frame

def save_image_locally(frame):
    filename = "captured_image.jpg"
    cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    st.success(f"Image saved as {filename}")
    st.session_state.stage =2
    st.rerun()

def load_camera():
    # webrtc_ctx = webrtc_streamer(
    #     key="example",
    #     video_transformer_factory=VideoTransformer,
    #     async_transform=True,
    # )
    webrtc_ctx = webrtc_streamer(
        key="arinspector",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration={  # Add this config
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        },
        video_transformer_factory=VideoTransformer,
        #video_frame_callback=video_frame_callback,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )
    if webrtc_ctx.video_transformer:
        if st.button("Capture Image"):
            captured_image = webrtc_ctx.video_transformer._last_frame
            save_image_locally(captured_image)

def merge_images(background_image, foreground_image, x_offset, y_offset, resize):
    # Open the background image
    background = Image.open(background_image)

    # Open the transparent PNG image
    foreground = Image.open(foreground_image)

    # Resize the PNG image if necessary
    if resize:
        foreground = foreground.resize((foreground.width // 2, foreground.height // 2))

    # Create a new image with the same size as the background image
    merged_image = Image.new("RGBA", background.size)

    # Paste the background onto the new image
    merged_image.paste(background, (0, 0))

    # Paste the PNG image onto the new image with transparency
    merged_image.paste(foreground, (x_offset, y_offset), mask=foreground)

    return merged_image

# Function to save content to content.py
def save_content(new_content):
    try:
        with open("prompts.py", "w") as file:
            file.write(new_content)
    except:
        print("Error")

def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def main():
    # for storing the details in session state(local storage)
    if "logged_in" not in st.session_state:
        st.session_state.logged_in=False
    if "app_title" not in st.session_state:
        st.session_state.app_title=""
    if "gpt_model" not in st.session_state:
        st.session_state.gpt_model=""
    if "output_filename" not in st.session_state:
        st.session_state.output_filename=""
    if "api_key" not in st.session_state:
        load_config_value()
    if "prompt" not in st.session_state:
        st.session_state.prompt=PROMPT_TEXT

    st.markdown(hide_menu,unsafe_allow_html=True)
    st.title(st.session_state.app_title)
    st.sidebar.title("Authentication")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if authenticate(username, password):
            st.session_state.logged_in = True
        else:
            st.session_state.logged_in= False
            st.error("Invaid user")   

    if username == "admin" and st.session_state.logged_in == True:
        print("admin")
        updated_content = st.sidebar.text_area("Prompt:",value=st.session_state.prompt,key="textarea",height=200)
        st.session_state.prompt = updated_content
        if st.sidebar.button("UpdatePrompt"): 
            print("update clicked")
            new_content='PROMPT_TEXT = """'+updated_content+'"""'
            st.session_state.prompt = updated_content
            save_content(new_content)
            st.sidebar.success("Content saved successfully!")
            #return        
    elif st.session_state.logged_in == True:
        print("user")        
    if st.session_state.logged_in == True:    
        if "stage" not in st.session_state:
            st.session_state.stage =1
        
        match st.session_state.stage:
            case 1:
                st.title("Camera Capture")
                load_camera()
                # uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    
                # if uploaded_file is not None:
                #     image = Image.open(uploaded_file)
                #     st.image(image, caption="Uploaded Image", use_column_width=True)
                    
                #     base64_str = image_to_base64(image)
                #     api_call(base64_str)
                    #st.write("Base64 Representation:")
                    #st.write(base64_str)
            case 2:
                st.title("Image Analyse")         
                draw_on_image("captured_image.jpg","canva")

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def api_call(): # for calling Chatgpt 4

    # OpenAI API Key
    api_key = st.session_state.api_key
    # Path to your image
    image_path = "final.jpg"

    # Getting the base64 string
    base64_image = encode_image(image_path)

    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
    }

    payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": PROMPT_TEXT
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    content = response.json()
    #print(content['choices'][0]['message']['content'])
    content = response.json()
    #print(content['choices'][0]['message']['content'])
    assistant_response = content['choices'][0]['message']['content']
    print(assistant_response)
    st.markdown(assistant_response)
 
def api_call_upload(base64_image): # for calling Chatgpt 4

    # OpenAI API Key
    api_key = st.session_state.api_key

    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
    }

    payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": PROMPT_TEXT
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    content = response.json()
    #print(content['choices'][0]['message']['content'])
    assistant_response = content['choices'][0]['message']['content']
    print(assistant_response)
    st.markdown(assistant_response)
 
    
def save_canvas_as_png(canva_result,file_path):
    # Convert NumPy array to PIL Image
    drawn_image_pil = Image.fromarray(canva_result)
    drawn_image_pil = drawn_image_pil.resize((640, 480))
    # Save the drawn image as PNG
    drawn_image_pil.save(file_path)

def draw_on_image(image_file,name):
    captured_frame = Image.open(image_file)
    
    col1, col2 = st.columns(2)
    with col1:
        drawing_mode = 'freedraw' #st.selectbox('Draw',('rect','point','freedraw'))
    with col2:
        stroke_color = 'rgb(0, 0, 255)' #st.color_picker('Stroke Color HEX: ')
    # #RGBimg = st.file_uploader('Select Image', type=['png','jpg'], key='dset_fu1', accept_multiple_files=False)
    fill_color = 'rgba(255,165,0,0.3)'
    canvas_result = st_canvas(fill_color=fill_color, stroke_width=3, stroke_color=stroke_color, background_color='#000000', background_image=captured_frame if captured_frame else None, update_streamlit=True, height=400, drawing_mode=drawing_mode, point_display_radius = 5 if drawing_mode=='point' else 0, key='canvas')
    
    if st.button("Analyse"):
        # Merge drawing with the captured image
        if canvas_result.image_data is not None:
            save_canvas_as_png(canvas_result.image_data,"canva.png")
            final_output= merge_images("captured_image.jpg","canva.png",0,0,False)
            final_output = final_output.convert("RGB")

            # Save as JPEG
            final_output.save("final.jpg")
            #st.image(final_output)
            api_call()


    #st.stop()
if __name__ == "__main__":
    main()


