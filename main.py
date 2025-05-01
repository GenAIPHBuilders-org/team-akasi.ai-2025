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
supabase_secret_api_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_secret_api_key)

# --- Bootstrap CDN Links ---
bootstrap_css_cdn = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
bootstrap_js_cdn = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
bootstrap_icons_cdn = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"

# --- REMOVED custom_styles variable ---

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
    pico=False,
    # *** ADD static_path ***
    static_path='static', # Tell FastHTML where static files are
    hdrs=(
        Link(rel='stylesheet', href=bootstrap_css_cdn, integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH", crossorigin="anonymous"),
        Link(rel='stylesheet', href=bootstrap_icons_cdn),
        Script(src=bootstrap_js_cdn, integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz", crossorigin="anonymous"),
        # *** ADD Link to external custom.css ***
        Link(rel='stylesheet', href='/css/custom.css'), # Path relative to static dir

    )
)

# --- Routes ---

# Landing Page
@rt('/')
def get():


    landing_script = Script(src='/js/landing_animation.js', defer=True)

    avatar_circle = Div('A', cls="avatar-circle")
    chat_bubble = Div(P(id="akasi-message"), cls="chat-bubble") # Target element for landing animation (not bottom up kay tungod sa Js)
    signup_card = A(I(cls="bi bi-person-plus-fill action-card-icon"), Div(H5("Create Account"), P("Join Akasi."), cls="action-card-text"), href="/signup", cls="action-card")
    login_card = A(I(cls="bi bi-box-arrow-in-right action-card-icon"), Div(H5("Login"), P("Access dashboard."), cls="action-card-text"), href="/login", cls="action-card")

    landing_content = Div(avatar_circle, chat_bubble, signup_card, login_card, landing_script, cls="landing-content")




    return Titled("Welcome to Akasi.ai", landing_content)


@rt('/signup')
def get():
    # Mura lage og pa reverse ang style if ingon ani like mag start sa pinaka ubos then e wrap wrap dayun pa ubos
    # Ma bottom up approach siya if ang element naay mga children or pwede nimo sa jaavascript nalang e butang para sa chat bubble
    # Pwede pani siya ma arrange jud og maayo nga consistent among bottom ups

    page_title = H1("Create an Account", cls="text-center mb-4")

    email_input = Div(Label("Email address", cls="form-label", **{'for': "emailInput"}), Input(type="email", name="email", required=True, cls="form-control", id="emailInput"), cls="mb-3")
    password_input = Div(Label("Password", cls="form-label", **{'for': "passwordInput"}), Input(type="password", name="password", required=True, cls="form-control", id="passwordInput"), cls="mb-3")
    submit_button = Button("Sign Up", type="submit", cls="btn btn-primary w-100")
    signup_form = Form(email_input, password_input, submit_button, method="post", action="/signup", cls="mt-4") # This triggers the post method below
    
    login_link_section = Div(P("Already have an account? ", A("Login", href="/login")), cls="mt-3 text-center")

    
    content = Div(Div(Div(page_title, signup_form, login_link_section, cls="card-body p-4"), cls="card shadow-sm"), cls="col-md-6 col-lg-5 mx-auto")
    
    # Final allignments
    page_wrapper = Div(Div(content, cls="row justify-content-center"), cls="container mt-5")
    return Titled("Sign Up", page_wrapper)

@rt('/signup')
async def post(req, sess):
    form = await parse_form(req); email = form.get('email'); password = form.get('password')
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            user = res.user
            sess['user'] = {'id': user.id, 'email': user.email}
            # print(f"Signup successful for {email}, session created.")
            return RedirectResponse('/home', status_code=303)
        else:
            # print("Signup seemed successful but no user data returned.")
            return RedirectResponse('/login', status_code=303)
    except Exception as e:
        error_alert = Div(Strong("Signup Error!"), f" An error occurred: {str(e)}", A(" Try Again", href="/signup", cls="alert-link"), cls="alert alert-danger mt-4", role="alert")
        email_input = Div(Label("Email address", cls="form-label", **{'for': "emailInput"}), Input(type="email", name="email", required=True, cls="form-control", id="emailInput", value=email or ''), cls="mb-3")
        password_input = Div(Label("Password", cls="form-label", **{'for': "passwordInput"}), Input(type="password", name="password", required=True, cls="form-control", id="passwordInput"), cls="mb-3")
        submit_button = Button("Sign Up", type="submit", cls="btn btn-primary w-100")
        signup_form = Form(email_input, password_input, submit_button, method="post", action="/signup", cls="mt-4")
        login_link_section = Div(P("Already have an account? ", A("Login", href="/login")), cls="mt-3 text-center")
        page_title = H1("Create an Account", cls="text-center mb-4")
        content = Div(Div(Div(page_title, error_alert, signup_form, login_link_section, cls="card-body p-4"), cls="card shadow-sm"), cls="col-md-6 col-lg-5 mx-auto")
        page_wrapper = Div(Div(content, cls="row justify-content-center"), cls="container mt-5")
        return Titled("Signup Error", page_wrapper)

@rt('/login')
def get():
    email_input = Div(Label("Email address", cls="form-label", **{'for': "emailInputLogin"}), Input(type="email", name="email", required=True, cls="form-control", id="emailInputLogin"), cls="mb-3")
    password_input = Div(Label("Password", cls="form-label", **{'for': "passwordInputLogin"}), Input(type="password", name="password", required=True, cls="form-control", id="passwordInputLogin"), cls="mb-3")
    submit_button = Button("Login", type="submit", cls="btn btn-primary w-100")
    login_form = Form(email_input, password_input, submit_button, method="post", action="/login", cls="mt-4")
    signup_link_section = Div(P("Don't have an account? ", A("Sign Up", href="/signup")), cls="mt-3 text-center")
    page_title = H1("Login", cls="text-center mb-4")
    form_card_content = [page_title, login_form, signup_link_section]
    content = Div(Div(Div(*form_card_content, cls="card-body p-4"), cls="card shadow-sm"), cls="col-md-6 col-lg-5 mx-auto")
    page_wrapper = Div(Div(content, cls="row justify-content-center"), cls="container mt-5")
    return Titled("Login", page_wrapper)


@rt('/login') 
async def post(req, sess):
    form = await parse_form(req); email = form.get('email'); password = form.get('password')
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = res.user
        # print(user)

        # TODO: Creat a function to handle onboarding step so that they can be redirected to the right routes and how
        # and how do you maintain that all through out ... like maybe upon account creation lang ma tawag to na function noh ?

    
        sess['user'] = {'id': user.id, 'email': user.email}
        return RedirectResponse('/home', status_code=303)
    except Exception as e:
        error_alert = Div(Strong("Login Error!"), f" {str(e)} ", A("Please Try Again", href="/login", cls="alert-link"), cls="alert alert-danger mt-4", role="alert")
        email_input = Div(Label("Email address", cls="form-label", **{'for': "emailInputLogin"}), Input(type="email", name="email", required=True, cls="form-control", id="emailInputLogin", value=email or ''), cls="mb-3")
        password_input = Div(Label("Password", cls="form-label", **{'for': "passwordInputLogin"}), Input(type="password", name="password", required=True, cls="form-control", id="passwordInputLogin"), cls="mb-3")
        submit_button = Button("Login", type="submit", cls="btn btn-primary w-100")
        login_form = Form(email_input, password_input, submit_button, method="post", action="/login", cls="mt-4")
        signup_link_section = Div(P("Don't have an account? ", A("Sign Up", href="/signup")), cls="mt-3 text-center")
        page_title = H1("Login", cls="text-center mb-4")
        form_card_content = [page_title, error_alert, login_form, signup_link_section]
        content = Div(Div(Div(*form_card_content, cls="card-body p-4"), cls="card shadow-sm"), cls="col-md-6 col-lg-5 mx-auto")
        page_wrapper = Div(Div(content, cls="row justify-content-center"), cls="container mt-5")
        return Titled("Login Error", page_wrapper)

# Home Page - Pinaka best example of bottom up approach
@rt('/home')
def get(auth):
    if auth is None: return RedirectResponse('/login', status_code=303)

    
    user_id = auth.get('id')
    user_profile = fetch_user_profile(supabase, user_id)
    current_onboarding_step = user_profile.get('onboarding_step')

    print(current_onboarding_step)

    home_animation_script = Script(src='/js/home_animation.js', defer=True)
    user_email = auth.get('email', 'A'); user_initial = user_email[0].upper() if user_email else 'A'
    avatar_circle = Div(user_initial, cls="avatar-circle")
    # Chat bubble only needs the ID now
    chat_bubble = Div(P(id="akasi-message-home"), cls="chat-bubble")
    
    # Add static text and update button
    status_text = P(
        "Update Database Value: Getting Personal Info Step", 
        id="status-text",
        cls="mt-4 mb-3 text-center"
    )
    
    update_button = Button(
        "Update", 
        type="button", 
        id="update-button", 
        cls="btn btn-primary mb-4"
    )
    
    update_section = Div(
        status_text,
        update_button,
        cls="update-section w-100 text-center"
    )


    logout_button = Button("Logout", type="submit", cls="btn btn-danger mt-4")
    logout_form = Form(logout_button, method="post", action="/logout")

    # *** DEFINE MESSAGES FOR EXTERNAL JS via inline script ***
    home_messages_list = [
        f"Welcome back, {user_email}!",
        "How can I help you today?",
        "Let's check on your wellness goals.",
        "Remember to stay hydrated!",
        "Anything specific you'd like to track?"
    ]
    home_messages_json = json.dumps(home_messages_list)
    home_messages_script = Script(f"window.homeMessages = {home_messages_json};")

    home_content = Div(
        avatar_circle,
        chat_bubble,
        update_section,
        Div(logout_form, cls="text-center"),
        home_messages_script, 
        home_animation_script,
        cls="home-content-wrapper"
    )
    page_wrapper = Div(home_content, cls="container d-flex flex-column justify-content-center align-items-center", style="flex-grow: 1;")
    return Titled("Akasi Home", page_wrapper)


# Handle logout (Unchanged)
@rt('/logout')
def post(sess):
    supabase.auth.sign_out()
    if 'user' in sess: del sess['user']
    return RedirectResponse('/', status_code=303)


serve()