import gradio as gr
import os
from apscheduler.schedulers.background import BackgroundScheduler
from huggingface_hub import HfApi
from datetime import datetime, timedelta

from src.assets.text_content import TITLE, INTRODUCTION_TEXT, CLEMSCORE_TEXT
from src.leaderboard_utils import filter_query
from src.plot_utils import plotly_plot
from src.github_utils import get_primary_leaderboard, get_open_models, get_closed_models, get_plot_df, get_version_names, get_version_df, get_prev_df

TIME = 100

# For Leaderboards
dataframe_height = 800  # Height of the table in pixels

def select_prev_df(name):
    version_names = get_version_names()
    version_dfs = get_version_df()
    ind = version_names.index(name)
    prev_df = version_dfs[ind]
    return prev_df


# API for auto restart
HF_TOKEN = os.environ.get("H4_TOKEN", None)
api = HfApi()


def restart_space():
    api.restart_space(repo_id="Koshti10/leaderboard", token=HF_TOKEN)


# MAIN APPLICATION
main_app = gr.Blocks()
with main_app:
    gr.HTML(TITLE)
    gr.Markdown(INTRODUCTION_TEXT, elem_classes="markdown-text")

    with gr.Tabs(elem_classes="tab-buttons") as tabs:
        with gr.TabItem("🥇 CLEM Leaderboard", elem_id="llm-benchmark-tab-table", id=0):
            with gr.Row():
                search_bar = gr.Textbox(
                    placeholder=" 🔍 Search for models - separate multiple queries with `;` and press ENTER...",
                    show_label=False,
                    elem_id="search-bar",
                    every=TIME
                )

            leaderboard_table = gr.Dataframe(
                value=get_primary_leaderboard(),
                every=TIME,
                elem_id="leaderboard-table",
                interactive=False,
                visible=True,
                height=dataframe_height
            )

            gr.HTML(CLEMSCORE_TEXT)

            # Add a dummy leaderboard to handle search queries from the primary_leaderboard_df and not update primary_leaderboard_df
            dummy_leaderboard_table = gr.Dataframe(
                value=get_primary_leaderboard(),
                every=TIME,
                elem_id="leaderboard-table",
                interactive=False,
                visible=False
            )

            search_bar.submit(
                filter_query,
                [dummy_leaderboard_table, search_bar],
                leaderboard_table,
                queue=True,
                every=TIME
            )

        with gr.TabItem("📈 Plot", id=3):
            with gr.Row():
                open_models_selection = gr.CheckboxGroup(
                    get_open_models(),
                    every=TIME,
                    label="Open-weight Models 🌐",
                    value=[],
                    elem_id="value-select",
                    interactive=True,
                )

            with gr.Row():
                closed_models_selection = gr.CheckboxGroup(
                    get_closed_models(),
                    every=TIME,
                    label="Closed-weight Models 💼",
                    value=[],
                    elem_id="value-select-2",
                    interactive=True,
                )

            with gr.Row():
                with gr.Column():
                    show_all = gr.CheckboxGroup(
                        ["Select All Models"],
                        label="Show plot for all models 🤖",
                        value=[],
                        elem_id="value-select-3",
                        interactive=True,
                        every=TIME
                    )

                with gr.Column():
                    show_names = gr.CheckboxGroup(
                        ["Show Names"],
                        label="Show names of models on the plot 🏷️",
                        value=[],
                        elem_id="value-select-4",
                        interactive=True,
                        every=TIME
                    )

                with gr.Column():
                    show_legend = gr.CheckboxGroup(
                        ["Show Legend"],
                        label="Show legend on the plot 💡",
                        value=[],
                        elem_id="value-select-5",
                        interactive=True,
                        every=TIME
                    )
                with gr.Column():
                    mobile_view = gr.CheckboxGroup(
                        ["Mobile View"],
                        label="View plot on smaller screens 📱",
                        value=[],
                        elem_id="value-select-6",
                        interactive=True,
                        every=TIME
                    )

            with gr.Row():
                dummy_plot_df = gr.DataFrame(
                    value=get_plot_df(),
                    every=TIME,
                    visible=False
                )

            with gr.Row():
                with gr.Column():
                    # Output block for the plot
                    plot_output = gr.Plot(every=TIME)

            open_models_selection.change(
                plotly_plot,
                [dummy_plot_df, open_models_selection, closed_models_selection, show_all, show_names, show_legend,
                 mobile_view],
                plot_output,
                queue=True,
                every=TIME
            )

            closed_models_selection.change(
                plotly_plot,
                [dummy_plot_df, open_models_selection, closed_models_selection, show_all, show_names, show_legend,
                 mobile_view],
                plot_output,
                queue=True,
                every=TIME
            )

            show_all.change(
                plotly_plot,
                [dummy_plot_df, open_models_selection, closed_models_selection, show_all, show_names, show_legend,
                 mobile_view],
                plot_output,
                queue=True,
                every=TIME
            )

            show_names.change(
                plotly_plot,
                [dummy_plot_df, open_models_selection, closed_models_selection, show_all, show_names, show_legend,
                 mobile_view],
                plot_output,
                queue=True,
                every=TIME
            )

            show_legend.change(
                plotly_plot,
                [dummy_plot_df, open_models_selection, closed_models_selection, show_all, show_names, show_legend,
                 mobile_view],
                plot_output,
                queue=True,
                every=TIME
            )

            mobile_view.change(
                plotly_plot,
                [dummy_plot_df, open_models_selection, closed_models_selection, show_all, show_names, show_legend,
                 mobile_view],
                plot_output,
                queue=True,
                every=TIME
            )

        with gr.TabItem("🔄 Versions and Details", elem_id="details", id=2):
            with gr.Row():
                version_select = gr.Dropdown(
                    get_version_names(), label="Select Version 🕹️", value=get_version_names()[0]
                )
            with gr.Row():
                search_bar_prev = gr.Textbox(
                    placeholder=" 🔍 Search for models - separate multiple queries with `;` and press ENTER...",
                    show_label=False,
                    elem_id="search-bar-2",
                    every=TIME
                )

            prev_table = gr.Dataframe(
                value=get_prev_df(),
                every=TIME,
                elem_id="leaderboard-table",
                interactive=False,
                visible=True,
                height=dataframe_height
            )

            dummy_prev_table = gr.Dataframe(
                value=get_prev_df(),
                every=TIME,
                elem_id="leaderboard-table",
                interactive=False,
                visible=False
            )

            search_bar_prev.submit(
                filter_query,
                [dummy_prev_table, search_bar_prev],
                prev_table,
                queue=True,
                every=TIME
            )

            version_select.change(
                select_prev_df,
                [version_select],
                prev_table,
                queue=True,
                every=TIME
            )
    main_app.load()

main_app.queue()

# Add scheduler to auto-restart the HF space at every TIME interval and update every component each time
scheduler = BackgroundScheduler()
scheduler.add_job(restart_space, 'interval', seconds=TIME)
scheduler.start()

# Log current start time and scheduled restart time
print(datetime.now())
print(f"Scheduled restart at {datetime.now() + timedelta(seconds=TIME)}")

main_app.launch()