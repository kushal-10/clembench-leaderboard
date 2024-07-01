import gradio as gr

from src.assets.text_content import TITLE, INTRODUCTION_TEXT, CLEMSCORE_TEXT
from src.leaderboard_utils import query_search, get_github_data

""" 
CONSTANTS
"""
# For restarting the gradio application
TIME = 200  # in seconds # Reload will not work locally - requires HFToken # The app launches locally as expected - only without the reload utility
# For Leaderboard table
dataframe_height = 800  # Height of the table in pixels # Set on average considering all possible devices


"""
GITHUB UTILS
"""
github_data = get_github_data()
text_leaderboard = github_data["text"][0]  # Get the text-only leaderboard for its available latest version
multimodal_leaderboard = github_data["multimodal"][0]  # Get multimodal leaderboard for its available latest version.

# Show only First 4 columns for the leaderboards
text_leaderboard = text_leaderboard.iloc[:, :4]
print(f"Showing the following columns for the latest leaderboard: {text_leaderboard.columns}")
multimodal_leaderboard = multimodal_leaderboard.iloc[:, :4]
print(f"Showing the following columns for the multimodal leaderboard: {multimodal_leaderboard.columns}")


"""
PLOT UTILS
"""



"""
MAIN APPLICATION
"""
hf_app = gr.Blocks()
with hf_app:
    gr.HTML(TITLE)
    gr.Markdown(INTRODUCTION_TEXT, elem_classes="markdown-text")

    with gr.Tabs(elem_classes="tab-buttons") as tabs:
        """
        FIRST TAB - TEXT-LEADERBOARD
        """
        with gr.TabItem("🥇 CLEM Leaderboard", elem_id="llm-benchmark-tab-table", id=0):
            with gr.Row():
                search_bar = gr.Textbox(
                    placeholder=" 🔍 Search for models - separate multiple queries with `;` and press ENTER...",
                    show_label=False,
                    elem_id="search-bar",
                )

            leaderboard_table = gr.Dataframe(
                value=text_leaderboard,
                elem_id="text-leaderboard-table",
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
                value=text_leaderboard,
                elem_id="text-leaderboard-table-dummy",
                interactive=False,
                visible=False
            )

            # Action after submitting a query to the search bar
            search_bar.submit(
                query_search,
                [dummy_leaderboard_table, search_bar],
                leaderboard_table,
                queue=True
            )

        """
        SECOND TAB - MULTIMODAL LEADERBOARD
        """
        with gr.TabItem("🥇 Multimodal CLEM Leaderboard", elem_id="mm-llm-benchmark-tab-table", id=1):
            with gr.Row():
                mm_search_bar = gr.Textbox(
                    placeholder=" 🔍 Search for models - separate multiple queries with `;` and press ENTER...",
                    show_label=False,
                    elem_id="search-bar",
                )

            mm_leaderboard_table = gr.Dataframe(
                value=multimodal_leaderboard,
                elem_id="mm-leaderboard-table",
                interactive=False,
                visible=True,
                height=dataframe_height
            )

            # Show information about the clemscore and last updated date below the table
            gr.HTML(CLEMSCORE_TEXT)
            gr.HTML(f"Last updated - {github_data['date']}")

            # Add a dummy leaderboard to handle search queries in leaderboard_table
            # This will show a temporary leaderboard based on the searched value
            mm_dummy_leaderboard_table = gr.Dataframe(
                value=multimodal_leaderboard,
                elem_id="mm-leaderboard-table-dummy",
                interactive=False,
                visible=False
            )

            # Action after submitting a query to the search bar
            mm_search_bar.submit(
                query_search,
                [mm_dummy_leaderboard_table, mm_search_bar],
                mm_leaderboard_table,
                queue=True
            )

        with gr.TabItem("", elem_id="plots", id=2):


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
