import datetime
import traceback
import random
from datetime import datetime 
from datetime import datetime, timezone, timedelta
from fasthtml.svg import Svg, Path, Rect, Text, NotStr, Ellipse, Circle
from fasthtml.svg import G  # type: ignore
from fasthtml.common import *
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from pathlib import Path
import json
from services.sb_user_services import fetch_user_profile # Assuming this path is correct relative to your project structure
from services.system_messages import AKASI_SYSTEM_MESSAGE_CONTENT, BODY_SCANNER_SYSTEM_MESSAGE_CONTENT, WELLNESS_JOURNAL_SYSTEM_MESSAGE_TEMPLATE
from fasthtml.core import RedirectResponse
import re
import asyncio
import time
import urllib.parse
from starlette.datastructures import UploadFile
import base64
from langchain.chat_models import init_chat_model
from typing import Annotated, List, Any, cast
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.graph import MessagesState
from langchain_core.tools import tool
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
)
from typing import Annotated, Literal
from langgraph.checkpoint.memory import MemorySaver
from typing import Union




# --- Configuration ---
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(os.path.join(BASE_DIR, '.env'))


supabase_url = os.getenv("SUPABASE_URL_NEW")
supabase_anon_key = os.getenv("SUPABASE_ANON_KEY_NEW")


if not supabase_url or not supabase_anon_key:
    raise ValueError("Missing required Supabase environment variables")

supabase: Client = create_client(supabase_url, supabase_anon_key)

# --- Global Store for Pending Journal Updates ---
pending_journal_updates: List[dict] = []
pending_journal_updates_2: List[dict] = []

# Define Manila timezone (UTC+8)
manila_timezone = timezone(timedelta(hours=8))
current_date_manila_iso = datetime.now(manila_timezone).isoformat()




def use_auth_context(access_token, refresh_token=None):
    """Set authentication context on the global client for the current request"""
    # Create a new instance with authentication context
    client = supabase
    
    # Set the session with the token
    client.auth.set_session(access_token, refresh_token or "")
    
    return client

# --- Authentication Beforeware ---
def auth_before(req, sess):
    auth = req.scope['auth'] = sess.get('user', None)
    if not auth and req.url.path == '/home':
        return RedirectResponse('/login', status_code=303)

beforeware = Beforeware(
    auth_before,
    skip=[r'/favicon\.ico', r'/htmx/.*', r'/static/.*', r'.*\.css', r'.*\.js', '/login', '/signup', '/']
)

# --- Initialize FastHTML App ---
app, rt = fast_app(
    before=beforeware,
    pico=False,  # Enable PicoCSS
    debug=True,
    static_path='static',
    hdrs=(
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@5"), 
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        # Link(rel='stylesheet', href='/css/custom.css'),  # Keep custom CSS if needed        
    ),
    bodykw={'class': 'bg-base-200'},

)







# --- Routes ---


# This link will be used in the route
wellness_journal_css_link = Link(rel='stylesheet', href='/css/wellness_journal.css')
google_material_icons_link = Link(href="https://fonts.googleapis.com/icon?family=Material+Icons", rel="stylesheet")
wellness_enhancements_js_link = Script(src="/js/wellness_enhancements.js", defer=True)


# Raw SVG string for the filter definition (from fasthtml_raw_scan_line_add_py)
scan_line_svg_defs_raw_string = """
<defs>
  <filter id="scanGlowGreenAnimation">
    <feGaussianBlur stdDeviation="1.2" result="coloredBlur"/>
    <feMerge>
      <feMergeNode in="coloredBlur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
</defs>
"""

# Raw SVG string for the scan line group itself
scan_line_group_raw_string = """
<g id="scanLineAnimationGroupRaw" style="display: none;">
  <line id="scanLineAnimationElementRaw" x1="10" y1="0" x2="90" y2="0" stroke="#10B981" stroke-width="2" stroke-opacity="0.8" filter="url(#scanGlowGreenAnimation)" stroke-dasharray="5 3">
    <animate attributeName="strokeOpacity" values="0.8;0.3;0.8" dur="1.2s" repeatCount="indefinite" />
  </line>
  <rect id="scanLineHighlightAnimationElementRaw" x="10" y="-2.5" width="80" height="5" fill="#10B981" opacity="0.15" filter="url(#scanGlowGreenAnimation)" />
</g>
"""

# --- Main Body SVG FT Component ---
# This function will create the main annotated SVG body using FastHTML components
def create_main_anatomy_svg():
    # Define default styles for clarity and to ensure they are applied
    default_body_fill = "#97979795"  # Light grey for external parts
    default_body_stroke = "#333333" # Dark grey/black outline
    default_stroke_width = "1px"

    internal_organ_fill = "#e57373" # Reddish for lungs
    internal_organ_stroke = "#c62828" # Darker red stroke for lungs
    internal_organ_fill_opacity = "0.7"

    heart_fill = "#d32f2f" # Specific deep red for heart
    heart_stroke = internal_organ_stroke # Consistent stroke with other internal organs

    return Svg(
        G( # Head
            Ellipse(cx=100, cy=40, rx="35", ry="30", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="head_group", cls="body-part", data_name="Head", data_info="The head contains the brain, eyes, ears, nose, and mouth. It is crucial for sensory input and cognitive functions."
        ),
        G( # Neck
            Rect(x=90, y=70, width="20", height="15", rx="2", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="neck_group", cls="body-part", data_name="Neck", data_info="The neck connects the head to the torso and houses the cervical spine, esophagus, and trachea."
        ),
        G( # Thorax
            Rect(x=60, y=85, width="80", height="75", rx="10", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="thorax_group", cls="body-part", data_name="Thorax (Chest)", data_info="The thorax, or chest, is the part of the torso between the neck and the abdomen. It houses the heart and lungs."
        ),
        G( # Lungs
            Ellipse(cx=85, cy=115, rx="18", ry="25", fill=internal_organ_fill, stroke=internal_organ_stroke, stroke_width=default_stroke_width, fill_opacity=internal_organ_fill_opacity),
            Ellipse(cx=115, cy=115, rx="18", ry="25", fill=internal_organ_fill, stroke=internal_organ_stroke, stroke_width=default_stroke_width, fill_opacity=internal_organ_fill_opacity),
            id="lungs_group", cls="body-part internal-organ", data_name="Lungs", data_info="The lungs are the primary organs of the respiratory system, responsible for oxygenating blood."
        ),
        G( # Heart
            Ellipse(cx=100, cy=120, rx="15", ry="15", style=f"fill: {heart_fill};", stroke=heart_stroke, stroke_width=default_stroke_width, fill_opacity=internal_organ_fill_opacity), # Retain specific heart fill, add stroke
            id="heart_group", cls="body-part internal-organ", data_name="Heart", data_info="The heart is a muscular organ that pumps blood throughout the body via the circulatory system."
        ),
        G( # Abdominal and Pelvic Region
            Rect(x=60, y=160, width="80", height="60", rx="10", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="abdominal_pelvic_region_group", cls="body-part", data_name="Abdominal and Pelvic Region", data_info="This region includes the abdomen and pelvis. It houses major organs of the digestive, urinary, and reproductive systems (e.g., stomach, intestines, liver, kidneys, bladder, reproductive organs)."
        ),
        G( # Left Shoulder
            Circle(cx=60, cy=95, r="12", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="left_shoulder_group", cls="body-part", data_name="Left Shoulder", data_info="The left shoulder joint connects the left arm to the torso."
        ),
        G( # Right Shoulder
            Circle(cx=140, cy=95, r="12", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="right_shoulder_group", cls="body-part", data_name="Right Shoulder", data_info="The right shoulder joint connects the right arm to the torso."
        ),
        G( # Left Arm
            Rect(x=25, y=95, width="30", height="70", rx="5", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="left_arm_group", cls="body-part", data_name="Left Arm", data_info="The left arm is used for reaching, grasping, and interacting with the environment."
        ),
        G( # Right Arm
            Rect(x=145, y=95, width="30", height="70", rx="5", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="right_arm_group", cls="body-part", data_name="Right Arm", data_info="The right arm, similar to the left, facilitates interaction and manipulation of objects."
        ),
        G( # Left Hand
            Ellipse(cx=40, cy=170, rx="12", ry="8", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="left_hand_group", cls="body-part", data_name="Left Hand", data_info="The left hand is at the end of the left arm, used for manipulation."
        ),
        G( # Right Hand
            Ellipse(cx=160, cy=170, rx="12", ry="8", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="right_hand_group", cls="body-part", data_name="Right Hand", data_info="The right hand is at the end of the right arm, used for manipulation."
        ),
        G( # Left Leg
            Rect(x=70, y=220, width="25", height="70", rx="5", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="left_leg_group", cls="body-part", data_name="Left Leg", data_info="The left leg supports the body and enables locomotion."
        ),
        G( # Right Leg
            Rect(x=105, y=220, width="25", height="70", rx="5", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="right_leg_group", cls="body-part", data_name="Right Leg", data_info="The right leg provides support and mobility."
        ),
        G( # Left Foot
            Ellipse(cx=83, cy=295, rx="15", ry="8", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="left_foot_group", cls="body-part", data_name="Left Foot", data_info="The left foot is at the end of the left leg, crucial for standing and walking."
        ),
        G( # Right Foot
            Ellipse(cx=118, cy=295, rx="15", ry="8", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="right_foot_group", cls="body-part", data_name="Right Foot", data_info="The right foot is at the end of the right leg, crucial for standing and walking."
        ),
        # Main SVG attributes
        id="mainAnatomySvgFT", 
        viewBox="0 -70 200 450", # viewBox adjusted for centering
        xmlns="http://www.w3.org/2000/svg",
        cls="object-contain w-full h-full p-2", 
        style="position: relative; z-index: 2; background-color: #f8fafc; border: 1px solid #e2e8f0;" 
    )
main_anatomy_svg_ft = create_main_anatomy_svg()


pre_configured_conversation_history = [
    'Human Message: "I\'ve had a sore throat for 3 days."',
    'AI Message: "Do you also have a fever or cough?"',
    'Human Message: "Yes, I have a mild fever but no cough."',
    'AI Message: "Are you experiencing any difficulty swallowing or swollen glands?"',
    'Human Message: "Swallowing is painful, and my neck feels tender."',
    'AI Message: "It may be a throat infection; I recommend seeing a doctor for a throat swab."'
]

# Body scanner action commands list
body_scanner_action_commands_list = [
    "START_SCAN", "STOP_SCAN", "Head", "Neck", "Thorax", "Lungs", "Heart", "idle"
    "Abdominal and Pelvic Region", "Left Shoulder", "Right Shoulder",
    "Left Arm", "Right Arm", "Left Hand", "Right Hand", "Left Leg",
    "Right Leg", "Left Foot", "Right Foot", "FULL_BODY_GLOW"
]




async def process_files_to_base64_list(files: list[UploadFile]) -> list[dict]:
    # (This function remains the same as provided in the previous correct answer)
    # It takes a list of UploadFile objects, reads them, converts to Base64,
    # and returns a list of dicts with filename, content_type, size, base64.
    # Ensure it handles potential errors and closes files.
    processed_attachments = []
    if not files:
        return processed_attachments
    
    for file_upload in files:
        if file_upload and file_upload.filename and isinstance(file_upload, UploadFile):
            try:
                contents = await file_upload.read()
                encoded_string = base64.b64encode(contents).decode('utf-8')
                processed_attachments.append({
                    "filename": file_upload.filename,
                    "content_type": file_upload.content_type,
                    "size": file_upload.size,
                    "base64": encoded_string
                })
                await file_upload.close()
            except Exception as e:
                print(f"Error processing file {getattr(file_upload, 'filename', 'unknown')}: {e}")
                processed_attachments.append({
                    "filename": getattr(file_upload, 'filename', 'unknown_error_file'),
                    "error": str(e)
                })
        else:
            print(f"Skipping invalid file object: {file_upload}") # Log if not an UploadFile
    return processed_attachments


# --- 🟣🟣🟣🟣 BUILDING THE LLM AGENT 1 🟣🟣🟣🟣 --- 
# Create an AI agent that has image tool that inteprets the message gets the data then gives it to the agent
# Then add a workflow to the agent so that you can control the body scanner
model_1_claude_haiku = "anthropic.claude-3-haiku-20240307-v1:0"
model_2_claude_3_5_sonnet =  "anthropic.claude-3-5-sonnet-20240620-v1:0"
model_2_claude_3_5_sonnet_v2 =  "anthropic.claude-3-5-sonnet-20241022-v2:0"


llm = init_chat_model(
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    model_provider="bedrock_converse",
    region_name='us-west-2',
    temperature = 0.1,
)


class MedicalAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    input_base64_images: Optional[List[dict]]
    body_scanner_command: str | None


graph_builder = StateGraph(MedicalAgentState)

memory = MemorySaver()

# Tool definition
@tool
def summarize_medical_images_tool_interface(images: List[dict]) -> str:
    """
    Analyzes and summarizes a list of provided medical images (e.g., X-rays, MRIs)
    by making an internal LLM call.
    This tool is invoked by the system when images are available in the current context
    and a summary is requested. The list of base64 encoded images is provided as an argument.
    """
    if not images:
        return "Error: No images were provided to summarize."
    

    # 1. Construct the multimodal message content parts for the internal LLM call
    message_content_parts = []
    for image_detail_dict in images:
        b64_image_data = image_detail_dict.get("data")
        media_type = image_detail_dict.get("media_type", "image/jpeg") 

        if not b64_image_data:
            print("Warning: An image item was missing base64 data in summarize_medical_images_tool_interface.")
            continue

        message_content_parts.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type, 
                "data": b64_image_data,
            },
        })
    

    if not message_content_parts:
        return "Error: No valid image data found to summarize after processing input."



    
    summarization_prompt_text = (
        "Based on the following medical image(s), provide a concise summary or medical report. "
        "Focus on observable features and avoid making diagnoses if not explicitly qualified to do so."
    )

    message_content_parts.append({"type": "text", "text": summarization_prompt_text})

    

    # 2. Create the System and Human messages for the LLM call
    summarization_system_prompt = SystemMessage(
        content=(
            "You are an expert medical image analyst. Your task is to provide a concise summary "
            "or medical report based on the provided image(s) and the user's request "
            "as conveyed in the text part of the message."
        )
    )
    summarization_human_message = HumanMessage(content=message_content_parts)

    try:
        print(f"Tool invoking LLM for summarization with {len(message_content_parts) -1} image(s).")
        response = llm.invoke([summarization_system_prompt, summarization_human_message])
        
        if isinstance(response, AIMessage) and response.content:
            print(f"Tool's LLM summarization successful. Summary: {response.content[:100]}...")
            return str(response.content)
        else:
            print(f"Tool's LLM summarization did not return expected AIMessage. Response: {response}")
            return "Error: Could not generate a summary from the LLM within the tool."
            
    except Exception as e:
        print(f"Error during LLM-based image summarization within tool: {e}")
        return f"Error summarizing images within tool: {str(e)}"


tools = [summarize_medical_images_tool_interface]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)


# --- Node Functions ---
def decide_action_node(state: MedicalAgentState):
    """
    The LLM decides whether to respond directly or call a tool.
    """
    print("\n--- Entered decide_action_node ---")
    
    akasi_system_message = SystemMessage(content=AKASI_SYSTEM_MESSAGE_CONTENT)
            
    messages_for_llm_invocation = [akasi_system_message] + state["messages"]
    
    print(f"Messages for LLM call in decide_action_node (first is Akasi persona): {[m.type for m in messages_for_llm_invocation]}")
    
    # Invoke the LLM with the Akasi persona and the rest of the conversation history
    response = llm_with_tools.invoke(messages_for_llm_invocation)
    
    print(f"LLM response type: {response.type}, Tool calls: {getattr(response, 'tool_calls', 'N/A')}")
    # The response (AIMessage) will be added to the state's message list by LangGraph's `add_messages`
    return {"messages": [response]}


def execute_tool_node(state: MedicalAgentState):
    """
    Executes the tool called by the LLM.
    """
    print("\n--- Entered execute_tool_node ---")
    tool_messages: List[ToolMessage] = []
    last_message = state["messages"][-1]

    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        print("No tool calls found in the last AI message.")
        return {} 

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        invoked_tool = tools_by_name.get(tool_name)

        print(f"Attempting to execute tool: {tool_name}")

        if not invoked_tool:
            observation = f"Error: Unknown tool '{tool_name}' called."
        elif tool_name == "summarize_medical_images_tool_interface":
            # This will be a List[dict] as per MedicalAgentState
            images_data_list_from_state = state.get("input_base64_images") 
            if images_data_list_from_state:

                tool_args_for_invoke = {"images": images_data_list_from_state}
                try:
                    print(f"Invoking '{tool_name}' with {len(images_data_list_from_state)} image items from state.")
                    observation = invoked_tool.invoke(tool_args_for_invoke)
                except Exception as e:
                    observation = f"Error invoking {tool_name}: {str(e)}"
                    print(f"Exception during tool invocation: {e}")
            else:
                observation = "Error: Tool 'summarize_medical_images_tool_interface' called, but no image data was found in the state."
        else:
            try:
                print(f"Invoking generic tool '{tool_name}' with args: {tool_call.get('args', {})}")
                observation = invoked_tool.invoke(tool_call.get("args", {}))
            except Exception as e:
                observation = f"Error invoking {tool_name}: {str(e)}"
                print(f"Exception during generic tool invocation: {e}")
        
        tool_messages.append(
            ToolMessage(content=str(observation), tool_call_id=tool_call["id"], name=tool_name)
        )
    print(f"Tool observation(s): {[str(tm.content)[:100] + '...' if tm.content else 'N/A' for tm in tool_messages]}")
    return {"messages": tool_messages}

# --- Conditional Edge Logic ---
def should_call_tool(state: MedicalAgentState):
    """
    Determines the next step based on whether the LLM decided to call a tool.
    """
    print("\n--- Entered should_call_tool ---")
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        print("Routing to execute_tool_node")
        return "execute_tool_node"
    print("Routing to END (or final response generation)")
    return END


# --- Graph Construction ---
graph_builder = StateGraph(MedicalAgentState)

graph_builder.add_node("decide_action_node", decide_action_node)
graph_builder.add_node("execute_tool_node", execute_tool_node)

graph_builder.set_entry_point("decide_action_node")

graph_builder.add_conditional_edges(
    "decide_action_node",
    should_call_tool,
    {
        "execute_tool_node": "execute_tool_node",
        END: END,
    },
)

graph_builder.add_edge("execute_tool_node", "decide_action_node")

graph_1 = graph_builder.compile(checkpointer=memory)

# --- 🟣🟣🟣🟣 BUILDING THE LLM AGENT 1 🟣🟣🟣🟣 --- 



# ---🔵🔵🔵🔵 Workflow 1 : BODY SCANNER COMMANDER  🔵🔵🔵🔵------- 
from pydantic import BaseModel, Field

graph_builder_2 = StateGraph(MedicalAgentState)

class BodyScannerCommand(BaseModel):
    """
    Represents the command to be sent to the body scanner animation system
    based on the ongoing conversation with the patient.
    """
    body_scanner_command: Literal["START_SCAN", "STOP_SCAN", "Head", "Neck", "Thorax", "Lungs", "Heart", "idle", "Abdominal and Pelvic Region", "Left Shoulder", "Right Shoulder", "Left Arm", "Right Arm", "Left Hand", "Right Hand", "Left Leg", "Right Leg", "Left Foot", "Right Foot", "FULL_BODY_GLOW"] = Field(
        ...,
        description="The chosen command for the body scanner animation. Must be one of the predefined commands."
    )




def body_scanner_commands(state: MedicalAgentState):
    print("\n--- Entered body_scanner_commands_node ---")
    conversation_history = state["messages"]
    if not conversation_history:
        print("Warning: No conversation history found for body scanner command generation.")
        return {"body_scanner_command": "idle"} # Default command

    # Ensure the LLM used here supports ainvoke and structured output
    body_scanner_commander_llm = llm.with_structured_output(BodyScannerCommand)
    
    system_prompt_content = BODY_SCANNER_SYSTEM_MESSAGE_CONTENT

    # Prepare messages for the commander LLM
    # The Bedrock Claude messages API expects a list of message dicts,
    # or LangChain BaseMessage objects.
    messages_for_commander_llm: List[BaseMessage] = [
        SystemMessage(content=system_prompt_content)
    ]
    # Append existing history (which are already BaseMessage objects)
    messages_for_commander_llm.extend(conversation_history)
    messages_for_commander_llm.append(
         HumanMessage(content="Based on the full conversation history provided, what is the single most appropriate body scanner command?")
    )
    
    try:
        result = body_scanner_commander_llm.invoke(messages_for_commander_llm)
        print(f"Body scanner commander LLM result type: {type(result)}")
        print(f"Body scanner commander LLM result: {result}")
        
        # Fix: Access the Pydantic model field directly
        if result and isinstance(result, BodyScannerCommand):
            command_to_set = result.body_scanner_command
        else:
            command_to_set = "idle"
            
        print(f"Body scanner commander LLM result: {command_to_set}")
        return {"body_scanner_command": command_to_set}
    except Exception as e:
        print(f"Error in body_scanner_commander_llm.invoke: {e}")
        return {"body_scanner_command": "idle"}


graph_builder_2.add_node("llm_body_ui_commander", body_scanner_commands)
graph_builder_2.add_edge(START, "llm_body_ui_commander")
graph_workflow_1 = graph_builder_2.compile()

# ---🔵🔵🔵🔵 Workflow 1 : BODY SCANNER COMMANDER  🔵🔵🔵🔵------- 






# --- ⚪⚪⚪⚪ Workflow 2 : JOURNAL ENTRY CONTROLLER  START  ⚪⚪⚪⚪ ------- 



system_prompt_content_wf_1 = WELLNESS_JOURNAL_SYSTEM_MESSAGE_TEMPLATE


system_prompt_content_wf_2 = system_prompt_content_wf_1.format(current_date_manila_iso=current_date_manila_iso)

class WellnessJournalOperation(BaseModel):
    """
    Represents a command to manage a patient's wellness journal entry.
    This command is derived from analyzing the conversation history between the patient
    and an AI assistant, as well as any existing wellness journal entries.
    It specifies whether to add a new entry, update an existing one, or remove one,
    along with the necessary details for the operation.
    """

    wellness_journal_entry_id: str = Field(
        ...,
        description=(
            "The unique identifier for the wellness journal entry. "
            "For 'ADD' operations, this should be a new, unique ID (e.g., if existing IDs are '1', '2', a new one could be '3'; if no entries exist, start with '1'). "
            "For 'UPDATE' or 'REMOVE' operations, this MUST exactly match the ID of an existing entry from the provided list."
        )
    )

    wellness_journal_title: str = Field(
        ...,
        description=(
            "A concise and descriptive title for the wellness journal entry. "
            "For 'ADD', create a new title reflecting the conversation's topic. "
            "For 'UPDATE', this can be the existing title or an updated one if the entry's focus has significantly changed. "
            "For 'REMOVE', this should be the title of the entry being removed."
        )
    )

    wellness_journal_current_summary: str = Field(
        ...,
        description=(
            "A 1 sentence short summary of the patient's current condition, symptoms, feelings, or relevant information for this journal entry, "
            "derived primarily from the latest relevant parts of the conversation. "
            "For 'ADD', this is a new summary. "
            "For 'UPDATE', this should reflect the most current information, potentially integrating or replacing the previous summary. "
            "For 'REMOVE', this can be the summary of the entry being removed or a placeholder like 'Entry removed'."
        )
    ) 

    wellness_journal_entry_action: Literal["ADD", "UPDATE", "REMOVE"] = Field(
        ...,
        description=(
            "The action to perform on the wellness journal entry. Must be one of 'ADD', 'UPDATE', or 'REMOVE'."
        )
    )

    wellness_journal_entry_date: str = Field(
        ...,
        description=(
            "The date associated with the wellness journal entry, in YYYY-MM-DD format. "
            "Try to infer this from the conversation (e.g., 'today', 'yesterday', specific dates mentioned). "
            "If no specific date is mentioned for the event, use the current date of the conversation for 'ADD' or 'UPDATE' operations. "
            "For 'REMOVE', use the date of the entry being removed or the current date."
        )
    )

    wellness_journal_severity_value: Literal[1, 2, 3] = Field(
        ...,
        description=(
            "The severity of the reported symptom or condition, rated on a scale of 1 to 3. "
            "1: Low/Mild (minor discomfort, not significantly impacting daily activities). "
            "2: Medium/Moderate (noticeable impact, may interfere with some daily activities). "
            "3: High/Severe (significant impact, debilitating, or significantly disrupts activities). "
            "Infer this from the patient's description. If severity is unclear, default to 1."
        )
    )



class Workflow2State(MedicalAgentState):
    # Final structured response from the agent
    wellness_journal_operation: WellnessJournalOperation


graph_builder_3 = StateGraph(Workflow2State)



def wellness_journal_entry_generator_node(state: Workflow2State):
    print("\n--- Entered wellness_journal_entry_generator_node --------------------")
    print(current_date_manila_iso)

    # print(pending_journal_updates)

    conversation_history = state["messages"]
    existing_entries_str = state.get("existing_journal_entries_json_string", "[]") 


    # Ensure the LLM used here supports ainvoke and structured output
    wellness_journal_llm = llm.with_structured_output(WellnessJournalOperation)

    try:
        current_pending_updates_str = json.dumps(pending_journal_updates)
    except TypeError as e:
        print(f"Error serializing pending_journal_updates: {e}. Using empty list.")
        current_pending_updates_str = "[]"


    if not conversation_history:
        print("Warning: No conversation history found for journal entry generation.")
        return {"wellness_journal_operation": None} 

    # Prepare messages for the journal LLM
    messages_for_journal_llm: list[BaseMessage] = [
        SystemMessage(content=system_prompt_content_wf_2), # system_prompt_content is updated
        HumanMessage(content=f"Here are the existing wellness journal entries:\n{pending_journal_updates_2}"),
    ]

    if all(isinstance(msg, BaseMessage) for msg in conversation_history):
        messages_for_journal_llm.extend(conversation_history)
    else:
        print("Warning: Conversation history contains non-BaseMessage objects. Attempting conversion or skipping.")



    messages_for_journal_llm.append(
        HumanMessage(content="Based on the full conversation history, the EXTERNALLY SAVED journal entries, AND THE PENDING updates, what is the single most appropriate wellness journal operation (ADD, UPDATE, or REMOVE) to perform next? Provide only the JSON object.")
    )


    try:

        print("LLM call with structured output would happen here.")
        journal_operation_result = wellness_journal_llm.invoke(messages_for_journal_llm)

        if journal_operation_result:
            print(f"💛 Wellness journal LLM result: {journal_operation_result}")
            print(journal_operation_result)
            print(type(journal_operation_result))
            return {"wellness_journal_operation": journal_operation_result}
        else:
            print("Wellness journal LLM returned no result.")
            return {"wellness_journal_operation": None}

    except Exception as e:
        print(f"Error in wellness_journal_llm.invoke: {e}")
        return {"wellness_journal_operation": None}





graph_builder_3.add_node("llm_wellness_journal", wellness_journal_entry_generator_node)
graph_builder_3.add_edge(START, "llm_wellness_journal")
graph_workflow_2 = graph_builder_3.compile()





async def process_wellness_journal_data(input_payload_for_journal):
    """
    Simulates processing of conversation history for a wellness journal entry.
    Prints a preconfigured output after a delay.
    """
    print("--- Wellness Journal Processor UI PROCESS---")


    journal_output_process_2 = graph_workflow_2.invoke(input_payload_for_journal)
    actual_journal_operation = journal_output_process_2.get("wellness_journal_operation")

    if actual_journal_operation is None:
        print("No journal operation to process - actual_journal_operation is None")
        return None

    wellness_journal_final_entries = {
        "wellness_journal_entry_id": actual_journal_operation.wellness_journal_entry_id,
        "wellness_journal_title": actual_journal_operation.wellness_journal_title,
        "wellness_journal_current_summary": actual_journal_operation.wellness_journal_current_summary,
        "wellness_journal_entry_action": actual_journal_operation.wellness_journal_entry_action, 
        "wellness_journal_entry_date": actual_journal_operation.wellness_journal_entry_date,  
        "wellness_journal_severity_value": actual_journal_operation.wellness_journal_severity_value,  
    }    

    print(wellness_journal_final_entries)
    pending_journal_updates.append(wellness_journal_final_entries)
    pending_journal_updates_2.append(wellness_journal_final_entries)

    print("💚 --- JOURNAL UPDATES NEW VALUE---")
    print(pending_journal_updates)

    print("💚 --- JOURNAL UPDATES NEW VALUE---")
    return wellness_journal_final_entries







# --- FT Component for a single journal entry ---
def render_single_journal_entry_ft(entry_data: dict):
    try:
        print(f"Debug: render_single_journal_entry_ft called with: {entry_data}")
        
        severity_map = {
            1: {"text": "Low", "classes": "text-green-700 border-green-400 bg-green-100"},
            2: {"text": "Medium", "classes": "text-yellow-700 border-yellow-400 bg-yellow-100"},
            3: {"text": "High", "classes": "text-red-700 border-red-400 bg-red-100"},
        }
        
        # Use .get with a default for severity, and ensure it's an int
        severity_val = entry_data.get("wellness_journal_severity_value")
        print(f"Debug: severity_val = {severity_val}")
        
        try:
            severity_int = int(severity_val) if severity_val is not None else 1
        except ValueError:
            severity_int = 1 # Default if conversion fails
            
        severity_info = severity_map.get(severity_int, {"text": "N/A", "classes": "text-gray-600 border-gray-300 bg-gray-100"})
        
        entry_id_val = entry_data.get("wellness_journal_entry_id", f"entry-{time.time_ns()}")
        item_id_attr = f"journal-entry-{entry_id_val}" # Unique ID for the div
        print(f"Debug: entry_id_val = {entry_id_val}, item_id_attr = {item_id_attr}")

        # Format date nicely
        try:
            date_obj = datetime.fromisoformat(entry_data.get("wellness_journal_entry_date", datetime.now().isoformat()))
            formatted_date = date_obj.strftime('%b %d, %Y') # e.g., May 23, 2025
        except ValueError as e:
            print(f"Debug: Date parsing error: {e}")
            formatted_date = "Invalid Date"

        print("Debug: About to create Div element")
        
        result = Div(
            Div(
                H3(entry_data.get("wellness_journal_title", "No Title"), cls="font-medium text-base-content/90 text-sm"),
                Span(severity_info["text"], cls=f"text-xs font-semibold px-2 py-0.5 rounded-full border {severity_info['classes']}"),
                cls="flex justify-between items-start mb-1"
            ),
            P(entry_data.get("wellness_journal_current_summary", "No summary."), cls="text-base-content/80 text-xs mb-1.5 leading-relaxed"),
            P(formatted_date, cls="text-base-content/70 text-xs text-right"),
            Button(
                Span("delete", cls="material-icons emoji-icon text-sm"), # Smaller icon
                hx_post="/htmx/journal_entry_action",
                hx_vals=json.dumps({"wellness_journal_entry_id": str(entry_id_val), "wellness_journal_entry_action": "REMOVE"}),
                hx_target=f"#{item_id_attr}", # Target self for removal
                hx_swap="outerHTML",          # Remove the element
                # Add hx_confirm here if desired: hx_confirm="Are you sure you want to remove this entry?"
                cls="btn btn-xs btn-circle btn-ghost text-error absolute top-1 right-1 opacity-50 hover:opacity-100",
                title="Remove Entry"
            ),
            cls="bg-base-100/80 backdrop-blur-sm rounded-lg p-3 shadow-md hover:shadow-lg transition-shadow border border-base-300/80 relative animate-fadeIn", # Added animation
            id=item_id_attr
        )
        
        print(f"Debug: Successfully created Div element: {type(result)}")
        return result
        
    except Exception as e:
        print(f"ERROR in render_single_journal_entry_ft: {e}")
        print(f"ERROR traceback: {traceback.format_exc()}")
        
        # Return a fallback div instead of None
        fallback_id = f"journal-entry-error-{entry_data.get('wellness_journal_entry_id', 'unknown')}"
        return Div(
            P(f"Error rendering journal entry: {str(e)}", cls="text-red-500"),
            id=fallback_id,
            cls="bg-red-50 border border-red-200 p-3 rounded"
        )

# --- ⚪⚪⚪⚪ Workflow 2 : JOURNAL ENTRY CONTROLLER  START  ⚪⚪⚪⚪ ------- 





async def llm_agent_1(user_message: str, attachments_data: Optional[list[dict]] = None):
    """
    Processes the user message and optional image attachments,
    invokes the LangGraph agent, and returns the final response.
    'attachments_data' is expected to be a list of dictionaries, where each dict has:
    {"filename": "...", "content_type": "image/png", "base64": "..."}
    """
    print(f"\n--- Entered llm_agent_1 ---")
    print(f"User Message: {user_message}")
    if attachments_data:
        print(f"Number of attachments: {len(attachments_data)}")

    message_content_parts: List[dict] = [{"type": "text", "text": user_message}]
    image_details_for_state_and_tool: List[dict] = [] 

    if attachments_data:
        for att_data in attachments_data:

            b64_string = att_data.get("base64")
            media_type = att_data.get("content_type", "image/jpeg")

            if b64_string:
                message_content_parts.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": b64_string}
                })

                image_details_for_state_and_tool.append({"data": b64_string, "media_type": media_type})
    

    config = cast(Any, {"configurable": {"thread_id": "1"}})
    initial_messages = HumanMessage(content=cast(Any, message_content_parts))
    
    initial_graph_state = {
        "messages": [initial_messages],  # Wrap single message in a list
        "input_base64_images": image_details_for_state_and_tool if image_details_for_state_and_tool else None,
    }

    print(f"\nInitial graph state being sent to agent:")
    print(f"  Input Base64 Images provided: {bool(initial_graph_state['input_base64_images'])}")
    if initial_graph_state['input_base64_images']:
        print(f"  Number of image details for tool: {len(initial_graph_state['input_base64_images'])}")

    for i, msg in enumerate(initial_graph_state["messages"]):
        print(f"  Message {i} Type: {msg.type}")
        if isinstance(msg.content, list):
            for part_idx, part in enumerate(msg.content):
                if part["type"] == "text":
                    print(f"    Part {part_idx} (text): {part['text'][:50]}...")
                elif part["type"] == "image":
                    print(f"    Part {part_idx} (image): media_type={part['source']['media_type']}, data_len={len(part['source']['data'])}")
        else:
            print(f"    Content: {str(msg.content)[:70]}...")

    final_state = graph_1.invoke(initial_graph_state, config)

    final_ai_response_content = "No response generated."
    if final_state and "messages" in final_state and final_state["messages"]:
        last_message_obj = final_state["messages"][-1]
        if isinstance(last_message_obj, AIMessage):
            final_ai_response_content = last_message_obj.content
        elif isinstance(last_message_obj, ToolMessage) and len(final_state["messages"]) > 1:
            potential_ai_message = final_state["messages"][-2]
            if isinstance(potential_ai_message, AIMessage):
                 final_ai_response_content = potential_ai_message.content
        else:
            final_ai_response_content = str(last_message_obj.content)

    print(f"\nFinal AI Response from invoke: {final_ai_response_content}")


    # print("------------------ PRINTING FINAL STATE MESSAGES-----------------------")
    # print(final_state["messages"])
    # print("------------------ PRINTING FINAL STATE MESSAGES-----------------------")

    ai_response = final_ai_response_content
    print("------------------ body scanner command start -----------------------")    


    workflow_input_state = {
        "messages": final_state.get("messages", []), 
        "input_base64_images": None,
        "body_scanner_command": None 
    }    

    body_scan_command_wf = graph_workflow_1.invoke(workflow_input_state)

    print("------------------ body scanner command workflow output -----------------------")    

    print(body_scan_command_wf)

    workflow_input_state = {
        "messages": final_state.get("messages", []), 
        "input_base64_images": None,
        "body_scanner_command": None 
    }    


    asyncio.create_task(process_wellness_journal_data(workflow_input_state))
    print("--- Wellness Journal Processor: Task scheduled (will run in background) ---")



    
    response_data = {
        "ai_response": f"{ai_response}", # Dynamic AI response
        "body_scanner_animation_action_comand": body_scan_command_wf["body_scanner_command"],
        "trigger_wellness_journal_data_listener": "START", # This can be made dynamic too
        "output_conversation_history": "EMPTY" # Using the predefined list
    }

    return response_data




def unified_ui_controller_for_chat_window_and_body_scanner(llm_data: dict, user_message_text: str, bubble_id: Optional[str] = None):
    """
    Processes LLM data to generate UI updates (primarily AI chat bubble).
    Prints other data for now.
    """
    ai_response_text = llm_data.get("ai_response", "Sorry, I encountered an issue.")
    current_id = bubble_id if bubble_id else f"ai-bubble-{time.time_ns()}"

    # Generate AI chat bubble FT component
    ai_chat_bubble = Div(
        Div(
            Div(
                Div(
                    Span("smart_toy", cls="material-icons emoji-icon"),
                    cls="bg-transparent text-neutral-content rounded-full w-8 h-8 text-sm flex items-center justify-center"
                ),
                cls="avatar placeholder p-0 w-8 h-8 rounded-full mr-2 bg-base-300"
            ),
            Div( 
                P(ai_response_text, cls="text-sm leading-relaxed chat-message-text"),
                cls="chat-bubble chat-bubble-neutral bg-base-300 text-base-content rounded-bl-none shadow-md"
            ),
            cls="flex items-end max-w-xs sm:max-w-md md:max-w-lg"
        ),
        cls="flex justify-start chat-message-container animate-slideUp", 
        id=current_id 

    )


    # print(f"Unified UI Controller - Body Scanner Command: {llm_data.get('body_scanner_animation_action_comand')}")
    # print(f"Unified UI Controller - Wellness Journal Trigger: {llm_data.get('trigger_wellness_journal_data_listener')}")
    # print(f"Unified UI Controller - Conversation History: {llm_data.get('output_conversation_history')}")

    return ai_chat_bubble



@rt("/send_chat_message")
async def handle_send_chat_message(req, sess):
    print("================== send_chat_message route  - PRINTING FORM DATA =======================")
    form_data = await req.form()
    print(form_data)
    user_message_text = form_data.get("chatInput", "")

    print("================== send_chat_message route - PRINTING  user_message_text=======================")

    print(user_message_text)


    uploaded_file_objects: list[UploadFile] = form_data.getlist("files")

    attachment_uuids_for_next_step = []
    processed_attachments_for_preview = []
    
    # This needs to be more effecient because I have to wait for the file to be converted to base64 then inserted on saupabase. I think its because of the uuid that I need to wait
    if uploaded_file_objects:
        print(f"Received {len(uploaded_file_objects)} file objects in /send_chat_message.")
        base64_attachments_list = await process_files_to_base64_list(uploaded_file_objects)
        
        if base64_attachments_list:
            processed_attachments_for_preview = base64_attachments_list 
            for att_data in base64_attachments_list:
                if "error" not in att_data and "base64" in att_data:
                    insert_payload = {
                        "base64_string": att_data["base64"],
                        "file_type": att_data.get("content_type"),
                        # Optional: "filename": att_data.get("filename") # if you added filename to your table
                    }
                    try:
                        response = supabase.table("akasi_base64_image_strings").insert(insert_payload).execute()
                        if response.data and len(response.data) > 0:
                            new_uuid = response.data[0]['id']
                            attachment_uuids_for_next_step.append(str(new_uuid))
                            print(f"Inserted attachment {att_data.get('filename', 'N/A')} to Supabase with UUID: {new_uuid}")
                        else:
                            print(f"Error inserting {att_data.get('filename', 'N/A')} to Supabase or no data returned. Response: {response}")
                    except Exception as e:
                        print(f"Supabase insert exception for {att_data.get('filename', 'N/A')}: {e}")
                else:
                    print(f"Skipping insert for attachment due to processing error or missing base64: {att_data.get('filename', 'N/A')}")
            print(f"Collected {len(attachment_uuids_for_next_step)} UUIDs from Supabase inserts.")
        else:
            print("No valid attachments processed to store in Supabase.")
    
    
    if not user_message_text and not processed_attachments_for_preview:
        # If message and attachments are empty, just return the OOB cleared input
        return Textarea(id="chatInput", name="chatInput", placeholder="Describe your symptoms here...", cls="textarea textarea-bordered flex-grow resize-none scrollbar-thin", rows="1", style="min-height: 44px; max-height: 120px;", hx_swap_oob="true")


    # --- Construct User Chat Bubble with Attachment Previews (using processed_attachments_for_preview) ---
    user_chat_bubble_content_elements = []
    if user_message_text:
        user_chat_bubble_content_elements.append(P(user_message_text, cls="text-sm leading-relaxed chat-message-text"))

    if processed_attachments_for_preview:
        attachment_previews_container_items = []
        for att_info in processed_attachments_for_preview: # Use the data we have on hand for preview
            if "error" not in att_info:
                icon_name = "image" if att_info.get("content_type", "").startswith("image/") else "article"
                file_size_kb = (att_info.get('size', 0) / 1024)
                size_text = f"({file_size_kb:.1f} KB)" if file_size_kb > 0 else ""
                
                preview_item = Div(
                    Span(icon_name, cls="material-symbols-outlined emoji-icon text-lg mr-1.5 text-primary/80 flex-shrink-0"),
                    Span(f"{att_info.get('filename', 'N/A')} {size_text}".strip(), cls="text-xs text-base-content/80 truncate"),
                    cls="flex items-center p-1.5 bg-primary/10 rounded"
                )
                attachment_previews_container_items.append(preview_item)
        
        if attachment_previews_container_items:
            user_chat_bubble_content_elements.append(
                Div(*attachment_previews_container_items, cls="mt-2 pt-2 space-y-1.5 border-t border-primary/30")
            )
    



    user_chat_bubble = Div(
        Div(
            Div( 
                Div(
                    Span("person", cls="material-icons emoji-icon"),
                    cls="bg-transparent text-neutral-content rounded-full w-8 h-8 text-sm flex items-center justify-center"
                ),
                cls="avatar placeholder p-0 w-8 h-8 rounded-full ml-2 user-message-gradient"
            ),
            Div(
                *user_chat_bubble_content_elements,
                cls="chat-bubble chat-bubble-primary user-message-gradient rounded-br-none shadow-md"
            ),
            cls="flex items-end max-w-xs sm:max-w-md md:max-w-lg flex-row-reverse"
        ),
        cls="flex justify-end chat-message-container animate-slideUp"
    )

    user_message_text_encoded = urllib.parse.quote(user_message_text)

 
    print("================== send_chat_message route - PRINTING   user_message_text_encoded=======================")

    print(user_message_text)
   

    
    # Construct attachment_uuids_param
    attachment_uuids_str = ",".join(attachment_uuids_for_next_step)
    attachment_uuids_param = f"&attachment_uuids={attachment_uuids_str}" if attachment_uuids_str else ""

    typing_loader_trigger_id = f"typing-loader-placeholder-{time.time_ns()}"
    typing_loader_trigger = Div(
        id=typing_loader_trigger_id,
        hx_get=f"/load_typing_indicator?user_message={user_message_text_encoded}{attachment_uuids_param}",
        hx_trigger="load delay:500ms", hx_swap="outerHTML"
    )

    # This OOB swap clears the textarea.
    cleared_chat_input = Textarea(id="chatInput", name="chatInput", placeholder="Describe your symptoms here...", cls="textarea textarea-bordered flex-grow resize-none scrollbar-thin", rows="1", style="min-height: 44px; max-height: 120px;", hx_swap_oob="true")
 


    return user_chat_bubble, typing_loader_trigger, cleared_chat_input


@rt("/load_typing_indicator")
async def load_typing_indicator_handler(req):
    user_message_from_query = req.query_params.get("user_message", "")
    attachment_uuids = req.query_params.get("attachment_uuids", "") # Get the UUIDs string
    ai_bubble_target_id = f"ai-bubble-{time.time_ns()}"

    print("================== load_typing_indicator   - PRINTING user_message_from_query  =======================")

    print(user_message_from_query)        

    attachment_uuids_param = f"&attachment_uuids={attachment_uuids}" if attachment_uuids else ""

    user_message_text_encoded = urllib.parse.quote(user_message_from_query)

    typing_indicator_bubble = Div(
        Div(
            Div(
                Div(Span("smart_toy", cls="material-icons emoji-icon"), cls="bg-transparent text-neutral-content rounded-full w-8 h-8 text-sm flex items-center justify-center"),
                cls="avatar placeholder p-0 w-8 h-8 rounded-full mr-2 bg-base-300"
            ),
            Div(
                P("Akasi is typing...", cls="text-sm italic text-base-content/70 chat-message-text"),
                cls="chat-bubble chat-bubble-neutral bg-base-300 text-base-content rounded-bl-none shadow-md"
            ),
            cls="flex items-end max-w-xs sm:max-w-md md:max-w-lg"
        ),
        id=ai_bubble_target_id,
        cls="flex justify-start chat-message-container animate-slideUp",
        hx_get=f"/get_ai_actual_response?user_message={user_message_text_encoded}&target_id={ai_bubble_target_id}{attachment_uuids_param}",
        hx_trigger="load delay:50ms", 
        hx_swap="outerHTML"
    )


    return typing_indicator_bubble



@rt("/get_ai_actual_response")
async def get_ai_actual_response_route(req, sess):
    get_user_message = req.query_params.get("user_message", "")
    target_id = req.query_params.get("target_id", "") 
    attachment_uuids_str = req.query_params.get("attachment_uuids", "") # Get the UUIDs string

    user_message_text = urllib.parse.unquote(get_user_message)
    
    print("================== /get_ai_actual_response - PRINTING get_user_message =======================")

    print(get_user_message) 
    print("================== SEEING IF THE PENDING JOURNAL UPDATES HAS NEW ENTRIES  =======================")         
    print(pending_journal_updates)

    print("================== /get_ai_actual_response - PRINTING  user_message_text =======================")

    print( user_message_text)      



    retrieved_attachments_from_supabase = [] # Renamed for clarity
    list_of_uuids_to_delete = [] # Keep track of UUIDs to delete later

    if attachment_uuids_str:
        list_of_uuids = [uid.strip() for uid in attachment_uuids_str.split(',') if uid.strip()]
        if list_of_uuids:
            print(f"Attempting to retrieve attachments from Supabase for UUIDs: {list_of_uuids}")
            try:
                response = supabase.table("akasi_base64_image_strings").select("id, base64_string, file_type").in_("id", list_of_uuids).execute()
                
                if response.data:
                    print(f"Retrieved {len(response.data)} attachments from Supabase.")
                    for row in response.data:

                        retrieved_attachments_from_supabase.append({

                            "filename": f"attachment_{row['id']}.{row['file_type'].split('/')[-1] if row.get('file_type') else 'bin'}",
                            "content_type": row.get('file_type'),
                            "base64": row.get('base64_string'),

                        })
                else:
                    print(f"No data returned from Supabase for UUIDs: {list_of_uuids}. Response: {response}")
            except Exception as e:
                print(f"Supabase select exception for UUIDs {list_of_uuids}: {e}")
        else:
            print("No valid UUIDs found in attachment_uuids_str.")
            


    # ** ADD LATER Optional but Recommended: Delete from Supabase after processing**

    if not user_message_text and not retrieved_attachments_from_supabase:
        return Div(
            P("Error: No message or attachments to process.", cls="text-red-500 text-sm"),
            id=target_id, cls="chat-bubble chat-bubble-error"
        )


    llm_output = await llm_agent_1(user_message_text, attachments_data=retrieved_attachments_from_supabase) 

    print("-------- IM IN THE  /get_ai_actual_response  AFTER THE ai_chat_bubble_component -------------")


    # Trigger an async function that takes in the 

    ai_chat_bubble_component = unified_ui_controller_for_chat_window_and_body_scanner(
        llm_data=llm_output,
        user_message_text=user_message_text, 
        bubble_id=target_id 
    )


    animation_script_component = None
    scanner_command = llm_output.get('body_scanner_animation_action_comand', "idle")
    if scanner_command and scanner_command.lower() != "idle":
        js_command_call = f"executeBodyScannerCommand('{scanner_command}');"
        animation_script_component = Script(f"(() => {{ try {{ {js_command_call} }} catch (e) {{ console.error('Error executing scanner command:', e); }} }})();")

    # Prepare headers for HX-Trigger. Using JSON format for HX-Trigger is robust.
    response_headers = {"HX-Trigger": json.dumps({"loadJournalUpdate": True})}

    content_tuple = [ai_chat_bubble_component]
    if animation_script_component:
        content_tuple.append(animation_script_component)

    # Use FtResponse to send content along with custom headers
    return FtResponse(content=tuple(content_tuple), headers=response_headers)





@rt('/onboarding/wellness-journal')
def wellness_journal_page(auth):
    if auth is None:
        return RedirectResponse('/login', status_code=303)

    scan_line_svg_overlay_raw = Svg(
        NotStr(scan_line_svg_defs_raw_string), 
        NotStr(scan_line_group_raw_string),   
        id="scanLineSvgOverlayRaw",         
        viewBox="0 0 100 200",              
        width="100%",                       
        height="100%",                      
        style="position: absolute; top: 0; left: 0; z-index: 3; pointer-events: none;" 
    )


    chatbox_header = Header(
        H1("Akasi.ai Chat", cls="text-lg sm:text-xl font-semibold text-center"),
        Div(
            Button(
                Span("refresh", cls="material-icons emoji-icon mr-1"), " Clear Chat",
                id="clearChatButton",
                cls="btn btn-xs bg-white/20 hover:bg-white/30 border-none flex items-center gap-1",
                title="Clear chat history"
            ),
            Button(
                "Add AI Bubble",
                id="addAIBubbleButton",
                cls="btn btn-xs bg-white/20 hover:bg-white/30 border-none",
                title="Add sample AI chat bubble"
            ),
            Button(
                "Add User Bubble",
                id="addUserBubbleButton",
                cls="btn btn-xs bg-white/20 hover:bg-white/30 border-none",
                title="Add sample User chat bubble"
            ),
            cls="flex space-x-2 mt-1.5"
        ),
        id="chatboxHeader",
        cls="p-3.5 sm:p-4 shadow-md primary-green-gradient flex flex-col items-center"
    )

    messages_area = Div(
        Div(
            Div(
                Div(
                    Div(
                        Span("smart_toy", cls="material-icons emoji-icon"),
                        cls="bg-transparent text-neutral-content rounded-full w-8 h-8 text-sm flex items-center justify-center"
                    ),
                    cls="avatar placeholder p-0 w-8 h-8 rounded-full mr-2 bg-base-300"
                ),
                Div(
                    P("Hi there! Im Akasi, your personal wellness assistant. I help you track your health by building a wellness journal. I've activated my body scanner to check how you're doing. Just start by telling me how you feel today. You can also add notes, symptoms, photos, or any medical documents along the way. Lets begin!", cls="text-sm leading-relaxed chat-message-text"),
                    cls="chat-bubble chat-bubble-neutral bg-base-300 text-base-content rounded-bl-none shadow-md"
                ),
                cls="flex items-end max-w-xs sm:max-w-md md:max-w-lg"
            ),
            cls="flex justify-start chat-message-container animate-slideUp"
        ),
        

        id="messagesArea",
        cls="flex-grow p-3 sm:p-4 space-y-3 overflow-y-auto bg-base-200 scrollbar-thin"
    )

    chat_input_area = Div(
        Div(id="stagedAttachmentsContainer", 
            cls="mb-2 p-2 border border-base-300 rounded-lg bg-base-200 max-h-32 overflow-y-auto scrollbar-thin space-y-2 hidden" 

        ),
        Div(

            Div(
                Button(

                    
                    Span("add", cls="material-icons emoji-icon text-2xl"),
                    id="attachmentButton", tabindex="0", role="button", title="Attach files",
                    cls="btn btn-ghost btn-circle text-primary"
                ),
                Div( 
                    Button(Span("image", cls="material-icons emoji-icon"), " Attach Image(s)", id="attachImageButton", cls="btn btn-sm btn-ghost justify-start gap-2"),
                    Button(Span("article", cls="material-icons emoji-icon"), " Attach Document(s)", id="attachDocumentButton", cls="btn btn-sm btn-ghost justify-start gap-2"),
                    id="attachmentOptionsContent", tabindex="0",
                    cls="dropdown-content z-[20] menu p-2 shadow bg-base-100 rounded-box w-56 mb-2"
                ),
                id="attachmentOptionsDropdownContainer", cls="dropdown dropdown-top"
            ),


            Form(

                Input(type="file", multiple=True, id="fileInput", name="files_placeholder", cls="hidden"),

                # Chat Textarea
                Textarea(id="chatInput", name="chatInput", 
                        placeholder="Describe your symptoms here...",
                        cls="textarea textarea-bordered flex-grow resize-none scrollbar-thin",
                        rows="1", style="min-height: 44px; max-height: 120px;"),

                # Send Button
                Button(
                    Span("send", cls="material-icons emoji-icon text-xl"),
                    id="sendButton",
                    type="submit",   
                    cls="btn btn-primary btn-circle"
                ),


                # HTMX attributes for the Form:
                id="chatForm", # Added an ID to the form for easier JS targeting
                hx_post="/send_chat_message",
                hx_target="#messagesArea", # Target for appending new user/AI messages
                hx_swap="beforeend",     # Append new messages to the target
                cls="flex items-end space-x-2 sm:space-x-3 flex-grow"
            ),
            cls="flex items-end space-x-2 sm:space-x-3" # Original class for this parent Div
        ),
        cls="bg-base-100 p-3 sm:p-4 shadow-inner border-t border-base-300"
    )

    left_panel_chatbox = Div(
        Div(
            chatbox_header,
            messages_area,
            chat_input_area,
            id="chatboxRoot",
            cls="flex flex-col h-full bg-base-100 text-base-content rounded-lg shadow-xl overflow-hidden border border-base-300"
        ),
        cls="w-full md:w-2/5 lg:w-1/3 h-1/2 md:h-full flex flex-col"
    )

    scanner_visual_container = Div(

        main_anatomy_svg_ft,
        scan_line_svg_overlay_raw,
        cls="border-2 border-emerald-500 rounded-lg bg-white/10 flex items-center justify-center relative overflow-hidden",
        style=f"width: 350px; height: 500px;"
    )


    scanner_main_area_content = Div(
        Div(
            scanner_visual_container,
            Div(
                Div(
                    P("Scanner idle. Describe symptoms or restart. ", id="scannerStatusText", cls="text-base-content text-sm"),
                    Span("💤", id="scannerStatusIconContainer", cls="mt-1 text-xl text-primary  h-6 w-6 flex items-center justify-center"),
                    id="scannerStatusContainer",
                    cls="flex flex-col items-center justify-center h-full"
                ),
                cls="text-center h-10 w-full max-w-xs mb-3 mt-6" # mb-3 provides some space above bottom buttons
            ),
            cls="flex flex-col items-center justify-center flex-grow w-full " # This wrapper grows and centers its content
        ),
        Div(
            Button("Restart Scan", id="restartScanButton", cls="btn btn-outline btn-sm w-full mb-2"),
            Button(
                Span("menu_book", cls="material-icons emoji-icon"), " Finish Wellness Journal",
                id="finishJournalButton",
                cls="btn btn-sm w-full flex items-center justify-center gap-2 primary-green-gradient",
                hx_post="/finalize-journal",         # New endpoint to handle this action
                hx_target="#diaryLoadingOverlay",    # Target the existing overlay
                hx_swap="innerHTML"                  # Replace its content with the response
            ),
            cls="w-full max-w-xs flex flex-col items-center"
        ),
        cls="flex flex-col flex-grow h-full p-4 md:p-6 items-center justify-between relative"
    )


    journal_entries_list_items = [
        Div(
            Div(
                H3("Headache", cls="font-medium text-base-content/90 text-sm"),
                Span("Medium", cls="text-xs font-semibold px-2 py-0.5 rounded-full border text-yellow-700 border-yellow-400 bg-yellow-100"),
                cls="flex justify-between items-start mb-1"
            ),
            P("Dull ache reported across the forehead area.", cls="text-base-content/80 text-xs mb-1.5 leading-relaxed"),
            P("5/17/2025", cls="text-base-content/70 text-xs text-right"),
            cls="bg-base-100/80 backdrop-blur-sm rounded-lg p-3 shadow-md hover:shadow-lg transition-shadow border border-base-300/80"
        ),
        Div(
            Div(
                H3("Knee Pain (Right)", cls="font-medium text-base-content/90 text-sm"),
                Span("Low", cls="text-xs font-semibold px-2 py-0.5 rounded-full border text-green-700 border-green-400 bg-green-100"),
                cls="flex justify-between items-start mb-1"
            ),
            P("Slight discomfort in the right knee after physical activity.", cls="text-base-content/80 text-xs mb-1.5 leading-relaxed"),
            P("5/16/2025", cls="text-base-content/70 text-xs text-right"),
            cls="bg-base-100/80 backdrop-blur-sm rounded-lg p-3 shadow-md hover:shadow-lg transition-shadow border border-base-300/80"
        ),
        Div(
            Div(
                H3("Sleep Quality", cls="font-medium text-base-content/90 text-sm"),
                Span("High", cls="text-xs font-semibold px-2 py-0.5 rounded-full border text-red-700 border-red-400 bg-red-100"),
                cls="flex justify-between items-start mb-1"
            ),
            P("Reports difficulty falling asleep and staying asleep.", cls="text-base-content/80 text-xs mb-1.5 leading-relaxed"),
            P("5/15/2025", cls="text-base-content/70 text-xs text-right"),
            cls="bg-base-100/80 backdrop-blur-sm rounded-lg p-3 shadow-md hover:shadow-lg transition-shadow border border-base-300/80"
        ),
        Div(
            Div(
                H3("Overall Energy", cls="font-medium text-base-content/90 text-sm"),
                Span("Medium", cls="text-xs font-semibold px-2 py-0.5 rounded-full border text-yellow-700 border-yellow-400 bg-yellow-100"),
                cls="flex justify-between items-start mb-1"
            ),
            P("Feeling generally okay, but some afternoon sluggishness noted.", cls="text-base-content/80 text-xs mb-1.5 leading-relaxed"),
            P("5/14/2025", cls="text-base-content/70 text-xs text-right"),
            cls="bg-base-100/80 backdrop-blur-sm rounded-lg p-3 shadow-md hover:shadow-lg transition-shadow border border-base-300/80"
        ),
        Div(
            Span("warning", id="noJournalIconContainer", cls="material-icons mb-2 text-4xl"),
            P("No entries yet.", cls="text-sm"),
            P("Symptoms you describe will appear here.", cls="text-xs mt-1"),
            id="noJournalEntries",
            cls="flex flex-col items-center justify-center h-full text-base-content/70 text-center py-6",
            style="display: none;"
        )
    ]

    journal_entries_panel = Div(
        Div(
            H2("Wellness Journal", cls="text-md font-semibold text-center flex-grow"),
            Button(
                Span("add", cls="material-icons emoji-icon text-lg"),
                id="addManualEntryButton",
                cls="btn btn-xs btn-circle btn-ghost",
                title="Add Manual Entry"
            ),
            cls="p-3.5 border-b border-primary/60 primary-green-gradient flex justify-between items-center"
        ),
        Div(
            id="journalEntriesList",
            cls="flex-grow overflow-y-auto p-3 space-y-2.5 scrollbar-thin"
        ),
        Div( # Placeholder for when no entries exist
            Span("info_outline", id="noJournalIconContainer", cls="material-icons mb-2 text-4xl text-base-content/50"),
            P("No entries yet.", cls="text-sm text-base-content/70"),
            P("Entries from chat or manual additions will appear here.", cls="text-xs mt-1 text-base-content/60"),
            id="noJournalEntries",
            cls="flex flex-col items-center justify-center h-full text-center py-6",
            style="display: flex;" # Initially visible as the list is empty
        ),
        Div( # Clear All Button Container
            Button(
                Span("delete_sweep", cls="material-icons emoji-icon mr-1"), " Clear All",
                id="clearAllJournalButton",
                cls="btn btn-xs btn-outline btn-error flex items-center gap-1.5",
                title="Clear all journal entries",
                hx_post="/htmx/clear_journal",
                # The response from /htmx/clear_journal will handle OOB swaps
                # for #journalEntriesList, #noJournalEntries, and #clearJournalContainer
                hx_confirm="Are you sure you want to clear all journal entries?" # Optional confirmation
            ),
            id="clearJournalContainer",
            cls="p-2.5 border-t border-primary/30 flex justify-end",
            style="display: none;" # Initially hidden, JS/HTMX will show it when entries exist
        ),
        cls="w-full md:w-2/5 lg:w-1/3 h-full border-l border-primary/30 flex flex-col bg-base-100/50"
    )

 


    # This Div is crucial for HTMX to receive journal updates triggered by the server
    journal_update_event_handler_div = Div(
        id="journalUpdateEventHandler", 
        hx_get="/htmx/get_journal_update",
        hx_trigger="loadJournalUpdate from:body", # Listens for 'loadJournalUpdate' event on the body
        hx_target="#journalEntriesList",          # The new entry HTML will go here
        hx_swap="afterbegin",                     # Prepend it to the list
        # This div itself can be empty and hidden; it's a mechanism.
    )

    right_panel_scanner_journal_root = Div(
        scanner_main_area_content,
        journal_entries_panel,
        id="scannerJournalRoot",
        cls="flex flex-col md:flex-row w-full h-full text-base-content rounded-lg shadow-xl overflow-hidden subtle-green-gradient-bg border border-base-300"
    )

    right_panel_wrapper = Div(
        right_panel_scanner_journal_root,
        cls="w-full md:w-3/5 lg:w-2/3 h-1/2 md:h-full flex"
    )

    page_content = Div(
        left_panel_chatbox,
        right_panel_wrapper,
        journal_update_event_handler_div,
        cls="flex flex-col md:flex-row h-full text-base-content p-2 sm:p-4 gap-2 sm:gap-4 font-sans"
    )

    narrow_scan_modal = Dialog(
        Div(
            Form(
                Button(
                    Span("close", cls="material-icons emoji-icon"),
                    id="closeNarrowScanModalButton",
                    cls="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
                ),
                method="dialog"
            ),
            H3("Specify Narrow Scan Target", cls="font-bold text-lg mb-3"),
            Input(type="text", id="narrowScanInput", placeholder="E.g., Head, Lungs, Arm", cls="input input-bordered w-full mb-3"),
            Button("Confirm & Scan", id="confirmNarrowScanButton", cls="btn btn-primary w-full"),
            cls="modal-box"
        ),
        Form(Button("close"), method="dialog", cls="modal-backdrop"),
        id="narrowScanModal", cls="modal"
    )

    # --- Manual Entry Modal (Updated for HTMX submission) ---
    manual_entry_modal = Dialog(
        Div( # Modal Box
            Form( # For DaisyUI 'X' button to close via method="dialog"
                Button(
                    Span("close", cls="material-icons emoji-icon"), 
                    # id="closeManualEntryModalButtonInternal" # JS will target this if needed
                    cls="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
                ), 
                method="dialog" # This form closes the dialog
            ),
            H3("Add Manual Journal Entry", cls="font-bold text-lg mb-4"),
            Form( # This is the actual data submission form, now with HTMX attributes
                Div(Label("Title / Body Part", For="manualTitle", cls="block text-xs font-medium text-base-content/80 mb-1"), Input(type="text", id="manualTitle", name="title", placeholder="E.g., Headache, Stomach Ache", cls="input input-bordered input-sm w-full", required=True), cls="mb-3"),
                Div(Label("Status / Severity", For="manualStatus", cls="block text-xs font-medium text-base-content/80 mb-1"), Select(Option("Low", value="1", selected=True), Option("Medium", value="2"), Option("High", value="3"), id="manualStatus", name="status", cls="select select-bordered select-sm w-full"), cls="mb-3"),
                Div(Label("Summary / Description", For="manualSummary", cls="block text-xs font-medium text-base-content/80 mb-1"), Textarea(id="manualSummary", name="summary", placeholder="Describe the issue or feeling...", rows="3", cls="textarea textarea-bordered textarea-sm w-full", required=True), cls="mb-3"),
                Div(Label("Date", For="manualDate", cls="block text-xs font-medium text-base-content/80 mb-1"), Input(type="date", id="manualDate", name="date", cls="input input-bordered input-sm w-full", required=True), cls="mb-4"),
                Input(type="hidden", name="wellness_journal_entry_action", value="ADD"), # Specify the action for the backend
                Div(
                    Button("Cancel", type="button", id="cancelManualEntryButton", cls="btn btn-sm btn-ghost"), # JS will handle this click to close modal
                    Button("Save Entry", type="submit", id="saveManualEntryButton", cls="btn btn-sm btn-primary"), # This button submits the HTMX form
                    cls="flex justify-end gap-2 mt-0" # Removed modal-action, as form submission handles it
                ),
                id="manualEntryForm", # ID for JS to hook for modal closing on success etc.
                hx_post="/htmx/journal_entry_action",
                hx_target="#journalEntriesList",      # Target where new entry HTML will be placed
                hx_swap="afterbegin",                # Prepend the new entry
                # The server response from /htmx/journal_entry_action (for ADD)
                # will also include OOB swaps for #noJournalEntries and #clearJournalContainer
            ),
            cls="modal-box"
        ),
        Form(Button("close_backdrop", cls="hidden"), method="dialog", cls="modal-backdrop"), # For closing modal by clicking backdrop
        id="manualEntryModal", cls="modal"
    )
    # --- End of Manual Entry Modal ---
    diary_loading_overlay = Div(
        Span("refresh", id="diaryLoadingIconContainer", cls="material-icons text-emerald-400 mb-6 text-5xl animate-subtle-spin"),
        H2("We are building your health diary...", cls="text-white text-2xl font-semibold mb-3"),
        P(
            "Please wait a moment while Akasi.ai compiles your personalized wellness summary.",
            cls="text-center text-gray-300 text-lg max-w-md"
        ),
        id="diaryLoadingOverlay",
        cls="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex flex-col justify-center items-center p-4 animate-fadeIn",
        style="display: none;"
    )

    toast_container = Div(id="toastContainer", cls="toast toast-top toast-center z-[200]")
    script_runner_area = Div(id="script_runner_area")

    full_page_wrapper = Div(
        page_content,
        narrow_scan_modal,
        manual_entry_modal,
        diary_loading_overlay,
        toast_container,
        script_runner_area, 
        cls="h-screen"
    )

    return (
        Title("Wellness Journal - Akasi.ai"),
        google_material_icons_link,
        wellness_journal_css_link,
        wellness_enhancements_js_link,
        full_page_wrapper
    )




# --- HTMX UI ROUTES / FUNCTIONS  ---

@rt("/trigger_body_scan_animation_script")
def get_trigger_body_scan_animation_script():
    js_code = """
    (() => {
        if (typeof startBodyScanAnimation === 'function') {
            startBodyScanAnimation();
        } else {
            console.error('startBodyScanAnimation function not defined in wellness_enhancements.js');
        }
    })();
    """
    return Script(js_code)

@rt("/trigger_stop_body_scan_script")
def get_trigger_stop_body_scan_script():
    js_code = """
    (() => {
        if (typeof stopBodyScanAnimation === 'function') {
            stopBodyScanAnimation();
        } else {
            console.error('stopBodyScanAnimation function not defined in wellness_enhancements.js');
        }
    })();
    """
    return Script(js_code)


@rt("/trigger_body_glow_script")
def get_trigger_body_glow_script():
    """
    This route is triggered by the 'Full Body Glow' button.
    It returns a JavaScript snippet that calls the toggleBodyGlowEffect function
    defined in wellness_enhancements.js.
    """
    js_code = """
    (() => {
        if (typeof toggleBodyGlowEffect === 'function') {
            toggleBodyGlowEffect();
        } else {
            console.error('toggleBodyGlowEffect function not defined in wellness_enhancements.js');
            // Optionally, you could alert the user or send a toast message from here if the function is missing
            // For example: document.getElementById('toastContainer').dispatchEvent(new CustomEvent('showtoast', { detail: { message: 'Error: Glow effect unavailable.', type: 'error' }}));
        }
    })();
    """
    return Script(js_code)

@rt("/js_show_narrow_scan_modal")
def js_show_narrow_scan_modal_script():
    """
    Returns a JavaScript snippet to open the narrowScanModal.
    """
    # Ensure the modal ID matches the one in your FT definitions
    js_code = """
    (() => {
        const modal = document.getElementById('narrowScanModal');
        if (modal && typeof modal.showModal === 'function') {
            // Clear previous input if any
            const narrowInput = document.getElementById('narrowScanInput');
            if (narrowInput) {
                narrowInput.value = '';
            }
            modal.showModal();
        } else {
            console.error('Narrow scan modal or its showModal function not found.');
            // Fallback or error toast could be triggered here
            // Example: showToast('Error: Cannot open scan options.', 'error');
        }
    })();
    """
    return Script(js_code)




@rt("/htmx/journal_entry_action")
async def post_journal_action_handler(req): # Renamed for clarity
    # This endpoint will be called by HTMX forms or buttons
    form_data = await req.form()
    action = form_data.get("wellness_journal_entry_action")
    entry_id = form_data.get("wellness_journal_entry_id")

    print(f"HTMX Journal Action Received: {action}, ID: {entry_id}, Form: {form_data}") # For debugging

    if action == "REMOVE":
        # The client-side HTMX swap (outerHTML) on the delete button already removes the element.
        # This endpoint's job is to confirm and perform any server-side cleanup if needed.
        # For now, it just acknowledges. If server-side state of entries needs updating, do it here.
        # We might need to send OOB swaps for the placeholder/clear button if the list becomes empty.
        # This is now handled by the htmx:afterSwap JS listener as a simpler client-side check.
        print(f"Server: REMOVE action for entry ID {entry_id} processed.")
        return "" # Empty response because client-side swap handles DOM.

    elif action == "ADD": # This will be used by the manual entry form
        new_entry_data = {
            "wellness_journal_entry_id": str(form_data.get("id", time.time_ns())), # Use form ID or generate
            "wellness_journal_title": form_data.get("title", "Untitled Entry"),
            "wellness_journal_current_summary": form_data.get("summary", "No summary provided."),
            "wellness_journal_severity": int(form_data.get("status", 1)),
            "wellness_journal_entry_date": datetime.strptime(form_data.get("date"), '%Y-%m-%d').isoformat() if form_data.get("date") else datetime.now().isoformat(),
            # "wellness_journal_entry_action": "ADD" # Already known
        }
        # Here you would save to a database in a real application.

        new_entry_ft = render_single_journal_entry_ft(new_entry_data)
        # OOB swaps for placeholder and clear button visibility
        no_entries_div_oob = Div(id="noJournalEntries", style="display: none;", hx_swap_oob="true")
        clear_button_div_oob = Div(id="clearJournalContainer", style="display: flex;", hx_swap_oob="true")

        # The new_entry_ft is returned to be swapped into the target of the HTMX form submission
        # (which is #journalEntriesList with swap 'afterbegin').
        return new_entry_ft, no_entries_div_oob, clear_button_div_oob

    return HtmxResponseHeaders(HX_Reswap="none") # Tell HTMX to do nothing if action not handled


@rt("/htmx/get_journal_update")
def get_journal_update_handler(): 
    print("--- Entered /htmx/get_journal_update handler ---")
    global pending_journal_updates # Use the primary queue for UI updates
    global pending_journal_updates_2 # Master list, used for context in REMOVE OOB

    rendered_html_component = None
    action_performed = None
    processed_entry_id = None
    entry_operation_data = None # Initialize

    if pending_journal_updates:
        try:
            entry_operation_data = pending_journal_updates.pop(0) 
            print(f"Debug (get_journal_update_handler): Processing journal operation data: {entry_operation_data}")
            
            if not isinstance(entry_operation_data, dict):
                print(f"ERROR (get_journal_update_handler): Popped data is not a dictionary: {entry_operation_data}")
                entry_operation_data = None # Invalidate it
            else:
                action_performed = entry_operation_data.get("wellness_journal_entry_action")
                processed_entry_id = entry_operation_data.get("wellness_journal_entry_id")
            
            # Attempt to render if data is suitable for ADD/UPDATE
            if entry_operation_data and action_performed in ["ADD", "UPDATE"]:
                print(f"Debug (get_journal_update_handler): Attempting to render for action '{action_performed}' with data: {entry_operation_data}")
                rendered_html_component = render_single_journal_entry_ft(entry_operation_data)
            elif entry_operation_data and action_performed == "REMOVE" and processed_entry_id:
                # For REMOVE, create a specific empty component for OOB removal
                target_id_attr = f"journal-entry-{processed_entry_id}"
                rendered_html_component = Div(id=target_id_attr, hx_swap_oob="true") 
                print(f"Debug (get_journal_update_handler): Action REMOVE for ID {processed_entry_id}. Created empty OOB component.")
            elif entry_operation_data: # NONE_ACTION or unknown
                 print(f"Debug (get_journal_update_handler): Action '{action_performed}' for ID {processed_entry_id}. No UI component to render from this handler for this action.")
                 # rendered_html_component remains None, will be caught by the guard below.

        except IndexError:
            print("Debug (get_journal_update_handler): pending_journal_updates was or became empty during processing.")
            # entry_operation_data and rendered_html_component remain None
        except Exception as e:
            print(f"ERROR (get_journal_update_handler): Exception during processing: {e}\n{traceback.format_exc()}")
            # entry_operation_data and rendered_html_component remain None
    else:
        print("Debug (get_journal_update_handler): pending_journal_updates is empty. No update to send.")
        # entry_operation_data and rendered_html_component remain None

    # CRITICAL GUARD: Check if a component was successfully prepared
    if rendered_html_component is None:
        print(f"Debug (get_journal_update_handler): rendered_html_component is None before action dispatch. Action was '{action_performed}'. Returning 204.")
        return HTMLResponse(content="", status_code=204)

    # --- Action-specific return logic ---
    if action_performed == "ADD":
        print(f"Debug (get_journal_update_handler): Action ADD for {processed_entry_id}. Returning component directly for 'afterbegin' swap.")
        return FtResponse(
            content=(
                rendered_html_component,
                Div(id="noJournalEntries", style="display: none;", hx_swap_oob="true"),
                Div(id="clearJournalContainer", style="display: flex;", hx_swap_oob="true")
            )
        )
    elif action_performed == "UPDATE":
        print(f"Debug (get_journal_update_handler): Action UPDATE for {processed_entry_id}. Modifying attrs for OOB swap.")
        # Directly modify attributes to set hx-swap-oob, avoiding .With()
        if hasattr(rendered_html_component, 'attrs') and isinstance(rendered_html_component.attrs, dict):
            rendered_html_component.attrs['hx-swap-oob'] = 'true' # kebab-case for HTML attributes
            print(f"DIAGNOSTIC (UPDATE path - direct attrs): Attributes modified. Returning component.")
            return rendered_html_component # Return the modified component for OOB swap
        else:
            # This case should ideally not be hit if render_single_journal_entry_ft always returns a valid FT component
            print(f"CRITICAL ERROR (get_journal_update_handler - UPDATE): rendered_html_component (type: {type(rendered_html_component)}) lacks .attrs dict or not a dict. ID: {processed_entry_id}")
            return HTMLResponse("Error: Server component malformed for update.", status_code=500)

    elif action_performed == "REMOVE": 
        # rendered_html_component here is the empty Div(id=target_id_attr, hx_swap_oob="true")
        print(f"Debug (get_journal_update_handler): Action REMOVE for {processed_entry_id}. Returning OOB removal component.")
        if not pending_journal_updates_2: # Check the master list for emptiness
             return FtResponse(
                content=(
                    rendered_html_component, 
                    Div(id="noJournalEntries", style="display: flex;", hx_swap_oob="true"),
                    Div(id="clearJournalContainer", style="display: none;", hx_swap_oob="true")
                )
            )
        return rendered_html_component # Just the OOB empty div to remove the item

    else: 
        print(f"Warning (get_journal_update_handler): Unhandled action '{action_performed}' or component state. Returning 204.")
        return HTMLResponse(content="", status_code=204)



@rt("/htmx/clear_journal")
async def post_clear_journal_handler(req): # Changed name
    global pending_journal_updates
    pending_journal_updates = [] # Clear any pending automated updates as well

    # In a real app, you would clear entries from your database here.

    # Return OOB swaps to reset the journal list UI
    empty_journal_list_oob = Div(id="journalEntriesList", hx_swap_oob="true") # Empty its content
    no_entries_div_oob = Div(id="noJournalEntries", style="display: flex;", hx_swap_oob="true") # Show placeholder
    clear_button_div_oob = Div(id="clearJournalContainer", style="display: none;", hx_swap_oob="true") # Hide clear button

    return empty_journal_list_oob, no_entries_div_oob, clear_button_div_oob


@rt('/finalize-journal')
def post_finalize_journal():
    # Define the HTML content for the loading screen
    loading_elements_tuple = (
        Span("hourglass_empty", cls="material-icons text-emerald-400 mb-6 text-5xl animate-spin"),
        H2("Just a moment! Your Healthy Diary is coming together", cls="text-white text-2xl font-semibold mb-3 text-center px-4"),
        P(
            "Akasi is thoughtfully piecing together your wellness journal entries to give you a clear snapshot of your well-being",
            cls="text-center text-gray-300 text-lg max-w-md px-4"
        )
    )

    # JavaScript to run after the new content is swapped in and this script is processed by HTMX
    js_to_run_on_client = """
    (function() {
        const overlay = document.getElementById('diaryLoadingOverlay');
        if (overlay) {
            // *** THIS IS THE KEY LINE TO SHOW THE OVERLAY ***
            overlay.style.display = 'flex'; 

            // Optional: Re-trigger fade-in animation
            overlay.classList.remove('animate-fadeIn');
            void overlay.offsetWidth; // Force browser reflow/repaint
            overlay.classList.add('animate-fadeIn');
            
            console.log("Loading overlay displayed via inline script. Redirecting to /home in 5 seconds.");
        } else {
            console.error("diaryLoadingOverlay (for inline script) not found!");
        }

        // Set a timeout to redirect to /home after 5 seconds
        setTimeout(function() {
            window.location.href = '/home';
        }, 5000); // 5000 milliseconds = 5 seconds
    })();
    """
    
    return loading_elements_tuple, Script(js_to_run_on_client)


# Landing Page
@rt('/')
def index():
    landing_script = Script(src='/js/landing_animation.js', defer=True)
    landing_css = Link(rel='stylesheet', href='/css/landing_page.css')
    nav_bar = Div(
        Div(
            A('Akasi.ai', cls='btn btn-ghost text-xl'),
            cls='flex-1'
        ),
        Div(
            Ul(
                Li(
                    A('Login', href="/login" ,cls='btn btn-ghost text-teal-600')
                ),
                Li(
                    A('Create Account', href="/signup" ,cls='btn bg-teal-600 text-white hover:bg-teal-700 ml-5')
                ),
                cls='menu menu-horizontal px-1'
            ),
            cls='flex-none'
        ),
        cls='navbar mt-8 bg-base-100 shadow-sm'
    )
    
    # E pagawas nalang kaha ning mga class variables samoka HAHAHHAHAHA ARON SAYUN RA E COPY PASTE
    hero_card = Div(
        Div(
            Div(
                Div(
                    Span('A', cls='text-3xl md:text-4xl text-white font-bold'),
                    cls='w-20 h-20 md:w-28 md:h-28 rounded-full bg-gradient-to-br from-teal-400 via-cyan-500 to-sky-600 flex items-center justify-center shadow-lg'
                ),
                cls='mb-8 flex justify-center'
            ),
            Div(
                Div(
                    Div(id='akasi-hero-message', cls='chat-bubble chat-bubble-success !bg-green-500 text-white shadow-md transition-all duration-300 ease-in-out hover:shadow-xl cursor-pointer animate-float min-h-[3em] flex items-center justify-center p-4 whitespace-nowrap'),
                    cls='chat chat-end justify-center'
                ),
                cls='max-w-md w-full min-w-[300px] sm:min-w-[350px]'
            ),
            cls='hero-content text-center flex-col items-center py-16 md:py-24'
        ),
        cls='hero min-h-96 bg-base-100 mt-8 rounded-box shadow-lg'
    )   

    # Container for all landing content
    landing_page_content = Div(
        landing_css,
        nav_bar,
        hero_card,
        landing_script,
        cls="max-w-4xl mx-auto min-h-screen flex flex-col"
    )


    return (
        Title("Welcome to Akasi.ai"),
        landing_page_content 
    )


@rt('/signup')
def signup_page(sess):
    auth = sess.get('user', None) # Adjust session key as per your application
    if auth:
        return RedirectResponse('/home', status_code=303) # Adjust redirect URL as needed

    # --- Logo and Site Name Section ---
    logo_section = Div(
        A(
            Div(
                Span('A', cls='text-2xl text-white font-bold'),
                cls='w-16 h-16 rounded-full bg-gradient-to-br from-teal-400 via-cyan-500 to-sky-600 flex items-center justify-center shadow-lg'
            ),
            Span('Akasi.ai', cls='ml-3 text-2xl font-semibold text-gray-700'),
            href="/",
            cls='flex items-center justify-center'
        ),
        cls='mb-6'
    )

    # --- Form Input Group: Full Name ---
    full_name_input_group = Div(
        Label(
            Span('Full Name', cls='label-text text-gray-700'),
            For='fullName',
            cls='label'
        ),
        Input(type='text', id='fullName', name='fullName', placeholder='e.g., Alex Smith',
              cls='input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500', required=True)
    )

    # --- Form Input Group: Email ---
    email_input_group = Div(
        Label(
            Span('Email Address', cls='label-text text-gray-700'),
            For='email',
            cls='label'
        ),
        Input(type='email', id='email', name='email', placeholder='you@example.com',
              cls='input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500', required=True)
    )

    # --- Form Input Group: Password ---
    password_input_group = Div(
        Label(
            Span('Password', cls='label-text text-gray-700'),
            For='password',
            cls='label'
        ),
        Input(type='password', id='password', name='password', placeholder='•••••••• (min. 8 characters)',
              cls='input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500', required=True, minlength="8")
    )

    # --- Form Input Group: Confirm Password ---
    confirm_password_input_group = Div(
        Label(
            Span('Confirm Password', cls='label-text text-gray-700'),
            For='confirmPassword',
            cls='label'
        ),
        Input(type='password', id='confirmPassword', name='confirmPassword', placeholder='••••••••',
              cls='input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500', required=True, minlength="8")
    )

    # --- Terms and Conditions Checkbox ---
    terms_checkbox_section = Div(
        Label(
            Input(type='checkbox', name='terms', cls='checkbox checkbox-primary checkbox-sm', required=True),
            Span( 
                "I agree to the ",
                A("Terms of Service", href="#", cls="link link-hover text-teal-600 hover:text-teal-700"),
                " and ",
                A("Privacy Policy", href="#", cls="link link-hover text-teal-600 hover:text-teal-700"),
                ".",
                cls='label-text text-gray-600 text-sm'
            ),
            cls='label cursor-pointer gap-2 justify-start'
        ),
        cls='form-control mt-2'
    )

    # --- Submit Button Section ---
    submit_button_section = Div(
        Button('Create Account', type='submit',
               cls='btn btn-primary bg-teal-600 hover:bg-teal-700 border-none text-white w-full text-lg'),
        cls='card-actions justify-center w-full mt-6'
    )

    # --- Signup Form Structure ---
    signup_form_structure = Form(
        full_name_input_group,
        email_input_group,
        password_input_group,
        confirm_password_input_group,
        terms_checkbox_section,
        submit_button_section,
        cls='w-full space-y-4',
        method="post", 
        action="/signup"  
    )

    # --- Login Link Section ---
    login_link_structure = Div(
        P(
            "Already have an account? ",
            A('Log in here', href='/login', cls='link link-hover text-teal-600 hover:text-teal-700 font-semibold'), 
            cls='text-gray-600'
        ),
        cls='mt-6 text-center text-sm'
    )

    # --- Card Body Content ---
    card_body_structure = Div(
        logo_section,
        H2('Create Your Account', cls='card-title text-2xl md:text-3xl font-bold mb-1 text-gray-800'),
        P('Join Akasi.ai to start your wellness journey.', cls='text-gray-500 mb-6'),
        signup_form_structure,
        login_link_structure,
        cls='card-body items-center text-center p-8 md:p-12'
    )

    # --- Main Signup Card Element ---
    signup_page_main_content = Main(
        card_body_structure,
        cls='card w-full max-w-lg bg-base-100 shadow-xl' 
    )

    # --- Footer Element ---
    signup_page_footer = Footer(
        '© 2025 Akasi.ai. All rights reserved.',
        cls='text-center mt-8 text-xs text-gray-500'
    )

    # --- Layout Wrapper for Centering Signup Page Content ---
    signup_layout_wrapper = Div(
        signup_page_main_content,
        signup_page_footer,
        # password_validation_script has been removed
        cls="flex flex-col items-center justify-center w-full min-h-screen px-4 py-8"
    )

    # The route returns a Title component and the layout wrapper
    return (
        Title("Create Account - Akasi.ai"),
        signup_layout_wrapper
    )


@rt('/signup')
async def signup_submit(req, sess):
    form = await parse_form(req)
    # Match field names to the new form: fullName, email, password, confirmPassword, terms
    display_name = str(form.get('fullName', '')) # Changed from 'display_name' to 'fullName'
    email = str(form.get('email', ''))
    password = str(form.get('password', ''))
    # confirm_password = form.get('confirmPassword') # You might want to use this in validation
    # terms_agreed = form.get('terms') # You might want to check this

    try:
        # User's existing Supabase signup logic - REMAINS UNCHANGED
        # Ensure the data passed to sign_up matches what Supabase expects.
        # If Supabase needs 'display_name', you might need to pass it in options.
        # For example: options={"data": {"display_name": display_name}}
        res = supabase.auth.sign_up({"email": email, "password": password, 
                                     "options": {"data": {"full_name": display_name}} # Example of passing additional data
                                    })
        if res.user and res.session:
            user = res.user
            session = res.session
            
            sess['user'] = {
                'id': user.id, 
                'email': user.email,
                'display_name': display_name, # Storing the display_name/fullName
                'access_token': session.access_token,
                'refresh_token': session.refresh_token
            }
            
            auth_client = use_auth_context(session.access_token, session.refresh_token)
                                    
            return RedirectResponse('/onboarding/personal-info', status_code=303)
        else:
            # This case might indicate an issue with the signup response even if no exception was thrown
            # Or if res.user is None for some other reason (e.g., email confirmation required)
            # Re-render form with a generic error or a specific one if available from `res`
            error_message = "Signup was not successful. Please try again."
            # Note: Supabase AuthResponse doesn't have an 'error' attribute in type annotations
            # Errors are typically handled via exceptions
            # Fall through to the general exception handling below by raising an exception
            raise Exception(error_message) 
            
    except Exception as e:
        # --- Error Handling: Reconstruct the signup page with an error message ---
        
        # 1. Create the error message component
        error_message_component = Div(
            NotStr('<svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2 2m2-2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>'),
            Span(f"{str(e)}"),
            cls="alert alert-error shadow-lg my-4"
        )

        # 2. Reconstruct components from the GET route's structure
        logo_section = Div(
            A(
                Div(
                    Span('A', cls='text-2xl text-white font-bold'),
                    cls='w-16 h-16 rounded-full bg-gradient-to-br from-teal-400 via-cyan-500 to-sky-600 flex items-center justify-center shadow-lg'
                ),
                Span('Akasi.ai', cls='ml-3 text-2xl font-semibold text-gray-700'),
                href="/", 
                cls='flex items-center justify-center'
            ),
            cls='mb-6'
        )

        full_name_input_group = Div(
            Label(Span('Full Name', cls='label-text text-gray-700'), For='fullName', cls='label'),
            Input(type='text', id='fullName', name='fullName', placeholder='e.g., Alex Smith',
                  cls='input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500', 
                  required=True, value=display_name or '') # Pre-fill
        )

        email_input_group = Div(
            Label(Span('Email Address', cls='label-text text-gray-700'), For='email', cls='label'),
            Input(type='email', id='email', name='email', placeholder='you@example.com',
                  cls='input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500', 
                  required=True, value=email or '') # Pre-fill
        )

        password_input_group = Div(
            Label(Span('Password', cls='label-text text-gray-700'), For='password', cls='label'),
            Input(type='password', id='password', name='password', placeholder='•••••••• (min. 8 characters)',
                  cls='input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500', required=True, minlength="8")
        )

        confirm_password_input_group = Div(
            Label(Span('Confirm Password', cls='label-text text-gray-700'), For='confirmPassword', cls='label'),
            Input(type='password', id='confirmPassword', name='confirmPassword', placeholder='••••••••',
                  cls='input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500', required=True, minlength="8")
        )

        terms_checkbox_section = Div(
            Label(
                Input(type='checkbox', name='terms', cls='checkbox checkbox-primary checkbox-sm', required=True), # Consider pre-checking if terms_agreed
                Span(
                    "I agree to the ",
                    A("Terms of Service", href="#", cls="link link-hover text-teal-600 hover:text-teal-700"),
                    " and ",
                    A("Privacy Policy", href="#", cls="link link-hover text-teal-600 hover:text-teal-700"),
                    ".",
                    cls='label-text text-gray-600 text-sm'
                ),
                cls='label cursor-pointer gap-2 justify-start'
            ),
            cls='form-control mt-2'
        )

        submit_button_section = Div(
            Button('Create Account', type='submit',
                   cls='btn btn-primary bg-teal-600 hover:bg-teal-700 border-none text-white w-full text-lg'),
            cls='card-actions justify-center w-full mt-6'
        )

        signup_form_structure = Form(
            full_name_input_group,
            email_input_group,
            password_input_group,
            confirm_password_input_group,
            terms_checkbox_section,
            submit_button_section,
            cls='w-full space-y-4',
            method="post", 
            action="/signup"  
        )

        login_link_structure = Div(
            P(
                "Already have an account? ",
                A('Log in here', href='/login', cls='link link-hover text-teal-600 hover:text-teal-700 font-semibold'), 
                cls='text-gray-600'
            ),
            cls='mt-6 text-center text-sm'
        )

        card_body_structure = Div(
            logo_section,
            H2('Create Your Account', cls='card-title text-2xl md:text-3xl font-bold mb-1 text-gray-800'),
            P('Join Akasi.ai to start your wellness journey.', cls='text-gray-500 mb-2'), # Adjusted margin
            error_message_component, # Insert error message
            signup_form_structure,
            login_link_structure,
            cls='card-body items-center text-center p-8 md:p-12'
        )

        signup_page_main_content = Main(
            card_body_structure,
            cls='card w-full max-w-lg bg-base-100 shadow-xl' 
        )

        signup_page_footer = Footer(
            '© 2024 Akasi.ai. All rights reserved.',
            cls='text-center mt-8 text-xs text-gray-500'
        )

        signup_layout_wrapper = Div(
            signup_page_main_content,
            signup_page_footer,
            # No client-side script here
            cls="flex flex-col items-center justify-center w-full min-h-screen px-4 py-8"
        )
        
        return (
            Title("Signup Error - Akasi.ai"),
            signup_layout_wrapper
        )

@rt('/login')
def login_page(sess):
    auth = sess.get('user', None) # Adjust session key as per your application
    if auth:
        return RedirectResponse('/home', status_code=303) # Adjust redirect URL as needed

    # --- Logo and Site Name Section ---
    logo_section = Div(
        A( 
            Div( 
                Span('A', cls='text-2xl text-white font-bold'),
                cls='w-16 h-16 rounded-full bg-gradient-to-br from-teal-400 via-cyan-500 to-sky-600 flex items-center justify-center shadow-lg'
            ),
            Span('Akasi.ai', cls='ml-3 text-2xl font-semibold text-gray-700'), 
            href="/", 
            cls='flex items-center justify-center' 
        ),
        cls='mb-6' 
    )

    # --- Form Input Group: Email ---
    email_input_group = Div(
        Label(
            Span('Email Address', cls='label-text text-gray-700'),
            For='email', 
            cls='label'
        ),
        Input(type='email', id='email', name='email', placeholder='you@example.com',
              cls='input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500', required=True)
    )

    # --- Form Input Group: Password ---
    password_input_group = Div(
        Label(
            Span('Password', cls='label-text text-gray-700'),
            For='password', 
            cls='label'
        ),
        Input(type='password', id='password', name='password', placeholder='••••••••',
              cls='input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500', required=True)
    )

    # --- Remember Me & Forgot Password Section ---
    remember_forgot_section = Div(
        Div( 
            Label(
                Input(type='checkbox', name='remember', cls='checkbox checkbox-primary checkbox-sm'),
                Span('Remember me', cls='label-text text-gray-600'),
                cls='label cursor-pointer gap-2' 
            ),
            cls='form-control' 
        ),
        A('Forgot password?', href='#', cls='link link-hover text-teal-600 hover:text-teal-700'), 
        cls='flex items-center justify-between text-sm mt-2' 
    )

    # --- Submit Button Section ---
    submit_button_section = Div(
        Button('Log In', type='submit',
               cls='btn btn-primary bg-teal-600 hover:bg-teal-700 border-none text-white w-full text-lg'),
        cls='card-actions justify-center w-full mt-6' 
    )

    # --- Login Form Structure (combining all form elements) ---
    login_form_structure = Form(
        email_input_group,
        password_input_group,
        remember_forgot_section,
        submit_button_section,
        cls='w-full space-y-4', 
        method="post",         
        action="/login"         
    )

    # --- Sign Up Link Section ---
    signup_link_structure = Div(
        P(
            "Don't have an account? ", 
            A('Sign up here', href='/signup', cls='link link-hover text-teal-600 hover:text-teal-700 font-semibold'), 
            cls='text-gray-600' 
        ),
        cls='mt-6 text-center text-sm' 
    )

    # --- Card Body Content (combining all elements within the card) ---
    card_body_structure = Div(
        logo_section,
        H2('Welcome Back!', cls='card-title text-2xl md:text-3xl font-bold mb-1 text-gray-800'), 
        P('Please enter your details to log in.', cls='text-gray-500 mb-6'), 
        login_form_structure, 
        signup_link_structure, 
        cls='card-body items-center text-center p-8 md:p-12' 
    )

    # --- Main Login Card Element ---
    login_page_main_content = Main( 
        card_body_structure,
        cls='card w-full max-w-md bg-base-100 shadow-xl' 
    )

    # --- Footer Element ---
    login_page_footer = Footer(
        '© 2025 Akasi.ai. All rights reserved.', 
        cls='text-center mt-8 text-xs text-gray-500' 
    )

    login_layout_wrapper = Div(
        login_page_main_content,
        login_page_footer,
        cls="flex flex-col items-center justify-center w-full min-h-screen px-4 py-8"
    )


    return (
        Title("Login - Akasi.ai"), 
        login_layout_wrapper      
    )



def get_onboarding_redirect(onboarding_step):
    """Returns the appropriate redirect based on onboarding step"""
    if onboarding_step == "personal_info":
        return '/onboarding/personal-info'
    elif onboarding_step == "wellness_journal":
        return '/onboarding/wellness-journal'
    elif onboarding_step == "completed":
        return '/home'
    else:
        return '/onboarding/personal-info'



@rt('/login') 
async def login_submit(req, sess): # Changed to req, sess to match common FastHTML patterns
    form = await parse_form(req)
    email = str(form.get('email', ''))
    password = str(form.get('password', ''))
    
    try:
        # User's existing Supabase login logic - REMAINS UNCHANGED
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        if not res.user or not res.session:
            raise Exception("Authentication failed - no user or session returned")
            
        user = res.user
        session = res.session
        
        sess['user'] = {
            'id': user.id, 
            'email': user.email,
            'access_token': session.access_token,
            'refresh_token': session.refresh_token
        }
        
        auth_client = use_auth_context(session.access_token, session.refresh_token)
        
        try:
            user_profile = fetch_user_profile(auth_client, user.id)
            current_onboarding_step = user_profile.get('onboarding_step', 'personal_info')
        except Exception as e:
            print(f"Error fetching profile: {str(e)}")
            current_onboarding_step = 'personal_info' 
        
        redirect_url = get_onboarding_redirect(current_onboarding_step)
        return RedirectResponse(redirect_url, status_code=303)
    
    except Exception as e:
        error_message_component = Div(
            # Optional: SVG icon for error
            NotStr('<svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2 2m2-2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>'),
            Span(f"{str(e)}"), # The actual error message from the exception
            cls="alert alert-error shadow-lg my-4" # DaisyUI alert classes, added margin
        )
        logo_section = Div(
            A( 
                Div( 
                    Span('A', cls='text-2xl text-white font-bold'),
                    cls='w-16 h-16 rounded-full bg-gradient-to-br from-teal-400 via-cyan-500 to-sky-600 flex items-center justify-center shadow-lg'
                ),
                Span('Akasi.ai', cls='ml-3 text-2xl font-semibold text-gray-700'), 
                href="/", 
                cls='flex items-center justify-center' 
            ),
            cls='mb-6' 
        )

        # --- Form Input Group: Email (pre-filled) ---
        email_input_group = Div(
            Label(
                Span('Email Address', cls='label-text text-gray-700'),
                For='email', # Matches the ID in the GET route
                cls='label'
            ),
            Input(type='email', id='email', name='email', placeholder='you@example.com',
                  cls='input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500', 
                  required=True,
                  value=email or '' # Pre-fill email if available
            )
        )

        # --- Form Input Group: Password ---
        password_input_group = Div(
            Label(
                Span('Password', cls='label-text text-gray-700'),
                For='password', # Matches the ID in the GET route
                cls='label'
            ),
            Input(type='password', id='password', name='password', placeholder='••••••••',
                  cls='input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500', required=True)
        )

        # --- Remember Me & Forgot Password Section ---
        remember_forgot_section = Div(
            Div( 
                Label(
                    Input(type='checkbox', name='remember', cls='checkbox checkbox-primary checkbox-sm'),
                    Span('Remember me', cls='label-text text-gray-600'),
                    cls='label cursor-pointer gap-2' 
                ),
                cls='form-control' 
            ),
            A('Forgot password?', href='#', cls='link link-hover text-teal-600 hover:text-teal-700'), 
            cls='flex items-center justify-between text-sm mt-2' 
        )

        # --- Submit Button Section ---
        submit_button_section = Div(
            Button('Log In', type='submit',
                   cls='btn btn-primary bg-teal-600 hover:bg-teal-700 border-none text-white w-full text-lg'),
            cls='card-actions justify-center w-full mt-6' 
        )

        # --- Login Form Structure ---
        login_form_structure = Form(
            email_input_group,
            password_input_group,
            remember_forgot_section,
            submit_button_section,
            cls='w-full space-y-4', 
            method="post",         
            action="/login"         
        )

        # --- Sign Up Link Section ---
        signup_link_structure = Div(
            P(
                "Don't have an account? ", 
                A('Sign up here', href='#', cls='link link-hover text-teal-600 hover:text-teal-700 font-semibold'), 
                cls='text-gray-600' 
            ),
            cls='mt-6 text-center text-sm' 
        )

        # --- Card Body Content (with error message inserted) ---
        card_body_structure = Div(
            logo_section,
            H2('Welcome Back!', cls='card-title text-2xl md:text-3xl font-bold mb-1 text-gray-800'), 
            P('Please enter your details to log in.', cls='text-gray-500 mb-2'), # Adjusted margin
            error_message_component, # Insert the error message here
            login_form_structure, 
            signup_link_structure, 
            cls='card-body items-center text-center p-8 md:p-12' 
        )

        # --- Main Login Card Element ---
        login_page_main_content = Main( 
            card_body_structure,
            cls='card w-full max-w-md bg-base-100 shadow-xl' 
        )

        # --- Footer Element ---
        login_page_footer = Footer(
            '© 2024 Akasi.ai. All rights reserved.', 
            cls='text-center mt-8 text-xs text-gray-500' 
        )

        # --- Layout Wrapper for Centering (same as GET route) ---
        login_layout_wrapper = Div(
            login_page_main_content,
            login_page_footer,
            cls="flex flex-col items-center justify-center w-full min-h-screen px-4 py-8"
        )

        # Return the full page structure with the error
        return (
            Title("Login Error - Akasi.ai"), 
            login_layout_wrapper
        )

# --- CSS for Animations and Specific Styles ---
onboarding_styles_content = """
    /* Floating animation for the Akasi Ball */
    @keyframes floatAnimation {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    .floating-ball {
        width: 100px; /* Size of the ball */
        height: 100px;
        border-radius: 50%;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 3rem; /* Size of the letter 'A' */
        font-weight: bold;
        margin: 0 auto; /* Will be centered by parent's items-center */
        animation: floatAnimation 4s ease-in-out infinite;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1), 0 6px 6px rgba(0,0,0,0.15);
    }

    /* Styling for chat bubbles */
    .akasi-chat-bubble {
        transition: opacity 0.6s ease-out, transform 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
        opacity: 0;
        transform: translateY(30px) scale(0.9); 
    }
    .akasi-chat-bubble.show {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
    /* Fixed height for the message container */
    .message-area {
        height: 200px; 
        display: flex;
        flex-direction: column;
        justify-content: flex-start; /* Bubbles start from top */
        overflow: hidden; 
    }
"""

# --- JavaScript for Variation 1 Looping Bubbles ---
variation1_script_content = """
    const messages1 = [
        "Hello there! I'm Akasi.",
        "Your personal AI Guardian of Health and Wellness.",
        "Let's get you set up!"
    ];
    const messageContainer1 = document.getElementById('messageContainer1');
    const startButton1 = document.getElementById('startButton1');
    let currentMessageIndex1 = 0;
    let firstCycleComplete1 = false; 

    function showNextMessage1() {
        if (!messageContainer1) return;

        if (currentMessageIndex1 === 0) {
            messageContainer1.innerHTML = ''; 
        }

        if (currentMessageIndex1 < messages1.length) {
            const bubbleSide = 'chat-start'; 
            const bubbleColor = 'chat-bubble-primary'; 
            
            const chatDiv = document.createElement('div');
            chatDiv.className = `chat ${bubbleSide} akasi-chat-bubble w-full`;
            
            const bubbleDiv = document.createElement('div');
            bubbleDiv.className = `chat-bubble ${bubbleColor} text-white`; // DaisyUI classes
            bubbleDiv.textContent = messages1[currentMessageIndex1];
            
            chatDiv.appendChild(bubbleDiv);
            messageContainer1.appendChild(chatDiv);

            setTimeout(() => chatDiv.classList.add('show'), 50); 

            currentMessageIndex1++;
            setTimeout(showNextMessage1, 2000); 
        } else {
            if (!firstCycleComplete1 && startButton1) {
                startButton1.classList.remove('opacity-0');
                startButton1.classList.add('opacity-100');
                firstCycleComplete1 = true;
            }
            currentMessageIndex1 = 0; 
            setTimeout(showNextMessage1, 3500); 
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
             if (messageContainer1) setTimeout(showNextMessage1, 500);
        });
    } else {
        if (messageContainer1) setTimeout(showNextMessage1, 500);
    }
"""

@rt('/onboarding/personal-info')
def personal_info_page(auth): 
    if auth is None: 
        return RedirectResponse('/login', status_code=303)
    
    user_email = auth.get('email', 'User') 
    user_initial = user_email[0].upper() if user_email and len(user_email) > 0 else 'A'

    akasi_ball_v1 = Div(
        Span(user_initial), 
        id="akasiBall1", 
        cls="floating-ball bg-gradient-to-br from-teal-400 via-cyan-500 to-sky-600 mb-6" 
    )

    message_container_v1 = Div(
        id="messageContainer1",
        cls="message-area space-y-3 mb-8 w-full max-w-xs mx-auto" 
    )

    start_button_v1 = Button(
        "Let's Get Started",
        id="startButton1", 
        type="button",
        hx_get="/onboarding/personal-info/form", 
        hx_target="#onboarding-card-content", 
        hx_swap="innerHTML",
        # MODIFIED: Removed mt-auto, added mt-12 for specific top margin
        cls="btn btn-primary bg-teal-600 hover:bg-teal-700 border-none text-white text-lg px-8 py-3 rounded-lg shadow hover:shadow-lg transition-opacity duration-500 opacity-0 mt-12" 
    )

    main_card_content_variation1 = Div(
        akasi_ball_v1,
        message_container_v1,
        start_button_v1,
        id="onboarding-card-content", 
        # MODIFIED: Added justify-center to vertically center the content group
        cls="bg-base-100 p-8 md:p-12 rounded-xl shadow-2xl text-center flex flex-col items-center justify-center min-h-[600px]"
    )
    
    onboarding_main_wrapper_v1 = Main(
        main_card_content_variation1,
        cls="container mx-auto max-w-md w-full" 
    )
    
    page_layout_wrapper = Div(
        onboarding_main_wrapper_v1,
        cls="flex flex-col items-center justify-center w-full min-h-screen px-4 py-8"
    )
    
    return (
        Title("Personal Information - Akasi.ai Onboarding"),
        Style(onboarding_styles_content), 
        page_layout_wrapper,
        Script(variation1_script_content) 
    )

@rt('/onboarding/personal-info/form')
def form_view(auth): 
    if auth is None: 
        return Div("Authentication required.", cls="text-red-500 p-4 text-center") 

    form_title = H3(
        "Let's get to know you better",
        cls="text-xl md:text-2xl font-semibold text-gray-800 text-center mb-6" 
    )

    full_name_input = Div(
        Label(Span("Full name", cls="label-text text-gray-700"), For="fullName", cls="label"),
        Input(type="text", id="fullName", name="full_name", placeholder="e.g., Test User",
              cls="input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500", required=True)
    )

    dob_input = Div(
        Label(Span("Date of birth", cls="label-text text-gray-700"), For="dob", cls="label"),
        Input(type="date", id="dob", name="date_of_birth",
              cls="input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500", required=True)
    )

    gender_select = Div(
        Label(Span("Gender", cls="label-text text-gray-700"), For="gender", cls="label"),
        Select(
            Option("Select gender", value="", disabled=True, selected=True),
            Option("Male", value="male"),
            Option("Female", value="female"),
            Option("Other", value="other"),
            Option("Prefer not to say", value="prefer_not_to_say"),
            id="gender", name="gender",
            cls="select select-bordered select-primary w-full focus:ring-teal-500 focus:border-teal-500", required=True
        )
    )
    
    dob_gender_grid = Div(dob_input, gender_select, cls="grid md:grid-cols-2 gap-6")

    height_input = Div(
        Label(Span("Height (cm)", cls="label-text text-gray-700"), For="height", cls="label"),
        Input(type="number", id="height", name="height", placeholder="e.g., 170",
              cls="input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500", required=True)
    )

    weight_input = Div(
        Label(Span("Weight (kg)", cls="label-text text-gray-700"), For="weight", cls="label"),
        Input(type="number", id="weight", name="weight", placeholder="e.g., 60",
              cls="input input-bordered input-primary w-full focus:ring-teal-500 focus:border-teal-500", required=True)
    )

    height_weight_grid = Div(height_input, weight_input, cls="grid md:grid-cols-2 gap-6")
    
    ethnicity_select = Div(
        Label(Span("Ethnicity", cls="label-text text-gray-700"), For="ethnicity", cls="label"),
        Select(
            Option("Select ethnicity", value="", disabled=True, selected=True),
            Option("Filipino", value="filipino"), Option("Chinese", value="chinese"),
            Option("Japanese", value="japanese"), Option("Korean", value="korean"),
            Option("Indian", value="indian"), Option("Caucasian", value="caucasian"),
            Option("African Descent", value="african_descent"), Option("Hispanic/Latino", value="hispanic_latino"),
            Option("Middle Eastern", value="middle_eastern"), Option("Native American", value="native_american"),
            Option("Pacific Islander", value="pacific_islander"), Option("Mixed Race", value="mixed_race"),
            Option("Other", value="other"), Option("Prefer not to say", value="prefer_not_to_say"),
            id="ethnicity", name="ethnicity",
            cls="select select-bordered select-primary w-full focus:ring-teal-500 focus:border-teal-500", required=True
        )
    )

    form_submit_button = Div(
        Button("Continue", type="submit", id="confirm-personal-info",
               cls="btn btn-primary bg-teal-600 hover:bg-teal-700 border-none text-white w-full text-lg"),
        cls="pt-4" # Tailwind: padding-top: 1rem
    )

    personal_info_form = Form(
        full_name_input, dob_gender_grid, height_weight_grid, ethnicity_select, form_submit_button,
        id="personal-info-form", cls="space-y-6", method="post", action="/onboarding/personal-info"
    )
    
    form_container_for_swap = Div(
        form_title,
        personal_info_form,
        cls="w-full text-left" 
    )
    
    return form_container_for_swap


@rt('/onboarding/personal-info')
async def personal_info_submit(request, auth):
    if auth is None: return RedirectResponse('/login', status_code=303)
    
    form = await parse_form(request)
    print("Form data received:", form)
    
    # Get tokens from session
    user_id = auth.get('id')
    access_token = auth.get('access_token')
    refresh_token = auth.get('refresh_token')
    
    # Create authenticated client
    auth_client = use_auth_context(access_token, refresh_token)
    
    try:
        # Use authenticated client for database operations
        profile_data = {
            'user_id': user_id,
            'full_name': form.get('full_name'),
            'date_of_birth': form.get('date_of_birth'),
            'gender': form.get('gender'),
            'height': form.get('height'),
            'weight': form.get('weight'),
            'ethnicity': form.get('ethnicity'),
            'onboarding_step': 'wellness_journal'  # Update onboarding step
        }
        
        # Check if profile exists using authenticated client
        response = auth_client.table('user_profiles').select('*').eq('user_id', user_id).execute()
        
        if response.data and len(response.data) > 0:
            # Profile exists, update it
            auth_client.table('user_profiles').update(profile_data).eq('user_id', user_id).execute()
            print(f"Updated existing profile for user {user_id}")
        else:
            # Profile doesn't exist, create it
            auth_client.table('user_profiles').insert(profile_data).execute()
            print(f"Created new profile for user {user_id}")
            
    except Exception as e:
        print(f"Error managing profile: {str(e)}")

    # Process form data here and redirect to next step
    return RedirectResponse('/onboarding/wellness-journal', status_code=303)


# Styles needed for the dashboard
dashboard_styles = Style("""
    /* Custom scrollbar from akasi_dashboard_html */
    .scrollbar-thin { scrollbar-width: thin; scrollbar-color: #CBD5E1 #F3F4F6; }
    .scrollbar-thin::-webkit-scrollbar { width: 8px; height: 8px; }
    .scrollbar-thin::-webkit-scrollbar-track { background: #F3F4F6; border-radius: 10px;}
    .scrollbar-thin::-webkit-scrollbar-thumb { background-color: #CBD5E1; border-radius: 10px; border: 2px solid #F3F4F6; }
    .scrollbar-thin::-webkit-scrollbar-thumb:hover { background-color: #9CA3AF; }
    .shadow-top-md { box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.07), 0 -2px 4px -1px rgba(0, 0, 0, 0.04); }
    
    #dashboard-tab-content > * {
        transition: opacity 0.3s ease-out, transform 0.3s ease-out;
    }
    #dashboard-tab-content.htmx-settling > * {
        opacity: 0;
        transform: translateY(10px);
    }
    main.dashboard-main-content {
        padding-bottom: 80px; 
    }
    /* Style for emoji icons in buttons to ensure consistent size and alignment */
    .emoji-icon {
        font-size: 1.5em; /* Adjust size as needed */
        line-height: 1;
    }
    .btm-nav-button .emoji-icon { /* Specific for bottom nav if needed */
        font-size: 1.75em; /* Larger for bottom nav */
        margin-bottom: 0.125rem; /* Add a bit of space below emoji */
    }
    .top-nav-btn .emoji-icon {
        font-size: 1.3em;
    }
""")

# JavaScript for date and active tab management
dashboard_script_content = """
document.addEventListener('DOMContentLoaded', () => {
    function updateTodayDate() {
        const todayDateEl = document.getElementById('todayDate');
        if (todayDateEl) {
            const today = new Date();
            const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
            todayDateEl.textContent = today.toLocaleDateString('en-US', options);
        }
    }
    updateTodayDate(); 

    const bottomNavButtons = document.querySelectorAll('.btm-nav-button');
    const tabContentContainer = document.getElementById('dashboard-tab-content');

    bottomNavButtons.forEach(button => {
        button.addEventListener('click', function() {
            bottomNavButtons.forEach(btn => {
                btn.classList.remove('active', 'text-emerald-500'); 
                btn.classList.add('text-gray-500');
                // For emoji, we might not need to change SVG color, but if emoji is in a span, that span could be styled.
            });
            this.classList.add('active', 'text-emerald-500');
            this.classList.remove('text-gray-500');
        });
    });

    if (tabContentContainer) {
        tabContentContainer.addEventListener('htmx:afterSwap', function(event) {
            updateTodayDate(); 
            initializeMetricButtons(); 
            initializeReminderButtons();
            initializeJournalForm();
            initializeScannerButton();
        });
    }
    
    function initializeMetricButtons() { /* Placeholder */ }
    function initializeReminderButtons() {
        document.querySelectorAll('.complete-reminder-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const reminderItem = e.currentTarget.closest('.reminder-item');
                if (reminderItem) {
                    reminderItem.style.opacity = '0.5';
                    reminderItem.style.textDecoration = 'line-through';
                    e.currentTarget.disabled = true;
                }
            });
        });
    }
    function initializeJournalForm() { /* Placeholder */ }
    function initializeScannerButton() {
        const goBackToScannerBtn = document.getElementById('goBackToScannerBtn');
        if(goBackToScannerBtn) {
            goBackToScannerBtn.addEventListener('click', () => {
                 alert("This button would normally take you back to the scanner experience.");
            });
        }
    }
    
    initializeReminderButtons(); 
    initializeScannerButton();
});
"""

@rt('/home')
def home_page(auth):
    if auth is None: return RedirectResponse('/login', status_code=303)
    
    user_name = auth.get('display_name', 'Test User') 
    user_initial = user_name[0].upper() if user_name else 'A'

    top_nav_bar = Nav(
        Div(
            Div(
                Div(
                    Span('A', cls='text-white font-bold text-lg'),
                    cls='w-9 h-9 bg-white/30 rounded-full flex items-center justify-center'
                ),
                Span('akasi.ai', cls='text-white font-semibold ml-2.5 text-xl'),
                cls='flex items-center'
            ),
            Div(
                Button(Span("🔔", cls="emoji-icon"), aria_label="Notifications", cls='p-2 rounded-full hover:bg-white/20 text-white btn btn-ghost btn-circle top-nav-btn'),
                Div(user_initial, cls='w-9 h-9 bg-white/30 rounded-full flex items-center justify-center text-white font-semibold', aria_label="User Menu"),
                cls='flex items-center space-x-3'
            ),
            cls='max-w-4xl mx-auto flex justify-between items-center'
        ),
        cls='p-3 shadow-md bg-gradient-to-r from-green-500 to-emerald-500 sticky top-0 z-30'
    )

    main_content_area = Main(
        Div(
            Div(
                render_home_tab_content(user_name, auth), 
                id='dashboard-tab-content' 
            ),
            cls='max-w-4xl mx-auto'
        ),
        cls='flex-grow overflow-y-auto scrollbar-thin dashboard-main-content' 
    )

    tabs = [
        {'name': 'home', 'label': 'Home', 'emoji': '🏠', 'route': '/home/home-view'},
        {'name': 'journal', 'label': 'Journal', 'emoji': '📝', 'route': '/home/journal-view'},
        {'name': 'insights', 'label': 'Insights', 'emoji': '📊', 'route': '/home/insights-view'},
        {'name': 'profile', 'label': 'Profile', 'emoji': '👤', 'route': '/home/profile-view'}
    ]
    
    bottom_nav_buttons = [
        Button(
            Span(tab['emoji'], cls="emoji-icon"), 
            Span(tab['label'], cls='text-xs mt-1'),
            data_tab=tab['name'], 
            hx_get=tab['route'],
            hx_target="#dashboard-tab-content",
            hx_swap="innerHTML",
            cls=f"btm-nav-button p-2 flex flex-col items-center w-1/4 transition-colors {'text-emerald-500 active' if tab['name'] == 'home' else 'text-gray-500 hover:text-emerald-500'}"
        ) for tab in tabs
    ]

    bottom_nav_bar = Footer(
        Div(
            Div(*bottom_nav_buttons, cls='flex justify-around py-2'),
            cls='max-w-4xl mx-auto'
        ),
        cls='sticky bottom-0 left-0 right-0 bg-white shadow-top-md z-30 border-t border-gray-200'
    )

    page_shell = Div(
        top_nav_bar,
        main_content_area,
        bottom_nav_bar,
        cls="min-h-screen flex flex-col" 
    )

    return (
        Title("Akasi.ai Dashboard"),
        dashboard_styles, 
        page_shell,
        Script(dashboard_script_content) 
    )

@rt('/home/home-view')
def home_tab_view(auth):
    if auth is None: return Div("Not authenticated", cls="text-red-500 p-4")
    user_name = auth.get('display_name', 'Test User') 
    return render_home_tab_content(user_name, auth) 

def render_home_tab_content(user_name, auth_session_data):
    today = datetime.now()
    today_date_str = today.strftime("%A, %B %d, %Y") 

    health_metrics_card = Div(
        H2("Today's Health", cls="text-xl font-semibold mb-4 text-gray-700"),
        Div(
            Div(
                Div(Span("✅", cls="emoji-icon mr-1.5 text-emerald-500"), Span("Medications", cls="text-sm font-medium"), cls="flex items-center justify-center mb-1 text-gray-600"),
                Div(
                    Button("-", cls="metric-btn p-1 text-gray-400 hover:text-emerald-600 text-xl", data_metric="medicationsTaken", data_action="decrement", data_total="3"),
                    P("1/3", id="medicationsTaken", cls="text-2xl font-semibold text-emerald-600 mx-3"),
                    Button("+", cls="metric-btn p-1 text-gray-400 hover:text-emerald-600 text-xl", data_metric="medicationsTaken", data_action="increment", data_total="3"),
                    cls="flex justify-center items-center"
                )
            ),
            Div(
                Div(Span("😴", cls="emoji-icon mr-1.5 text-indigo-500"), Span("Sleep", cls="text-sm font-medium"), cls="flex items-center justify-center mb-1 text-gray-600"),
                P("6.5 hrs", id="sleepHours", cls="text-2xl font-semibold text-indigo-600")
            ),
            Div(
                Div(Span("💧", cls="emoji-icon mr-1.5 text-sky-500"), Span("Water", cls="text-sm font-medium"), cls="flex items-center justify-center mb-1 text-gray-600"),
                Div(
                    Button("-", cls="metric-btn p-1 text-gray-400 hover:text-sky-600 text-xl", data_metric="waterIntake", data_action="decrement", data_goal="8"),
                    P("4/8", id="waterIntake", cls="text-2xl font-semibold text-sky-600 mx-3"),
                    Button("+", cls="metric-btn p-1 text-gray-400 hover:text-sky-600 text-xl", data_metric="waterIntake", data_action="increment", data_goal="8"),
                    cls="flex justify-center items-center"
                )
            ),
            cls="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center"
        ),
        cls="bg-white rounded-xl shadow-lg p-5 mb-6"
    )

    reminders_card = Div(
        Div(H2("Reminders", cls="text-xl font-semibold text-gray-700"), Button("See all", cls="text-sm font-medium text-emerald-600 hover:text-emerald-700"), cls="flex justify-between items-center mb-4"),
        Div(
            Div(
                Div("12:30 PM", cls="mr-4 text-red-600 text-sm font-medium"),
                Div("Take Metformin with lunch", cls="flex-1 text-gray-700 text-sm"),
                Button(Span("✅", cls="emoji-icon"), cls="complete-reminder-btn p-2 text-gray-400 hover:text-emerald-700 rounded-full btn btn-ghost btn-sm btn-circle"),
                cls="reminder-item flex items-center p-3.5 border-l-4 border-red-500 bg-red-50 rounded-r-lg shadow-sm"
            ),
             Div(
                Div("3:00 PM", cls="mr-4 text-emerald-600 text-sm font-medium"),
                Div("Log afternoon symptoms", cls="flex-1 text-gray-700 text-sm"),
                Button(Span("✅", cls="emoji-icon"), cls="complete-reminder-btn p-2 text-gray-400 hover:text-emerald-700 rounded-full btn btn-ghost btn-sm btn-circle"),
                cls="reminder-item flex items-center p-3.5 border-l-4 border-emerald-500 bg-emerald-50 rounded-r-lg shadow-sm mt-3"
            ),
            # cls="space-y-3" # space-y-3 might not work as expected with direct Div children, using mt-3 on second item.
        ),
        cls="bg-white rounded-xl shadow-lg p-5 mb-6"
    )
    
    insights_card = Div(
        Div(H2("Akasi Insights", cls="text-xl font-semibold text-gray-700"), Span("New", cls="bg-gradient-to-r from-green-500 to-emerald-500 text-white text-xs px-2.5 py-1 rounded-full font-medium"), cls="flex justify-between items-center mb-4"),
        Div(
            Div(
                Div(Div(Span("ℹ️", cls="emoji-icon"),cls="w-8 h-8 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center"), cls="flex-shrink-0 mr-3 mt-0.5"),
                P("Your sleep pattern has improved by 12% this week.", cls="text-gray-700 text-sm"),
                cls="flex items-start p-3.5 bg-gray-50 rounded-lg"
            ),
            Div(
                Div(Div(Span("ℹ️", cls="emoji-icon"),cls="w-8 h-8 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center"), cls="flex-shrink-0 mr-3 mt-0.5"),
                P("Consider reducing caffeine - may be affecting your symptoms.", cls="text-gray-700 text-sm"),
                cls="flex items-start p-3.5 bg-gray-50 rounded-lg mt-3"
            ),
            # cls="space-y-3"
        ),
        cls="bg-white rounded-xl shadow-lg p-5 mb-6"
    )

    quick_actions = Div(
        Button(Span("➕", cls="emoji-icon"), Span("Log Symptoms", cls="font-medium text-sm mt-2"), data_tab="journal", cls="tab-button flex flex-col items-center justify-center p-4 bg-white rounded-xl shadow-lg hover:bg-gray-50 transition-colors text-emerald-600 hover:text-emerald-700"),
        Button(Span("📅", cls="emoji-icon"), Span("My Journal", cls="font-medium text-sm mt-2"), data_tab="journal", cls="tab-button flex flex-col items-center justify-center p-4 bg-white rounded-xl shadow-lg hover:bg-gray-50 transition-colors text-emerald-600 hover:text-emerald-700"),
        cls="grid grid-cols-2 gap-4"
    )

    return Div( 
        Div(
            P(today_date_str, id="todayDate", cls="text-gray-500 text-sm"),
            H1(f"Hello, {user_name}", cls="text-3xl font-semibold mb-1 text-gray-800"),
            P("How are you feeling today?", cls="text-gray-600"),
            Div(
                Button("😊 Good", data_mood="Good", cls="mood-btn px-4 py-2 rounded-lg bg-green-100 hover:bg-green-200 text-green-700 transition-colors"),
                Button("😐 Okay", data_mood="Okay", cls="mood-btn px-4 py-2 rounded-lg bg-yellow-100 hover:bg-yellow-200 text-yellow-700 transition-colors"),
                Button("😔 Not great", data_mood="Not Great", cls="mood-btn px-4 py-2 rounded-lg bg-red-100 hover:bg-red-200 text-red-700 transition-colors"),
                cls="flex space-x-2 mt-3"
            ),
            cls="mb-6"
        ),
        health_metrics_card,
        reminders_card,
        insights_card,
        quick_actions,
        cls="p-4" 
    )

@rt('/home/journal-view')
def journal_tab_view(auth):
    if auth is None: return Div("Not authenticated", cls="text-red-500 p-4")
    
    add_entry_form = Form(
        Div(Label("How are you feeling?", For="journalMood", cls="block text-sm font-medium text-gray-700 mb-1"),
            Select(Option("Select mood", value=""), Option("Good 😊", value="Good"), Option("Okay 😐", value="Okay"), Option("Not Great 😔", value="Not Great"), 
                   id="journalMood", name="mood", cls="w-full p-2 border border-gray-300 rounded-md focus:ring-emerald-500 focus:border-emerald-500"),
            cls="mb-4"),
        Div(Label("Symptoms", For="journalSymptoms", cls="block text-sm font-medium text-gray-700 mb-1"),
            Input(type="text", id="journalSymptoms", name="symptoms", placeholder="Cramping, Fatigue, etc. (comma-separated)", cls="w-full p-2 border border-gray-300 rounded-md focus:ring-emerald-500 focus:border-emerald-500"),
            cls="mb-4"),
        Div(Label("Medications Taken", For="journalMedications", cls="block text-sm font-medium text-gray-700 mb-1"),
            Input(type="text", id="journalMedications", name="medications", placeholder="Metformin (500mg), etc. (comma-separated)", cls="w-full p-2 border border-gray-300 rounded-md focus:ring-emerald-500 focus:border-emerald-500"),
            cls="mb-4"),
        Div(Label("Notes", For="journalNotes", cls="block text-sm font-medium text-gray-700 mb-1"),
            Textarea(name="notes", placeholder="How was your day? Any triggers or improvements?", rows="3", cls="w-full p-2 border border-gray-300 rounded-md focus:ring-emerald-500 focus:border-emerald-500", id="journalNotes"),
            cls="mb-4"),
        Button("Save Entry", type="submit", cls="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-2.5 px-4 rounded-md transition-colors"),
        id="newJournalForm",
        cls="space-y-4" 
    )

    add_entry_card = Div(
        H2("Add Today's Entry", cls="text-lg font-medium mb-4"),
        add_entry_form,
        cls="bg-white rounded-xl shadow-lg p-5 mb-6"
    )

    previous_entries_content = [
        Div(
            Div(Div("Wed, May 17, 2025", cls="font-semibold text-emerald-700"), Div("😊 Good", cls="text-sm text-gray-500"), cls="flex justify-between items-center mb-1.5"),
            P(Strong("Symptoms:", cls="text-gray-700"), " Feeling energetic", cls="text-sm text-gray-600"),
            P(Strong("Medications:", cls="text-gray-700"), " Vitamin C", cls="text-sm text-gray-600"),
            P(Strong("Notes:", cls="text-gray-700"), " Slept well, feeling positive today.", cls="text-sm text-gray-700 mt-1"),
            cls="border-b border-gray-200 pb-3 last:border-0 last:pb-0"
        )
    ]

    previous_entries_card = Div(
        H2("Previous Entries", cls="text-lg font-medium mb-4"),
        Div(*previous_entries_content, id="journalEntriesContainer", cls="space-y-4"),
        cls="bg-white rounded-xl shadow-lg p-5"
    )

    return Div(
        Div(
            Div(H1("Health Journal", cls="text-2xl font-semibold text-gray-800"), P("Track your daily health journey.", cls="text-gray-600")),
            Button(Span("🩺", cls="emoji-icon"), " AI Symptom Log", id="goBackToScannerBtn", cls="px-4 py-2 text-sm bg-emerald-500 hover:bg-emerald-600 text-white rounded-md transition-colors flex items-center gap-2 shadow-sm"),
            cls="mb-6 flex justify-between items-center"
        ),
        add_entry_card,
        previous_entries_card,
        cls="p-4"
    )

@rt('/home/insights-view')
def insights_tab_view(auth):
    if auth is None: return Div("Not authenticated", cls="text-red-500 p-4")
    return Div(
        H1("Insights Page (Placeholder)", cls="text-2xl font-semibold text-gray-800"),
        P("Full insights content will be implemented here.", cls="text-gray-600"),
        cls="p-4"
    )

@rt('/home/profile-view')
def profile_tab_view(auth):
    if auth is None: return Div("Not authenticated", cls="text-red-500 p-4")
    
    user_name = auth.get('display_name', 'Test User')
    user_email = auth.get('email', 'maria@example.com')
    user_initial = user_name[0].upper() if user_name else 'A'
    
    # --- Profile Header ---
    profile_header = Div(
        # Div( # Avatar
        #     Span(user_initial, cls="text-white font-bold"),
        #     cls="profile-avatar-large rounded-full bg-gradient-to-br from-teal-400 via-cyan-500 to-sky-600 flex items-center justify-center shadow-lg mb-4"
        # ),
        H2(user_email, cls="text-2xl font-bold text-gray-800"),
        # P(user_email, cls="text-gray-500 mb-6"),
        cls="flex flex-col items-center pt-6" # Added pt-6 for spacing from top of card
    )
    
    # --- Account Information Section ---
    account_info_section = Div(
        H3("Account Information", cls="text-lg font-semibold text-gray-700 mb-3"),
        Div(
            Div(Span("Full Name:", cls="font-medium text-gray-600"), Span(user_name, cls="text-gray-800"), cls="flex justify-between py-2 border-b border-gray-200"),
            Div(Span("Email:", cls="font-medium text-gray-600"), Span(user_email, cls="text-gray-800"), cls="flex justify-between py-2 border-b border-gray-200"),
            Div(Span("Joined:", cls="font-medium text-gray-600"), Span("May 17, 2024", cls="text-gray-800"), cls="flex justify-between py-2"), # Placeholder date
            cls="space-y-1 text-sm"
        ),
        Button(Span("✏️", cls="emoji-icon mr-2"), "Edit Profile", cls="btn btn-outline btn-primary btn-sm mt-4 w-full md:w-auto"),
        cls="bg-white p-6 rounded-xl shadow-lg mb-6"
    )

    # --- Preferences Section ---
    preferences_section = Div(
        H3("Preferences", cls="text-lg font-semibold text-gray-700 mb-3"),
        Div( # Theme Toggle
            Label(
                Span("Dark Mode", cls="label-text text-gray-700"),
                Input(type="checkbox", id="themeToggle", cls="toggle toggle-primary"), 
                cls="label cursor-pointer"
            ),
            cls="form-control"
        ),
        Div( # Notification Preferences (Conceptual)
            Label(Span("Email Notifications", cls="label-text text-gray-700"), cls="label"),
            Select(
                Option("All", value="all"),
                Option("Important Only", value="important"),
                Option("None", value="none"),
                cls="select select-bordered select-primary w-full text-sm"
            ),
            cls="form-control mt-2"
        ),
        cls="bg-white p-6 rounded-xl shadow-lg mb-6"
    )
    
    # --- Security Section ---
    security_section = Div(
        H3("Security", cls="text-lg font-semibold text-gray-700 mb-3"),
        Button(Span("🔑", cls="emoji-icon mr-2"),"Change Password", cls="btn btn-outline btn-secondary w-full md:w-auto btn-sm"),
        cls="bg-white p-6 rounded-xl shadow-lg mb-6"
    )

    # --- Logout Section ---
    logout_section = Div(
        # Using a Form for logout to potentially handle POST request for CSRF protection etc.
        Form(
            Button(Span("🚪", cls="emoji-icon mr-2"), "Logout", type="submit", cls="btn btn-error text-white w-full"),
            method="post", # Or GET, depending on your logout implementation
            action="/logout" # Ensure you have a /logout route
        ),
        cls="mt-4" # Added margin-top to separate from security section
    )

    return Div(
        H1("My Profile", cls="text-3xl font-bold text-gray-800 mb-8 text-center"),
        profile_header,
        account_info_section,
        preferences_section,
        security_section,
        logout_section,
        cls="p-4 space-y-6" # Main padding and spacing for profile content sections
    )

@rt('/logout')
def get(sess):
    supabase.auth.sign_out()
    if 'user' in sess: del sess['user']
    return RedirectResponse('/', status_code=303)

@rt('/logout')
def post(sess):
    supabase.auth.sign_out()
    if 'user' in sess: del sess['user']
    return RedirectResponse('/', status_code=303)

serve()