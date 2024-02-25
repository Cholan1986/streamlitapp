import streamlit as st
import requests
from datetime import datetime,timedelta

#Error message from flowise
cqa_senario_invalid_response="Could you please provide more"
stockholder_invalid_response="Could you please select a stakeholder from the given list"


#Task Details
task_create_api_URL="https://services.magiqspark.com/api/system/tasks/create?token=rekraps"
task_name="Do CQA"
task_title=""
task_description=""
task_type="CQA"
task_assignee_type="User"
task_assigned_to=""
task_expires_at=""
task_assigned_by="Kumaran(CQA Bot)"

def update_task_details(): #Append task details to share it to the sparker app as task description
    task_desc="CQA senariou:"+st.session_state.cqa_senario+"\n"
    #task_desc+="stockholder:"+st.session_state.stockholder+"\n"
    description_content= st.session_state.conversation_history
    description_content=str(description_content).replace('"',"'")
    print(description_content)
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
    print(st.session_state.user_name+"---"+st.session_state.user_id)
    return True

def calling_flowise_api(question):
    api_response=""
    #st.session_state.waiting_for_input = True
    url = 'https://ai-dev.magiqspark.com/api/v1/prediction/5a9b8a7b-0558-4d86-bc24-8e110187f673'
    body = {
        "question": question 
    }
    response = requests.post(url, json=body)
    if response.status_code == 200:
        #st.session_state.waiting_for_input = False
        return response.json()
    else:
        #st.session_state.waiting_for_input = False
        return "Error with accessing the server. Please contact your mentor"
    
def validate_stockholder_selection(response,user_data):
    output=response.find(user_data)
    #print(output)
    return output
def step_1(): #welcome message and video screen
    #print("step_1")
    st.title("TinyMagiq CQA Bot Sample")
    st.markdown("---")
    conversation_history_placeholder = st.empty()
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
        # Proceed with next step
        st.write("No user input...")
        st.session_state.stage =2
        st.rerun()
    return True
def step_2(): #Getting Senario from the user
    #print("step_2")
    st.title("TinyMagiq CQA Bot Sample")
    st.markdown("---")
    conversation_history_placeholder = st.empty()
    st.subheader("What scenario do you need help with to get questions?")
    #conversation_history = conversation_history_placeholder.text_area("CQA Bot:", value="What scenario do you need help with to get questions?", height=50,disabled=True)
    col1,col2 = st.columns([9,1])
    user_input = col1.text_input("You:"," ")
    st.session_state.cqa_senario = user_input
    col2.write("")
    if col2.button("Send"):
        if user_input.strip() != "":
            api_response=calling_flowise_api(st.session_state.cqa_senario+"Who are stakeholders")
            if(api_response!="Error with accessing the server. Please contact your mentor"):
                st.session_state.stockholder_option=api_response
                st.session_state.stage=3
            else:
                print(api_response)
            st.session_state.conversation_history = api_response# += f"Bot: {api_response}\n"
            st.rerun()
    return True

def step_3(): #getting Stockholder from the user
    #print("step_3")
    st.title("TinyMagiq CQA Bot Sample")
    st.markdown("---")
    
    st.markdown(st.session_state.stockholder_option, unsafe_allow_html=True)
    col1,col2 = st.columns([9,1])
    # Text input for user to type messages
    user_input = col1.text_input("You:","")
    col2.write("")
    
    if col2.button(" Send"):
        if user_input.strip() != "":
            check= validate_stockholder_selection(st.session_state.conversation_history,user_input)
            st.success(check)
            if(check == -1):
                st.success("Please select the valid stockholder")
                return True
            st.session_state.stockholder = user_input
            st.session_state.stage=4
            st.rerun()
    return True
def step_4(): #Getting Question Type from the user
    #print("step_4")
    st.title("TinyMagiq CQA Bot Sample")
    st.markdown("---")
    st.session_state.question_type=st.radio("What type of question do you want to ask?  ",["Data","Thoughts","Feeling"])
    col1,col2 = st.columns([3,7])
    col2.write("")
    if col2.button("Proceed"):
        final_question= "Generate 5 "+ st.session_state.question_type +" question for"+ st.session_state.stockholder
        api_response=calling_flowise_api(final_question)
        st.success(api_response)
        if(api_response!="Error with accessing the server. Please contact your mentor"):
            st.session_state.stage=5
            #st.session_state.conversation_history += f"You: {user_input}\n"
            st.session_state.conversation_history = api_response# += f"Bot: {api_response}\n"          
            st.rerun()
    return True
def step_5(): #Show the result and Exit
    #print("step_5")
    st.title("TinyMagiq CQA Bot Sample")
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
    #print("step_6")
    match st.session_state.next_action_item:
        case "More Questions Of The Above":
            more_question()
            return True
        case "Question Of Another Type":
            st.session_state.stage=4
            st.rerun()
            return True
        case "I want to try with another stakeholder":
            st.session_state.stage=3
            st.rerun()
            return True
        case "I am clear. Thanks":
            get_query_parameters()
            create_task();
            all_the_best()
            
            return True
    return True
def more_question(): #getting more question
    final_question= "Generate 5 "+ st.session_state.question_type +" question for"+ st.session_state.stockholder
    api_response=calling_flowise_api(final_question)
    if(api_response!="Error with accessing the server. Please contact your mentor"):
        st.session_state.stage=5
        st.session_state.conversation_history = api_response# += f"Bot: {api_response}\n"          
        st.rerun()
    return True
def all_the_best(): #GoodBuy screen
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
    task_final_url=task_create_api_URL #+"&name="+task_name+"&title="+task_title+"&description="+update_task_details()+"&type="+task_type+"&assignee_type="+task_assignee_type+"&assigned_to="+task_assigned_to+"&expires_at="+get_current_date()+"&assigned_by="+task_assigned_by
    #print(data)
    response = requests.post(task_create_api_URL,data)
    if response.status_code == 200:
        st.session_state.waiting_for_input = False
        st.success(response.json())
        return response.json()
    else:
        st.success("Error creating task")
        st.session_state.waiting_for_input = False
        return "Error with accessing the server. Please contact your mentor"
    return True
# Define the Streamlit UI layout
def main():
    get_query_parameters() # get the user id and name from the URL
    
    # for storing the details in session state(local storage)
    if "cqa_senario" not in st.session_state:
        st.session_state.cqa_senario=""
    if "stockholder" not in st.session_state:
        st.session_state.stockholder=""
    if "stockholder_option" not in st.session_state:
        st.session_state.stockholder_option=""
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
        
    # if(st.session_state.stage==2):
    #     stage_2()
    # if(st.session_state.stage==3):
    #     stage_3()
    # if(st.session_state.stage==4):
    #     stage_4()
    # if(st.session_state.stage==5):
    #     stage_5()  
        
# Run the Streamlit app
if __name__ == "__main__":
    main()
