from fasthtml.common import *

def register_routes(app, supabase):
    """Register all onboarding-related UI update routes"""
    
    @app.route('/update-step')
    def post(auth):
        if auth is None: 
            return "Unauthorized", 401
        
        user_id = auth.get('id')
        
        # Fetch current step - Make sure fetch_user_profile is defined or imported
        response = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
        user_profile = response.data[0] if response.data else {}
        current_step = user_profile.get('onboarding_step', 'personal_info')
        
        # Define steps and get next
        steps = ['personal_info', 'wellness_journal', 'diary_setup', 'completed']
        
        try:
            current_index = steps.index(current_step)
        except ValueError:
            # Handle case where current_step is not in steps
            current_index = -1
            
        next_index = (current_index + 1) % len(steps)
        next_step = steps[next_index]
        
        # Update database
        supabase.table('user_profiles').update({"onboarding_step": next_step}).eq('user_id', user_id).execute()
        
        # Format for display
        formatted_step = next_step.replace('_', ' ').title()
        
        # Return just what needs to change
        return Div(
            H4("Current Onboarding Step:"),
            Div(formatted_step, id="step-display"),
            Button("Update Step", hx_post="/update-step", hx_target="#step-container"),
            id="step-container"
        )