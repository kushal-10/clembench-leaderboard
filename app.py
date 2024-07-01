import gradio as gr

from src.assets.text_content import TITLE, INTRODUCTION_TEXT, CLEMSCORE_TEXT
from src.leaderboard_utils import filter_search, get_github_data

""" 
CONSTANTS
"""
# For restarting the gradio application
TIME = 200  # in seconds # Reload will not work locally - requires HFToken # The app launches locally as expected - only without the reload utility
# For Leaderboard table
dataframe_height = 800  # Height of the table in pixels # Set on average considering all possible devices

"""
GitHub Utils
"""
github_data = get_github_data()
latest_leaderboard = github_data["text"][0]
latest_leaderboard = latest_leaderboard.iloc[:, :4]  # Show only First 4 columns of the dataframe
print(f"Showing the following columns for the latest leaderboard: {latest_leaderboard.columns[:4]}")

"""
MAIN APPLICATION
"""
hf_app = gr.Blocks()
with hf_app:
    gr.HTML(TITLE)
    gr.Markdown(INTRODUCTION_TEXT, elem_classes="markdown-text")

    with gr.Tabs(elem_classes="tab-buttons") as tabs:
        with gr.TabItem("🥇 CLEM Leaderboard", elem_id="llm-benchmark-tab-table", id=0):
            with gr.Row():
                search_bar = gr.Textbox(
                    placeholder=" 🔍 Search for models - separate multiple queries with `;` and press ENTER...",
                    show_label=False,
                    elem_id="search-bar",
                )

            leaderboard_table = gr.Dataframe(
                value=latest_leaderboard,
                elem_id="leaderboard-table",
                interactive=False,
                visible=True,
                height=dataframe_height
            )

            # Show information about the clemscore and last updated date below the table
            gr.HTML(CLEMSCORE_TEXT)
            gr.HTML(f"Last updated - {github_data['date']}")

            # Add a dummy leaderboard to handle search queries in leaderboard_table
            # This will show a temporary leaderboard based on the searched value
            dummy_leaderboard_table = gr.Dataframe(
                value=latest_leaderboard,
                elem_id="leaderboard-table",
                interactive=False,
                visible=False
            )

            # Action after submitting a query to the search bar
            search_bar.submit(
                filter_search,
                [dummy_leaderboard_table, search_bar],
                leaderboard_table,
                queue=True
            )

    hf_app.load()

hf_app.queue()

# # Add scheduler to auto-restart the HF space at every TIME interval and update every component each time
# scheduler = BackgroundScheduler()
# scheduler.add_job(restart_space, 'interval', seconds=TIME)
# scheduler.start()
#
# # Log current start time and scheduled restart time
# print(datetime.now())
# print(f"Scheduled restart at {datetime.now() + timedelta(seconds=TIME)}")

hf_app.launch()
