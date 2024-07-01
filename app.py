import gradio as gr

from src.assets.text_content import TITLE, INTRODUCTION_TEXT, CLEMSCORE_TEXT
from src.leaderboard_utils import query_search, get_github_data
from src.plot_utils import split_models, plotly_plot

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

list1 = list(multimodal_leaderboard["Model"])
list2 = list(text_leaderboard["Model"])


"""
PLOT UTILS
"""
plot_df = text_leaderboard
MODELS = list(plot_df[list(plot_df.columns)[0]].unique())  # Get list of models
OPEN_MODELS, CLOSED_MODELS = split_models(MODELS)
print(OPEN_MODELS, CLOSED_MODELS)


def update_selection(df, list_op: list, list_co: list,
                show_all: list = [], show_names: list = [], show_legend: list = [],
                mobile_view: list = []):
    """
    Abstraction over plotly_plot()
    Update model selection checkboxes as well
    """

    fig = plotly_plot(df, list_op, list_co, show_all, show_names, show_legend, mobile_view)

    return fig, show_all


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

        """
        THIRD TAB - PLOTS %PLAYED V/S QUALITY SCORE
        """
        with gr.TabItem("📈Plots", elem_id="plots", id=2):
            """
            Accordion Groups to select individual models - Hidden by default
            """
            with gr.Accordion("Select Open-weight Models 🌐", open=False):
                open_models_selection = gr.CheckboxGroup(
                    OPEN_MODELS,
                    value=[],
                    elem_id="value-select",
                    interactive=True,
                )

            with gr.Accordion("Select Closed-weight Models 💼", open=False):
                closed_models_selection = gr.CheckboxGroup(
                    CLOSED_MODELS,
                    value=[],
                    elem_id="value-select-2",
                    interactive=True,
                )

            """
            Checkbox group to control the layout of the plot 
            """
            with gr.Row():
                with gr.Column():
                    show_all = gr.CheckboxGroup(
                        ["Select All Models"],
                        label="Show plot for all models 🤖",
                        value=[],
                        elem_id="value-select-3",
                        interactive=True,
                    )

            """
            PLOT BLOCK
            """
            # Create a dummy DataFrame as an input to the plotly_plot function.
            # Uses this data to plot the %played v/s quality score
            with gr.Row():
                dummy_plot_df = gr.DataFrame(
                    value=plot_df,
                    visible=False
                )

            with gr.Row():
                with gr.Column():
                    # Output block for the plot
                    plot_output = gr.Plot()

            """
            CHANGE ACTIONS
            """
            open_models_selection.change(
                update_selection,
                [dummy_plot_df, open_models_selection, closed_models_selection],
                [plot_output, show_all],
                queue=True
            )

            closed_models_selection.change(
                update_selection,
                [dummy_plot_df, open_models_selection, closed_models_selection],
                [plot_output, show_all],
                queue=True
            )

            show_all.change(
                update_selection,
                [dummy_plot_df, open_models_selection, closed_models_selection, show_all],
                [plot_output, show_all],
                queue=True
            )

            # open_models_selection.change(
            #     update_show_all,
            #     [],
            #     [show_all],
            #     queue=True
            # )
            # closed_models_selection.change(
            #     update_show_all,
            #     [],
            #     [show_all],
            #     queue=True
            # )
            # show_all.change(
            #     update_selection,
            #     [show_all],
            #     [open_models_selection, closed_models_selection],
            #     queue=True
            # )

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
