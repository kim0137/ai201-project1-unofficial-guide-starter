import gradio as gr
from query import ask, get_retriever

# Load once at startup — not on every query
model, collection = get_retriever()


def handle_query(question: str):
    """Run the full RAG pipeline and format output for Gradio."""
    if not question.strip():
        return "Please enter a question.", ""

    result = ask(question, model, collection)

    sources = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Housing Guide") as demo:
    gr.Markdown("## 🏠 The Unofficial Off-Campus Housing Guide")
    gr.Markdown(
        "Ask any question about finding off-campus housing, leases, "
        "roommates, budgeting, or rental scams."
    )

    with gr.Row():
        inp = gr.Textbox(
            label="Your question",
            placeholder="e.g. What fees should I ask about before signing a lease?",
            lines=2,
        )

    btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        answer = gr.Textbox(label="Answer", lines=10)
        sources = gr.Textbox(label="Retrieved from", lines=10)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

demo.launch()