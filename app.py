import streamlit as st
import requests
from datetime import datetime,timedelta
import openai
import json
import re
import os

hide_menu="""
<style>
#MainMenu {
    visibility:hidden;
}

</style>
"""


#Task Details
task_create_api_URL= ""
task_name="Do CQA"
task_title=""
task_description=""
task_type="CQA"
task_assignee_type="User"
task_assigned_to=""
task_expires_at=""
task_assigned_by="Kumaran(CQA Bot)"

def remove_markdown(text):
    # Remove bold markdown (e.g., **text**)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Remove italic markdown (e.g., *text*)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # Remove bullet points markdown (e.g., 1. text)
    #text = re.sub(r'\d+\.\s+', '', text)
    return text

def load_config_value():
    # Load JSON file
    with open('config.json', 'r') as f:
        config = json.load(f)
    st.session_state.app_title= config.get('title')
    st.session_state.api_key= os.environ.get('api_key')
    st.session_state.cqa_prompt=config.get('cqa_prompt')
    st.session_state.gpt_model=config.get('gpt_model')
    st.session_state.create_task_url=config.get('create_task_url')
    return True
def open_ai_api(prompts):
    completion = openai.ChatCompletion.create(
    # Use GPT 3.5 as the LLM
    model=st.session_state.gpt_model,
    # Pre-define conversation messages for the possible roles
    messages=[
        {"role":"system","content":st.session_state.cqa_prompt},
    #    {"role": "user", "content": prompts}
    ]
    )
    #print(completion)
    return completion.choices[0].message.content

def update_task_details(): #Append task details to share it to the sparker app as task description
    task_desc="CQA senariou:"+st.session_state.cqa_senario+"\n"
    description_content= st.session_state.conversation_history
    description_content=str(description_content).replace('"',"'")
    task_desc+="Questions:"+ description_content
    return task_desc
def get_current_date(): # get the current date and add 4 days to calculate the expire date
    # Get current date
    current_date = datetime.now().date()
    # Add 4 days to the current date
    result_date = current_date + timedelta(days=4)
    formatted_date = result_date.strftime("%Y-%m-%d")
    return formatted_date

def get_query_parameters(): #get the user id and user name from URL
    query_params = st.query_params
    st.session_state.user_id = query_params.get("id")
    st.session_state.user_name = query_params.get("name")
    return True
   
def validate_stackholder_selection(response,user_data):  
    output=response.find(user_data)
    return output
  
def step_1(): #welcome message and video screen
    st.title(st.session_state.app_title)
    st.markdown("---")
    st.write("Hi I am your CQA Agent")
    st.video("cqa_video.mp4","video/mp4")
    st.write("Saw the video? Shall we proceed?")
    col1,col2,col3 = st.columns([2,2,6])     
    if col1.button("Yes"):
        # Proceed with next step
        st.write("Yes user input...")
        st.session_state.stage =2
        st.rerun()
    if col2.button("No"):
        # Show message to them to watch the video 
        st.success("Ok.. Please watch the video. once you are done. click 'Yes' to proceed with CQA")
    return True
def step_2(): #Getting Senario from the user
    st.title("TinyMagiq CQA Bot Sample")
    st.markdown("---")
    st.subheader("What scenario do you need help with to get questions?")
    
    col1,col2 = st.columns([9,1])
    user_input = col1.text_input("You:"," ",label_visibility="collapsed")
    st.session_state.cqa_senario = user_input
    if col2.button("Send"):
        if user_input.strip() != "":
            api_response=open_ai_api(st.session_state.cqa_senario+"Who are stakeholders")
            if(api_response!="Error with accessing the server. Please contact your mentor"):
                st.session_state.stage=3
                #st.session_state.conversation_history = api_response
                st.session_state.stackholder_option=api_response
                st.rerun()
            # else:
            #     print(api_response)   
    return True

def step_3(): #getting stackholder from the user
    st.title("TinyMagiq CQA Bot Sample")
    st.markdown("---")    
    st.subheader("Please select the stack holder:")
    cleaned_text = remove_markdown(st.session_state.stackholder_option)
    #print(cleaned_text)
    parsed_mappings = parse_input_content(cleaned_text)
            
    selected_stakeholder = st.radio(" ", list(parsed_mappings.values()))

    if selected_stakeholder:
        for key, value in parsed_mappings.items():
            if value == selected_stakeholder:
                st.session_state.stackholder = value
                #st.write("Selected Stakeholder:", key)
                #st.write("Description:", value)
    
    col1,col2 = st.columns([3,7])
    if col2.button(" Send"):
        st.session_state.stage=4
        st.rerun()
    return True
def step_4(): #Getting Question Type from the user
    st.title(st.session_state.app_title)
    st.markdown("---")
    st.session_state.question_type=st.radio("What type of question do you want to ask?  ",["Data","Thoughts","Feeling"])
    col1,col2 = st.columns([3,7])
    if col2.button("Proceed"):
        final_question= "Generate 5 '"+ st.session_state.question_type +"' question for '"+ st.session_state.stackholder+"' for senario '"+ st.session_state.cqa_senario+"'"
        print(final_question)
        api_response=open_ai_api(final_question)
        if(api_response!="Error with accessing the server. Please contact your mentor"):
            st.session_state.stage=5
            st.session_state.conversation_history = api_response         
            st.rerun()
    return True
def step_5(): #Show the result and Exit
    st.title(st.session_state.app_title)
    st.markdown("---")
    st.markdown(st.session_state.conversation_history, unsafe_allow_html=True)
    st.session_state.next_action_item=st.radio("Are you comfortable with a question to ask?",["More Questions Of The Above","Question Of Another Type","I want to try with another stakeholder","I am clear. Thanks"])
    col1,col2 = st.columns([3,7])
    col2.write("")
    if col2.button("Proceed"):
        st.session_state.stage=6
        st.rerun();
    return True
def step_6(): #Next action item?
    match st.session_state.next_action_item:
        case "More Questions Of The Above":
            more_question()
            st.session_state.next_action_item = "Completed"
            return True
        case "Question Of Another Type":
            st.session_state.stage=4
            st.session_state.next_action_item = "Completed"
            st.rerun()
            return True
        case "I want to try with another stakeholder":
            st.session_state.stage=3
            st.session_state.next_action_item = "Completed"
            st.rerun()
            return True
        case "I am clear. Thanks":
            get_query_parameters()
            create_task();
            st.session_state.next_action_item = "all the best"
            all_the_best()
            return True
        case "all the best":
            all_the_best()
            return True
    return True
def more_question(): #getting more question
    final_question= "Generate 5 '"+ st.session_state.question_type +"' question for '"+ st.session_state.stackholder+"' for senario '"+ st.session_state.cqa_senario+"'"
    print(final_question)
    api_response=open_ai_api(final_question)
    if(api_response!="Error with accessing the server. Please contact your mentor"):
        st.session_state.stage=5
        st.session_state.conversation_history = api_response          
        st.rerun()
    return True
def all_the_best(): #GoodBye screen
    st.title("TinyMagiq CQA Bot Sample")
    st.markdown("---")
    st.markdown("*All the best practicing CQA*", unsafe_allow_html=True)
    st.balloons()
    col1,col2 = st.columns([3,7])
    col2.write("")
    if col2.button(" Proceed "):
        st.session_state.stage=1;
        st.rerun()
          
    return True
def create_task(): #create task in the spearker environment
    task_title="CQA:"+st.session_state.cqa_senario
    data = {
    "name": "Do CQA",
    "title": ""+task_title+"",
    "description": ""+update_task_details()+"",
    "type": "simple",
    "assignee_type": "user",
    "assigned_to": ""+st.session_state.user_id+"",
    "expires_at": ""+get_current_date()+"",
    "assigned_by": ""+st.session_state.user_name+""
    }
    response = requests.post(st.session_state.create_task_url,data)
    if response.status_code == 200:
        st.session_state.waiting_for_input = False
        st.success(response.json())
        return response.json()
    else:
        st.success("Error creating task")
        st.session_state.waiting_for_input = False
        return "Error with accessing the server. Please contact your mentor"
    return True
def parse_input_content(content): #for mapping the stackholders response from the openai
    lines = content.split('\n')
    mappings = {}
    stakeholders_started = True
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if stakeholders_started:
            parts = line.split('. ')
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                mappings[key] = value
    return mappings
def get_selection_from_input(user_input, mappings): #For validating stackholder selection
    return mappings.get(user_input.lower(), "Invalid selection")

# Define the Streamlit UI layout
def main():
    st.markdown(hide_menu,unsafe_allow_html=True)

    #get_query_parameters() # get the user id and name from the URL
    
    # for storing the details in session state(local storage)
    if "cqa_senario" not in st.session_state:
        st.session_state.cqa_senario=""
    if "stackholder" not in st.session_state:
        st.session_state.stackholder=""
    if "stackholder_option" not in st.session_state:
        st.session_state.stackholder_option=""
    if "question_type" not in st.session_state:
        st.session_state.question_type=""
    if "stage" not in st.session_state:
        st.session_state.stage =1
    if "user_id" not in st.session_state:
        st.session_state.user_id =1
    if "user_name" not in st.session_state:
        st.session_state.user_name =1
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = ""
    if "waiting_for_input" not in st.session_state:
        st.session_state.waiting_for_input = False
    if "next_action_item" not in st.session_state:
        st.session_state.next_action_item=""
    if "app_title" not in st.session_state:
        st.session_state.app_title=""
    if "gpt_model" not in st.session_state:
        st.session_state.gpt_model=""
    if "create_task_url" not in st.session_state:
        st.session_state.create_task_url=""
    if "cqa_prompt" not in st.session_state:
        st.session_state.cqa_prompt=""
    
    if "api_key" not in st.session_state:
        load_config_value()
    openai.api_key = st.session_state.api_key
    match st.session_state.stage:
        case 1:
             step_1()
        case 2:
             step_2()
        case 3:
             step_3()
        case 4:
             step_4()
        case 5:
             step_5()
        case 6:
             step_6()
        
       
# Run the Streamlit app
if __name__ == "__main__":
    main()
