import datetime
from datetime import datetime 
from fasthtml.svg import Svg, Defs, Pattern, Path, Rect, Text, NotStr, Ellipse, Circle, Group, G
from fasthtml.common import *
# Ensure all necessary SVG elements are imported
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from pathlib import Path
import json
from services.sb_user_services import fetch_user_profile # Assuming this path is correct relative to your project structure
from fasthtml.core import RedirectResponse




# --- Configuration ---
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

supabase_url = os.getenv("SUPABASE_URL")
supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_anon_key)

def use_auth_context(access_token, refresh_token=None):
    """Set authentication context on the global client for the current request"""
    # Create a new instance with authentication context
    client = create_client(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_ANON_KEY")
    )
    
    # Set the session with the token
    client.auth.set_session(access_token, refresh_token)
    
    return client

# --- Authentication Beforeware ---
def auth_before(req, sess):
    auth = req.scope['auth'] = sess.get('user', None)
    if not auth and req.url.path == '/home':
        return RedirectResponse('/login', status_code=303)

beforeware = Beforeware(
    auth_before,
    skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', r'.*\.js', '/login', '/signup', '/']
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
            Ellipse(cx="100", cy="40", rx="35", ry="30", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="head_group", cls="body-part", data_name="Head", data_info="The head contains the brain, eyes, ears, nose, and mouth. It is crucial for sensory input and cognitive functions."
        ),
        G( # Neck
            Rect(x="90", y="70", width="20", height="15", rx="2", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="neck_group", cls="body-part", data_name="Neck", data_info="The neck connects the head to the torso and houses the cervical spine, esophagus, and trachea."
        ),
        G( # Thorax
            Rect(x="60", y="85", width="80", height="75", rx="10", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="thorax_group", cls="body-part", data_name="Thorax (Chest)", data_info="The thorax, or chest, is the part of the torso between the neck and the abdomen. It houses the heart and lungs."
        ),
        G( # Lungs
            Ellipse(cx="85", cy="115", rx="18", ry="25", fill=internal_organ_fill, stroke=internal_organ_stroke, stroke_width=default_stroke_width, fill_opacity=internal_organ_fill_opacity),
            Ellipse(cx="115", cy="115", rx="18", ry="25", fill=internal_organ_fill, stroke=internal_organ_stroke, stroke_width=default_stroke_width, fill_opacity=internal_organ_fill_opacity),
            id="lungs_group", cls="body-part internal-organ", data_name="Lungs", data_info="The lungs are the primary organs of the respiratory system, responsible for oxygenating blood."
        ),
        G( # Heart
            Ellipse(cx="100", cy="120", rx="15", ry="15", style=f"fill: {heart_fill};", stroke=heart_stroke, stroke_width=default_stroke_width, fill_opacity=internal_organ_fill_opacity), # Retain specific heart fill, add stroke
            id="heart_group", cls="body-part internal-organ", data_name="Heart", data_info="The heart is a muscular organ that pumps blood throughout the body via the circulatory system."
        ),
        G( # Abdominal and Pelvic Region
            Rect(x="60", y="160", width="80", height="60", rx="10", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="abdominal_pelvic_region_group", cls="body-part", data_name="Abdominal and Pelvic Region", data_info="This region includes the abdomen and pelvis. It houses major organs of the digestive, urinary, and reproductive systems (e.g., stomach, intestines, liver, kidneys, bladder, reproductive organs)."
        ),
        G( # Left Shoulder
            Circle(cx="60", cy="95", r="12", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="left_shoulder_group", cls="body-part", data_name="Left Shoulder", data_info="The left shoulder joint connects the left arm to the torso."
        ),
        G( # Right Shoulder
            Circle(cx="140", cy="95", r="12", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="right_shoulder_group", cls="body-part", data_name="Right Shoulder", data_info="The right shoulder joint connects the right arm to the torso."
        ),
        G( # Left Arm
            Rect(x="25", y="95", width="30", height="70", rx="5", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="left_arm_group", cls="body-part", data_name="Left Arm", data_info="The left arm is used for reaching, grasping, and interacting with the environment."
        ),
        G( # Right Arm
            Rect(x="145", y="95", width="30", height="70", rx="5", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="right_arm_group", cls="body-part", data_name="Right Arm", data_info="The right arm, similar to the left, facilitates interaction and manipulation of objects."
        ),
        G( # Left Hand
            Ellipse(cx="40", cy="170", rx="12", ry="8", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="left_hand_group", cls="body-part", data_name="Left Hand", data_info="The left hand is at the end of the left arm, used for manipulation."
        ),
        G( # Right Hand
            Ellipse(cx="160", cy="170", rx="12", ry="8", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="right_hand_group", cls="body-part", data_name="Right Hand", data_info="The right hand is at the end of the right arm, used for manipulation."
        ),
        G( # Left Leg
            Rect(x="70", y="220", width="25", height="70", rx="5", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="left_leg_group", cls="body-part", data_name="Left Leg", data_info="The left leg supports the body and enables locomotion."
        ),
        G( # Right Leg
            Rect(x="105", y="220", width="25", height="70", rx="5", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="right_leg_group", cls="body-part", data_name="Right Leg", data_info="The right leg provides support and mobility."
        ),
        G( # Left Foot
            Ellipse(cx="82.5", cy="295", rx="15", ry="8", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
            id="left_foot_group", cls="body-part", data_name="Left Foot", data_info="The left foot is at the end of the left leg, crucial for standing and walking."
        ),
        G( # Right Foot
            Ellipse(cx="117.5", cy="295", rx="15", ry="8", fill=default_body_fill, stroke=default_body_stroke, stroke_width=default_stroke_width),
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
@rt('/onboarding/wellness-journal')
def get(auth):
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
                    P("This is the first AI response.", cls="text-sm leading-relaxed chat-message-text"),
                    cls="chat-bubble chat-bubble-neutral bg-base-300 text-base-content rounded-bl-none shadow-md"
                ),
                cls="flex items-end max-w-xs sm:max-w-md md:max-w-lg"
            ),
            cls="flex justify-start"
        ),
        Div(
            Div(
                Div(
                    Div(
                        Span("person", cls="material-icons emoji-icon"),
                        cls="bg-transparent text-neutral-content rounded-full w-8 h-8 text-sm flex items-center justify-center"
                    ),
                    cls="avatar placeholder p-0 w-8 h-8 rounded-full ml-2 user-message-gradient"
                ),
                Div(
                    P("Hello Akasi!", cls="text-sm leading-relaxed chat-message-text"),
                    cls="chat-bubble chat-bubble-primary user-message-gradient rounded-br-none shadow-md"
                ),
                cls="flex items-end max-w-xs sm:max-w-md md:max-w-lg flex-row-reverse"
            ),
            cls="flex justify-end"
        ),
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
                    P("Here's a response to your query about images.", cls="text-sm leading-relaxed chat-message-text"),
                    cls="chat-bubble chat-bubble-neutral bg-base-300 text-base-content rounded-bl-none shadow-md"
                ),
                cls="flex items-end max-w-xs sm:max-w-md md:max-w-lg"
            ),
            cls="flex justify-start"
        ),
        Div(
            Div(
                Div(
                    Div(
                        Span("person", cls="material-icons emoji-icon"),
                        cls="bg-transparent text-neutral-content rounded-full w-8 h-8 text-sm flex items-center justify-center"
                    ),
                    cls="avatar placeholder p-0 w-8 h-8 rounded-full ml-2 user-message-gradient"
                ),
                Div(
                    P("Okay, check out these images.", cls="text-sm leading-relaxed chat-message-text"),
                    Div(
                        Div(
                            Div(
                                Img(src="https://placehold.co/100x75/A7F3D0/10B981?text=Img1", alt="Attached image 1", cls="rounded max-w-full h-auto max-h-32 object-contain", onerror="this.onerror=null; this.src='https://placehold.co/100x75/FEE2E2/DC2626?text=Error';"),
                                P("image_sample_1.jpg (78 KB)", cls="text-xs text-base-content/70 mt-1 truncate")
                            ),
                            cls="p-1.5 rounded-md bg-base-100/50 border border-base-300/50"
                        ),
                        Div(
                            Div(
                                Img(src="https://placehold.co/100x75/A7F3D0/10B981?text=Img2", alt="Attached image 2", cls="rounded max-w-full h-auto max-h-32 object-contain", onerror="this.onerror=null; this.src='https://placehold.co/100x75/FEE2E2/DC2626?text=Error';"),
                                P("photo_of_rash.png (120 KB)", cls="text-xs text-base-content/70 mt-1 truncate")
                            ),
                            cls="p-1.5 rounded-md bg-base-100/50 border border-base-300/50"
                        ),
                        Div(
                            Div(
                                Img(src="https://placehold.co/100x75/A7F3D0/10B981?text=Img3", alt="Attached image 3", cls="rounded max-w-full h-auto max-h-32 object-contain", onerror="this.onerror=null; this.src='https://placehold.co/100x75/FEE2E2/DC2626?text=Error';"),
                                P("scan_result_view.jpeg (95 KB)", cls="text-xs text-base-content/70 mt-1 truncate")
                            ),
                            cls="p-1.5 rounded-md bg-base-100/50 border border-base-300/50"
                        ),
                        cls="mt-2 pt-2 space-y-2 border-t border-green-400/50"
                    ),
                    cls="chat-bubble chat-bubble-primary user-message-gradient rounded-b-xl shadow-md"
                ),
                cls="flex items-end max-w-xs sm:max-w-md md:max-w-lg flex-row-reverse"
            ),
            cls="flex justify-end"
        ),
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
                    P("Understood. And for the documents?", cls="text-sm leading-relaxed chat-message-text"),
                    cls="chat-bubble chat-bubble-neutral bg-base-300 text-base-content rounded-bl-none shadow-md"
                ),
                cls="flex items-end max-w-xs sm:max-w-md md:max-w-lg"
            ),
            cls="flex justify-start"
        ),
        Div(
            Div(
                Div(
                    Div(
                        Span("person", cls="material-icons emoji-icon"),
                        cls="bg-transparent text-neutral-content rounded-full w-8 h-8 text-sm flex items-center justify-center"
                    ),
                    cls="avatar placeholder p-0 w-8 h-8 rounded-full ml-2 user-message-gradient"
                ),
                Div(
                    P("And here are some PDF documents.", cls="text-sm leading-relaxed chat-message-text"),
                    Div(
                        Div(
                            Div(
                                Span("attachment", cls="material-icons emoji-icon text-xl text-primary flex-shrink-0"),
                                Div(
                                    P("lab_results_q1.pdf", cls="text-xs font-medium text-base-content/90 truncate"),
                                    P("256 KB", cls="text-xs text-base-content/70"),
                                    cls="flex-grow overflow-hidden"
                                ),
                                cls="flex items-center gap-2"
                            ),
                            cls="p-1.5 rounded-md bg-base-100/50 border border-base-300/50"
                        ),
                        Div(
                            Div(
                                Span("attachment", cls="material-icons emoji-icon text-xl text-primary flex-shrink-0"),
                                Div(
                                    P("medical_history_summary.pdf", cls="text-xs font-medium text-base-content/90 truncate"),
                                    P("512 KB", cls="text-xs text-base-content/70"),
                                    cls="flex-grow overflow-hidden"
                                ),
                                cls="flex items-center gap-2"
                            ),
                            cls="p-1.5 rounded-md bg-base-100/50 border border-base-300/50"
                        ),
                        Div(
                            Div(
                                Span("attachment", cls="material-icons emoji-icon text-xl text-primary flex-shrink-0"),
                                Div(
                                    P("prescription_details.pdf", cls="text-xs font-medium text-base-content/90 truncate"),
                                    P("128 KB", cls="text-xs text-base-content/70"),
                                    cls="flex-grow overflow-hidden"
                                ),
                                cls="flex items-center gap-2"
                            ),
                            cls="p-1.5 rounded-md bg-base-100/50 border border-base-300/50"
                        ),
                        cls="mt-2 pt-2 space-y-2 border-t border-green-400/50"
                    ),
                    cls="chat-bubble chat-bubble-primary user-message-gradient rounded-b-xl shadow-md"
                ),
                cls="flex items-end max-w-xs sm:max-w-md md:max-w-lg flex-row-reverse"
            ),
            cls="flex justify-end"
        ),
        id="messagesArea",
        cls="flex-grow p-3 sm:p-4 space-y-3 overflow-y-auto bg-base-200 scrollbar-thin"
    )

    chat_input_area = Div(
        Div(id="stagedAttachmentsContainer", cls="mb-2 p-2 border border-base-300 rounded-lg bg-base-200 max-h-32 overflow-y-auto scrollbar-thin space-y-2 hidden"),
        Div(
            Div(
                Button(
                    Span("add", cls="material-icons emoji-icon text-2xl"),
                    id="attachmentButton", tabindex="0", role="button", title="Attach files",
                    cls="btn btn-ghost btn-circle text-primary"
                ),
                Div(
                    Button(
                        Span("image", cls="material-icons emoji-icon"), " Attach Image(s)",
                        id="attachImageButton", cls="btn btn-sm btn-ghost justify-start gap-2"
                    ),
                    Button(
                        Span("article", cls="material-icons emoji-icon"), " Attach Document(s)",
                        id="attachDocumentButton", cls="btn btn-sm btn-ghost justify-start gap-2"
                    ),
                    id="attachmentOptionsContent", tabindex="0",
                    cls="dropdown-content z-[20] menu p-2 shadow bg-base-100 rounded-box w-56 mb-2"
                ),
                id="attachmentOptionsDropdownContainer", cls="dropdown dropdown-top"
            ),
            Input(type="file", multiple=True, id="fileInput", cls="hidden"),
            Textarea(id="chatInput", placeholder="Describe your symptoms here...", cls="textarea textarea-bordered flex-grow resize-none scrollbar-thin", rows="1", style="min-height: 44px; max-height: 120px;"),
            Button(
                Span("send", cls="material-icons emoji-icon text-xl"),
                id="sendButton", cls="btn btn-primary btn-circle"
            ),
            cls="flex items-end space-x-2 sm:space-x-3"
        ),
        cls="bg-base-100 p-3 sm:p-4 shadow-inner border-t border-base-300"
    )

    left_panel_chatbox = Div(
        Div(
            chatbox_header,
            messages_area,
            Div(id="messagesEndRef", cls="h-0"),
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
            Button("Start Scan", id="debugStartScanButton", cls="btn primary-green-gradient",
                hx_get="/trigger_body_scan_animation_script", hx_target="#script_runner_area", hx_swap="innerHTML"),

            Button("Stop Scan", id="debugStopScanButton", cls="btn primary-green-gradient",
                hx_get="/trigger_stop_body_scan_script", hx_target="#script_runner_area", hx_swap="innerHTML"),

            Button("Narrow Scan", id="debugNarrowScanButton", cls="btn primary-green-gradient",
            hx_get="/js_show_narrow_scan_modal", hx_target="#script_runner_area", hx_swap="innerHTML"),

            Button("Full Body Glow", id="debugFullBodyGlowButton", cls="btn primary-green-gradient",
                hx_get="/trigger_body_glow_script", hx_target="#script_runner_area", hx_swap="innerHTML"),

            cls="grid grid-cols-2 sm:grid-cols-4 gap-2 w-full max-w-md px-2"
        ),
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
                cls="btn btn-sm w-full flex items-center justify-center gap-2 primary-green-gradient"
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
            *journal_entries_list_items,
            id="journalEntriesList",
            cls="flex-grow overflow-y-auto p-3 space-y-2.5 scrollbar-thin"
        ),
        Div(
            Button(
                Span("delete_sweep", cls="material-icons emoji-icon mr-1"), " Clear All",
                id="clearAllJournalButton",
                cls="btn btn-xs btn-outline btn-error flex items-center gap-1.5",
                title="Clear all journal entries"
            ),
            id="clearJournalContainer",
            cls="p-2.5 border-t border-primary/30 flex justify-end",
            style="display: flex;"
        ),
        cls="w-full md:w-2/5 lg:w-1/3 h-full border-l border-primary/30 flex flex-col bg-base-100/50"
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

    manual_entry_modal = Dialog(
        Div(
            Form(
                Button(
                    Span("close", cls="material-icons emoji-icon"),
                    id="closeManualEntryModalButton",
                    cls="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
                ),
                method="dialog"
            ),
            H3("Add Manual Journal Entry", cls="font-bold text-lg mb-4"),
            Form(
                Div(
                    Label("Title / Body Part", For="manualTitle", cls="block text-xs font-medium text-base-content/80 mb-1"),
                    Input(type="text", id="manualTitle", name="title", placeholder="E.g., Headache, Stomach Ache", cls="input input-bordered input-sm w-full", required=True),
                    cls="mb-3"
                ),
                Div(
                    Label("Status / Severity", For="manualStatus", cls="block text-xs font-medium text-base-content/80 mb-1"),
                    Select(
                        Option("Low", value="1"),
                        Option("Medium", value="2"),
                        Option("High", value="3"),
                        id="manualStatus", name="status", cls="select select-bordered select-sm w-full"
                    ),
                    cls="mb-3"
                ),
                Div(
                    Label("Summary / Description", For="manualSummary", cls="block text-xs font-medium text-base-content/80 mb-1"),
                    Textarea(id="manualSummary", name="summary", placeholder="Describe the issue or feeling...", rows="3", cls="textarea textarea-bordered textarea-sm w-full", required=True),
                    cls="mb-3"
                ),
                Div(
                    Label("Date", For="manualDate", cls="block text-xs font-medium text-base-content/80 mb-1"),
                    Input(type="date", id="manualDate", name="date", cls="input input-bordered input-sm w-full", required=True),
                    cls="mb-4"
                ),
                Div(
                    Button("Cancel", type="button", id="cancelManualEntryButton", cls="btn btn-sm btn-ghost"),
                    Button("Save Entry", type="submit", id="saveManualEntryButton", cls="btn btn-sm btn-primary"),
                    cls="flex justify-end gap-2 modal-action mt-0"
                ),
                id="manualEntryForm"
            ),
            cls="modal-box"
        ),
        Form(Button("close"), method="dialog", cls="modal-backdrop"),
        id="manualEntryModal", cls="modal"
    )

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




# Landing Page
@rt('/')
def get():
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
def get(sess):
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
async def post(req, sess):
    form = await parse_form(req)
    # Match field names to the new form: fullName, email, password, confirmPassword, terms
    display_name = form.get('fullName') # Changed from 'display_name' to 'fullName'
    email = form.get('email')
    password = form.get('password')
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
        if res.user:
            user = res.user
            
            sess['user'] = {
                'id': user.id, 
                'email': user.email,
                'display_name': display_name, # Storing the display_name/fullName
                'access_token': res.session.access_token,
                'refresh_token': res.session.refresh_token
            }
            
            auth_client = use_auth_context(res.session.access_token, res.session.refresh_token)
                                    
            return RedirectResponse('/onboarding/personal-info', status_code=303)
        else:
            # This case might indicate an issue with the signup response even if no exception was thrown
            # Or if res.user is None for some other reason (e.g., email confirmation required)
            # Re-render form with a generic error or a specific one if available from `res`
            error_message = "Signup was not successful. Please try again."
            if hasattr(res, 'error') and res.error:
                error_message = res.error.message
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
def get(sess):
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
async def post(req, sess): # Changed to req, sess to match common FastHTML patterns
    form = await parse_form(req)
    email = form.get('email')
    password = form.get('password')
    
    try:
        # User's existing Supabase login logic - REMAINS UNCHANGED
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        sess['user'] = {
            'id': res.user.id, 
            'email': res.user.email,
            'access_token': res.session.access_token,
            'refresh_token': res.session.refresh_token
        }
        
        auth_client = use_auth_context(res.session.access_token, res.session.refresh_token)
        
        try:
            user_profile = fetch_user_profile(auth_client, res.user.id)
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
def get(auth): 
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
        Input(type="text", id="fullName", name="full_name", placeholder="e.g., Maria Cruz",
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
async def post(request, auth):
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
def get(auth):
    if auth is None: return RedirectResponse('/login', status_code=303)
    
    user_name = auth.get('display_name', 'Maria') 
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
    user_name = auth.get('display_name', 'Maria') 
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
    
    user_name = auth.get('display_name', 'Maria')
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