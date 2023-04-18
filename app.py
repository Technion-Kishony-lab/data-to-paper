# -*- coding:utf-8 -*-
import os
import logging
import sys
import zipfile

import gradio as gr
# import torch
from app_modules.utils import *
from app_modules.presets import *
from app_modules.overwrites import *
from scientistgpt import run_scientist_gpt
DATA_FOLDER, OUTPUT_FOLDER = "app_user_data", "app_output"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
)

# load_8bit = (
#     sys.argv[3].lower().startswith("8")
#     if len(sys.argv) > 3 else False
# )
# base_model = "decapoda-research/llama-7b-hf"
# adapter_model = "decapoda-research/llama-7b-hf"
# tokenizer, model, device = load_tokenizer_and_model(
#     base_model, adapter_model, load_8bit=load_8bit
# )


# def predict(
#     text,
#     chatbot,
#     history,
#     top_p,
#     temperature,
#     max_length_tokens,
#     max_context_length_tokens,
# ):
#     if text == "":
#         yield chatbot, history, "Empty context."
#         return
#
#     inputs = generate_prompt_with_history(
#         text, history, tokenizer, max_length=max_context_length_tokens
#     )
#     if inputs is None:
#         yield chatbot, history, "Input too long."
#         return
#     else:
#         prompt, inputs = inputs
#         begin_length = len(prompt)
#     input_ids = inputs["input_ids"][:, -max_context_length_tokens:].to(device)
#     torch.cuda.empty_cache()
#
#     with torch.no_grad():
#         for x in sample_decode(
#             input_ids,
#             model,
#             tokenizer,
#             stop_words=["[|Human|]", "[|AI|]"],
#             max_length=max_length_tokens,
#             temperature=temperature,
#             top_p=top_p,
#         ):
#             if is_stop_word_or_prefix(x, ["[|Human|]", "[|AI|]"]) is False:
#                 if "[|Human|]" in x:
#                     x = x[: x.index("[|Human|]")].strip()
#                 if "[|AI|]" in x:
#                     x = x[: x.index("[|AI|]")].strip()
#                 x = x.strip(" ")
#                 a, b = [[y[0], convert_to_markdown(y[1])] for y in history] + [
#                     [text, convert_to_markdown(x)]
#                 ], history + [[text, x]]
#                 yield a, b, "Generating..."
#             if shared_state.interrupted:
#                 shared_state.recover()
#                 try:
#                     yield a, b, "Stop: Success"
#                     return
#                 except:
#                     pass
#     torch.cuda.empty_cache()
#     print(prompt)
#     print(x)
#     print("=" * 80)
#     try:
#         yield a, b, "Generate: Success"
#     except:
#         pass


# def retry(
#     text,
#     chatbot,
#     history,
#     top_p,
#     temperature,
#     max_length_tokens,
#     max_context_length_tokens,
# ):
#     logging.info("Retry...")
#     if len(history) == 0:
#         yield chatbot, history, "Empty context."
#         return
#     chatbot.pop()
#     inputs = history.pop()[0]
#     # for x in predict(
#     #     inputs,
#     #     chatbot,
#     #     history,
#     #     top_p,
#     #     temperature,
#     #     max_length_tokens,
#     #     max_context_length_tokens,
#     # ):
#     #     yield x


gr.Chatbot.postprocess = postprocess

with open("assets/custom.css", "r", encoding="utf-8") as f:
    customCSS = f.read()


def app_run_scientist_gpt(data_description, goal_description, file_upload, data_directory, output_directory):
    # extract uploaded files to data_directory
    data_directory = os.path.join(DATA_FOLDER, data_directory)
    output_directory = os.path.join(OUTPUT_FOLDER, output_directory)
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    # extract uploaded files to data_directory
    file_upload.save(data_directory)
    zipfile.ZipFile(os.path.join(data_directory, file_upload.name)).extractall(data_directory)
    # run scientist gpt
    run_scientist_gpt(data_description, goal_description, data_directory, output_directory)
    # return the pdf file from the output directory
    pdf_file = os.path.join(output_directory, "paper.pdf")
    return pdf_file


with gr.Blocks(css=customCSS, theme=small_and_beautiful_theme) as demo:
    history = gr.State([])
    # user_question = gr.State("")
    with gr.Row():
        gr.HTML(title)
        # status_display = gr.Markdown("Success", elem_id="status_display")
    gr.Markdown(description_top)
    with gr.Row():
        with gr.Column(scale=3):
            file_upload = gr.File(label="Data Files", file_types=[".zip"]).style(height=1)
        with gr.Column(scale=5):
            data_description = gr.Textbox(label='data_description', show_label=False ,lines=10, placeholder="Data Description").style(container=False)
        with gr.Column(scale=5):
            goal_description = gr.Textbox(label='goal_description', show_label=False ,lines=10, placeholder="Goal Description").style(container=False)
    generate_paper = gr.Button(label="generate_paper", value="Generate Paper!",)
    with gr.Row(scale=1).style(equal_height=True):
        with gr.Column(scale=5):
            with gr.Row(scale=1):
                scientist_chat = gr.Chatbot(label="Scientist Chat", elem_id="chuanhu_chatbot").style(height="100%")
                other_chat = gr.Chatbot(label="Others Chat", elem_id="chuanhu_chatbot").style(height="100%")
    with gr.Row():
        output_file = gr.File(label="Generated Paper", file_types=[".pdf"]).style(height=1)
            # with gr.Row(scale=1):
                # with gr.Column(scale=12):
                    # user_input = gr.Textbox(
                    #     show_label=False, placeholder="Enter text"
                    # ).style(container=False)
                # with gr.Column(min_width=70, scale=1):
                #     submitBtn = gr.Button("Send")
                # with gr.Column(min_width=70, scale=1):
                #     cancelBtn = gr.Button("Stop")

            # with gr.Row(scale=1):
            #     emptyBtn = gr.Button(
            #         "🧹 New Conversation",
            #     )
            #     retryBtn = gr.Button("🔄 Regenerate")
            #     delLastBtn = gr.Button("🗑️ Remove Last Turn")
        # with gr.Column():
        #     with gr.Column(min_width=50, scale=1):
        #         with gr.Tab(label="Parameter Setting"):
        #             gr.Markdown("# Parameters")
        #             top_p = gr.Slider(
        #                 minimum=-0,
        #                 maximum=1.0,
        #                 value=0.95,
        #                 step=0.05,
        #                 interactive=True,
        #                 label="Top-p",
        #             )
        #             temperature = gr.Slider(
        #                 minimum=0.1,
        #                 maximum=2.0,
        #                 value=1,
        #                 step=0.1,
        #                 interactive=True,
        #                 label="Temperature",
        #             )
        #             max_length_tokens = gr.Slider(
        #                 minimum=0,
        #                 maximum=512,
        #                 value=512,
        #                 step=8,
        #                 interactive=True,
        #                 label="Max Generation Tokens",
        #             )
        #             max_context_length_tokens = gr.Slider(
        #                 minimum=0,
        #                 maximum=4096,
        #                 value=2048,
        #                 step=128,
        #                 interactive=True,
        #                 label="Max History Tokens",
        #             )
    gr.Markdown(description)
    generate_paper.click(
        fn= app_run_scientist_gpt,
        inputs=[data_description, goal_description, file_upload, DATA_FOLDER, OUTPUT_FOLDER],
        outputs=[scientist_chat, other_chat, output_file],
    )


    # predict_args = dict(
    #     fn=predict,
    #     inputs=[
    #         user_question,
    #         chatbot,
    #         history,
    #         top_p,
    #         temperature,
    #         max_length_tokens,
    #         max_context_length_tokens,
    #     ],
    #     outputs=[chatbot, history, status_display],
    #     show_progress=True,
    # )
    # retry_args = dict(
    #     fn=retry,
    #     inputs=[
    #         user_input,
    #         chatbot,
    #         history,
    #         top_p,
    #         temperature,
    #         max_length_tokens,
    #         max_context_length_tokens,
    #     ],
    #     outputs=[chatbot, history, status_display],
    #     show_progress=True,
    # )

    # reset_args = dict(fn=reset_textbox, inputs=[], outputs=[user_input, status_display])

    # Chatbot
    # cancelBtn.click(cancel_outputing, [], [status_display])
    # transfer_input_args = dict(
    #     fn=transfer_input,
    #     inputs=[user_input],
    #     outputs=[user_question, user_input, submitBtn, cancelBtn],
    #     show_progress=True,
    # )

    # user_input.submit(**transfer_input_args).then(**predict_args)

    # submitBtn.click(**transfer_input_args).then(**predict_args)

    # emptyBtn.click(
    #     reset_state,
    #     outputs=[chatbot, history, status_display],
    #     show_progress=True,
    # )
    # emptyBtn.click(**reset_args)

    # retryBtn.click(**retry_args)

    # delLastBtn.click(
    #     delete_last_conversation,
    #     [chatbot, history],
    #     [chatbot, history, status_display],
    #     show_progress=True,
    # )

demo.title = "ScientistGPT"

if __name__ == "__main__":
    reload_javascript()
    demo.queue(concurrency_count=CONCURRENT_COUNT).launch(
        share=False, favicon_path="./assets/favicon.ico", inbrowser=True
    )
