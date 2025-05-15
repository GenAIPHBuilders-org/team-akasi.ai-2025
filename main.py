from fasthtml.common import *
from fasthtml.svg import Svg, Path
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from pathlib import Path
import json
from services.sb_user_services import fetch_user_profile

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
    pico=True,  # Enable PicoCSS
    debug=True,
    static_path='static',
    hdrs=(
        Link(rel='stylesheet', href='/css/custom.css'),  # Keep custom CSS if needed

    )
)

# --- Routes ---

# Landing Page
@rt('/')
def get():


    landing_script = Script(src='/js/landing_animation.js', defer=True)
    avatar_circle = Div('A', cls="avatar-circle")
    chat_bubble = Div(P(id="akasi-message"), cls="chat-bubble")
    
    # Gradient buttons with inline styles
    button_row = Div(
        A("Create Account", 
          href="/signup", 
          role="button",
          style="background: linear-gradient(45deg, #4287f5, #2961cc); border: none; color: white; padding: 0.75rem 1.5rem;"),
        
        A("Login", 
          href="/login", 
          role="button",
          style="background: linear-gradient(45deg, #676767, #404040); border: none; color: white; padding: 0.75rem 1.5rem;"),
        
        style="display: flex; gap: 1rem; justify-content: center; margin-top: 2rem;"
    )

    # Container for all landing content
    landing_content = Div(
        H1("Welcome to Akasi.ai", style="color: black; text-align: center; margin-bottom: 5rem;"),
        avatar_circle, 
        chat_bubble, 
        button_row,
        landing_script,
        style="max-width: 600px; width: 100%; margin: 0 auto; text-align: center;"
    )

    main_wrapper = Main(
        landing_content,
        cls="container",
        style="min-height: 100vh; display: flex; align-items: center; justify-content: center; transform: translateY(-15%);"

    )

    return (
        Title("Welcome to Akasi.ai"),
        main_wrapper
    )


@rt('/signup')
def get(sess):
    # Check if user is already logged in
    auth = sess.get('user', None)
    if auth:
        return RedirectResponse('/home', status_code=303)

    # Light-themed form using data-theme attribute with Display Name field
    signup_form = Form(
        Article(
            Div(
                Label("Display Name", For="displayNameInput"),
                Input(type="text", name="display_name", required=True, id="displayNameInput")
            ),
            Div(
                Label("Email address", For="emailInput"),
                Input(type="email", name="email", required=True, id="emailInput")
            ),
            Div(
                Label("Password", For="passwordInput"),
                Input(type="password", name="password", required=True, id="passwordInput")
            ),
            Button("Sign Up", type="submit", role="button"),
            data_theme="light"
        ),
        method="post", 
        action="/signup"
    )
    
    login_link_section = Div(
        P("Already have an account? ", A("Login", href="/login"), style="color: black;")
    )

    # Container with H1 title and form
    content = Div(
        H1("Akasi.ai | Signup", style="color: black; text-align: center; margin-bottom: 2rem;"),
        signup_form,
        login_link_section,
        style="max-width: 400px; width: 100%; margin: 0 auto;"
    )
    
    # Main wrapper that centers vertically
    main_wrapper = Main(
        content, 
        cls="container",
        style="min-height: 100vh; display: flex; align-items: center; justify-content: center; transform: translateY(-10%);"
    )
    
    return (
        Title("Sign Up"),
        main_wrapper
    )


@rt('/signup')
async def post(req, sess):
    form = await parse_form(req)
    display_name = form.get('display_name')
    email = form.get('email')
    password = form.get('password')
    
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            user = res.user
            
            # Store both tokens and user info in session
            sess['user'] = {
                'id': user.id, 
                'email': user.email,
                'display_name': display_name,
                'access_token': res.session.access_token,
                'refresh_token': res.session.refresh_token
            }
            
            # For database operations after signup, use authenticated client
            auth_client = use_auth_context(res.session.access_token, res.session.refresh_token)
                           
            return RedirectResponse('/onboarding/personal-info', status_code=303)
        else:
            return RedirectResponse('/login', status_code=303)
        
    except Exception as e:
        # Error UI matching the GET route
        print(e)
        error_alert = Article(
            Header(Strong("Signup Error!")),
            P(f"An error occurred: {str(e)}"),
            role="alert",
            data_theme="light"
        )
        
        signup_form = Form(
            Article(
                error_alert,
                Div(
                    Label("Display Name", For="displayNameInput"),
                    Input(type="text", name="display_name", required=True, id="displayNameInput", value=display_name or '')
                ),
                Div(
                    Label("Email address", For="emailInput"),
                    Input(type="email", name="email", required=True, id="emailInput", value=email or '')
                ),
                Div(
                    Label("Password", For="passwordInput"),
                    Input(type="password", name="password", required=True, id="passwordInput")
                ),
                Button("Sign Up", type="submit", role="button"),
                data_theme="light"
            ),
            method="post", 
            action="/signup"
        )
        
        login_link_section = Div(
            P("Already have an account? ", A("Login", href="/login"), style="color: black;")
        )

        # Container with H1 title and form - matching GET route
        content = Div(
            H1("Akasi.ai | Signup", style="color: black; text-align: center; margin-bottom: 2rem;"),
            signup_form,
            login_link_section,
            style="max-width: 400px; width: 100%; margin: 0 auto;"
        )
        
        # Main wrapper that centers vertically - matching GET route
        main_wrapper = Main(
            content, 
            cls="container",
            style="min-height: 100vh; display: flex; align-items: center; justify-content: center; transform: translateY(-10%);"
        )
        
        return (
            Title("Signup Error"),
            main_wrapper
        )


@rt('/login')
def get(sess):
    # Check if user is already logged in
    auth = sess.get('user', None)
    if auth:
        return RedirectResponse('/home', status_code=303)
    
    # Light-themed form using data-theme attribute
    login_form = Form(
        Article(
            Div(
                Label("Email address", For="emailInputLogin"),
                Input(type="email", name="email", required=True, id="emailInputLogin")
            ),
            Div(
                Label("Password", For="passwordInputLogin"),
                Input(type="password", name="password", required=True, id="passwordInputLogin")
            ),
            Button("Login", type="submit", role="button"),
            data_theme="light"
        ),
        method="post", 
        action="/login"
    )
    
    signup_link_section = Div(
        P("Don't have an account? ", A("Sign Up", href="/signup"), style="color: black;")
    )

    # Container with H1 title and form
    content = Div(
        H1("Akasi.ai | Login", style="color: black; text-align: center; margin-bottom: 2rem;"),
        login_form,
        signup_link_section,
        style="max-width: 400px; width: 100%; margin: 0 auto;"
    )
    
    # Main wrapper that centers vertically
    main_wrapper = Main(
        content, 
        cls="container",
        style="min-height: 100vh; display: flex; align-items: center; justify-content: center; transform: translateY(-10%);"
    )
    
    return (
        Title("Login"),
        main_wrapper
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
async def post(req, sess):
    form = await parse_form(req)
    email = form.get('email')
    password = form.get('password')
    
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        # Store both tokens and user info in session
        sess['user'] = {
            'id': res.user.id, 
            'email': res.user.email,
            'access_token': res.session.access_token,
            'refresh_token': res.session.refresh_token
        }
        
        # Create an authenticated client using the token
        auth_client = use_auth_context(res.session.access_token, res.session.refresh_token)
        
        try:
            # Use authenticated client to fetch user profile
            user_profile = fetch_user_profile(auth_client, res.user.id)
            current_onboarding_step = user_profile.get('onboarding_step', 'personal_info')
        except Exception as e:
            print(f"Error fetching profile: {str(e)}")
            current_onboarding_step = 'personal_info'  # Default to first step
        
        redirect_url = get_onboarding_redirect(current_onboarding_step)
        return RedirectResponse(redirect_url, status_code=303)
    
    except Exception as e:
        # Error UI matching the GET route
        error_alert = Article(
            Header(Strong("Login Error!")),
            P(f"{str(e)}"),
            role="alert",
            data_theme="light"
        )
        
        login_form = Form(
            Article(
                error_alert,
                Div(
                    Label("Email address", For="emailInputLogin"),
                    Input(type="email", name="email", required=True, id="emailInputLogin", value=email or '')
                ),
                Div(
                    Label("Password", For="passwordInputLogin"),
                    Input(type="password", name="password", required=True, id="passwordInputLogin")
                ),
                Button("Login", type="submit", role="button"),
                data_theme="light"
            ),
            method="post", 
            action="/login"
        )
        
        signup_link_section = Div(
            P("Don't have an account? ", A("Sign Up", href="/signup"), style="color: black;")
        )

        # Container with H1 title and form - matching GET route
        content = Div(
            H1("Akasi.ai | Login", style="color: black; text-align: center; margin-bottom: 2rem;"),
            login_form,
            signup_link_section,
            style="max-width: 400px; width: 100%; margin: 0 auto;"
        )
        
        # Main wrapper that centers vertically - matching GET route
        main_wrapper = Main(
            content, 
            cls="container",
            style="min-height: 100vh; display: flex; align-items: center; justify-content: center; transform: translateY(-10%);"
        )
        
        return (
            Title("Login Error"),
            main_wrapper
        )


@rt('/onboarding/personal-info')
def get(auth):
    if auth is None: return RedirectResponse('/login', status_code=303)
    
    user_id = auth.get('id')
    user_email = auth.get('email', 'A')
    user_initial = user_email[0].upper() if user_email else 'A'
    
    # Initial view - only show avatar, greeting, and start button
    initial_view = Div(
        H1("Akasi.ai | Personal Information", style="color: black; text-align: center; margin-bottom: 2rem;"),
        Article(
            Div(user_initial, cls="avatar-circle", style="margin: 0 auto 1rem; width: 80px; height: 80px; border-radius: 50%; background: #4287f5; color: white; display: flex; align-items: center; justify-content: center; font-size: 2rem;"),
            Div(P(f"Welcome, {user_email}!", id="greeting-message"), cls="chat-bubble", style="text-align: center;"),
            Button("Let's Get Started", 
                   type="button", 
                   role="button",
                   hx_get="/onboarding/personal-info/form",
                   hx_target="#onboarding-content",
                   hx_swap="innerHTML"),
            style="text-align: center; margin-top: 2rem; padding: 2rem;",
            data_theme="light"  # Add light theme
        ),
        id="onboarding-content"
    )
    
    main_wrapper = Main(
        initial_view,
        cls="container",
        style="min-height: 100vh; max-width: 800px; padding: 2rem; text-align: center; display: flex; align-items: center; justify-content: center; transform: translateY(-10%);"  # Add upward positioning
    )
    
    return (
        Title("Personal Information"),
        main_wrapper
    )



@rt('/onboarding/personal-info/form')
def form_view(auth):
    if auth is None: return ""
    
    # Form view - shown after clicking "Let's Get Started"
    form_content = Form(
        Article(
            H3("Let's get to know you better", style="text-align: center; margin-bottom: 1rem;"),
            
            # Compact grid layout
            Div(
                Div(
                    Label("Full name"),
                    Input(type="text", name="full_name", required=True, placeholder="Maria Cruz")
                ),
                cls="grid",
                style="grid-template-columns: 1fr; gap: 1rem;"
            ),
            
            Div(
                Div(
                    Label("Date of birth"),
                    Input(type="date", name="date_of_birth", required=True)
                ),
                Div(
                    Label("Gender"),
                    Select(
                        Option("Select", value="", disabled=True, selected=True),
                        Option("Male", value="male"),
                        Option("Female", value="female"),
                        Option("Other", value="other"),
                        name="gender", required=True
                    )
                ),
                cls="grid",
                style="grid-template-columns: 1fr 1fr; gap: 1rem;"
            ),
            
            Div(
                Div(
                    Label("Height (cm)"),
                    Input(type="number", name="height", required=True, placeholder="170")
                ),
                Div(
                    Label("Weight (kg)"),
                    Input(type="number", name="weight", required=True, placeholder="60")
                ),
                cls="grid",
                style="grid-template-columns: 1fr 1fr; gap: 1rem;"
            ),
            
            Div(
                Div(
                    Label("Ethnicity"),
                    Select(
                        Option("Select", value="", disabled=True, selected=True),
                        Option("Filipino", value="filipino"),
                        Option("Chinese", value="chinese"),
                        Option("Japanese", value="japanese"),
                        Option("Korean", value="korean"),
                        Option("Indian", value="indian"),
                        Option("Other", value="other"),
                        name="ethnicity", required=True
                    )
                ),
                cls="grid",
                style="grid-template-columns: 1fr; gap: 1rem;"
            ),
            
            # CHANGE: Make this a submit button instead of a button with type="button"
            Button("Continue", 
                   type="submit",  # Changed from "button" to "submit" 
                   id="confirm-personal-info", 
                   role="button", 
                   style="margin-top: 1rem; width: 100%;"),
                   
            data_theme="light"
        ),
        method="post",
        action="/onboarding/personal-info"
    )
    
    return form_content

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


@rt('/onboarding/wellness-journal')
def get(auth):
    if auth is None: return RedirectResponse('/login', status_code=303)
    
    user_email = auth.get('email', 'A')
    user_initial = user_email[0].upper() if user_email else 'A'
    
    # Header with title
    header = H1("Akasi.ai | Wellness Journal", style="color: black; text-align: center; margin-bottom: 2rem;")
    
    # Avatar with user initial - matching style from personal-info
    avatar_circle = Div(
        user_initial, 
        cls="avatar-circle", 
        style="margin: 0 auto 1rem; width: 80px; height: 80px; border-radius: 50%; background: #4287f5; color: white; display: flex; align-items: center; justify-content: center; font-size: 2rem;"
    )
    
    # Light-themed container with content
    journal_content = Article(
        H3("Let's build your wellness journal", style="text-align: center; margin-bottom: 1rem;"),
        
        Div(
            P("I'm Akasi.ai, your AI guardian of health and wellness.", style="margin-bottom: 0.75rem;"),
            P("This wellness journal will be your space to share any health concerns, symptoms, or wellness goals you might have. Everything you share here is private and secure.", style="margin-bottom: 0.75rem;"),
            P("I'll help you track your health journey and provide personalized insights based on the information you choose to share.", style="margin-bottom: 1.5rem;"),
            style="text-align: center;"
        ),
        
        A(
            "Start Your Wellness Journey",
            href="/home",
            role="button",
            id="confirm-wellness-journal",
            style="display: block; width: 100%; text-align: center; background: linear-gradient(45deg, #4287f5, #2961cc); border: none; color: white; padding: 0.75rem 1.5rem;"
        ),
        
        style="padding: 2rem;",
        data_theme="light"  # Set light theme explicitly
    )
    
    # Add the wellness messages for the animation
    wellness_messages = [
        "Welcome to your wellness journey!",
        "I'm Akasi, your AI health companion.",
        "Together, we'll build something special - your personal wellness journal.",
        "Your health and privacy are my top priority."
    ]
    wellness_messages_json = json.dumps(wellness_messages)
    wellness_messages_script = Script(f"window.wellnessMessages = {wellness_messages_json};")
    
    # Wrapper containing all components
    content = Div(
        header,
        avatar_circle,
        journal_content,
        wellness_messages_script,
        style="max-width: 800px; width: 100%; margin: 0 auto;"
    )
    
    # Main wrapper that centers vertically - matching style from other routes
    main_wrapper = Main(
        content,
        cls="container",
        style="min-height: 100vh; display: flex; align-items: center; justify-content: center; transform: translateY(-10%);"  # Match the upward positioning
    )
    
    return (
        Title("Wellness Journal"),
        main_wrapper
    )


# Home Page
@rt('/home')
def get(auth):
    if auth is None: return RedirectResponse('/login', status_code=303)
    
    user_id = auth.get('id')
    access_token = auth.get('access_token')
    refresh_token = auth.get('refresh_token')
    
    # Use authenticated client
    auth_client = use_auth_context(access_token, refresh_token)
    user_profile = fetch_user_profile(auth_client, user_id)


    current_onboarding_step = user_profile.get('onboarding_step')
    print(current_onboarding_step)
    
    user_email = auth.get('email', 'A')
    user_initial = user_email[0].upper() if user_email else 'A'
    
    # Create content with light theme
    avatar_circle = Div(user_initial, cls="avatar-circle", style="margin: 0 auto 1rem; width: 80px; height: 80px; border-radius: 50%; background: #4287f5; color: white; display: flex; align-items: center; justify-content: center; font-size: 2rem;")
    chat_bubble = Div(P(id="akasi-message-home"), cls="chat-bubble", style="text-align: center; margin-bottom: 2rem;")
    
    status_text = P(
        "Update Database Value: Getting Personal Info Step", 
        id="status-text",
        style="margin-bottom: 0.5rem;"
    )
    
    update_button = Button(
        "Update", 
        type="button", 
        id="update-button", 
        role="button"
    )
    
    update_section = Div(
        status_text,
        update_button,
        cls="update-section",
        style="margin-bottom: 1.5rem; text-align: center;"
    )
    
    logout_button = Button("Logout", type="submit", role="button", cls="secondary")
    logout_form = Form(logout_button, method="post", action="/logout", style="text-align: center;")
    
    home_messages_list = [
        f"Welcome back, {user_email}!",
        "How can I help you today?",
        "Let's check on your wellness goals.",
        "Remember to stay hydrated!",
        "Anything specific you'd like to track?"
    ]
    home_messages_json = json.dumps(home_messages_list)
    home_messages_script = Script(f"window.homeMessages = {home_messages_json};")
    
    # Add the home animation script
    home_animation_script = Script(src='/js/home_animation.js', defer=True)
    
    # Light themed article containing all content
    home_article = Article(
        H1("Akasi.ai | Dashboard", style="color: black; text-align: center; margin-bottom: 2rem;"),
        avatar_circle,
        chat_bubble,
        update_section,
        logout_form,
        home_messages_script,
        home_animation_script,
        data_theme="light",
        style="padding: 2rem; max-width: 600px; margin: 0 auto;"
    )
    
    # Main wrapper with vertical centering and upward shift
    main_wrapper = Main(
        home_article,
        cls="container",
        style="min-height: 100vh; display: flex; align-items: center; justify-content: center; transform: translateY(-10%);"
    )
    
    return (
        Title("Akasi Home"),
        main_wrapper
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