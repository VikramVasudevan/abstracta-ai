import asyncio
import logging
import time
import gradio as gr

async def steps_executor(
    steps_info,
    initial_outputs=None,
    build_progress_fn=None,
    final_message="Process completed successfully.",
    final_outputs=None,
):
    """
    Executes a sequence of asynchronous steps with progress reporting and yields intermediate outputs.

    Each step is a dictionary with keys:
      - "name": str - The display name of the step.
      - "func": callable - An async function accepting a `context` dict and returning its result.

    The function maintains a shared `context` dictionary that is passed to each step function,
    allowing steps to access results from previous steps.

    Args:
        steps_info (list of dict): List of steps to execute. Each dict must have "name" and "func".
        initial_outputs (tuple or None): Optional initial outputs to yield before starting steps.
        build_progress_fn (callable or None): Function to build progress UI. Signature:
            build_progress_fn(step_names: list[str], current_step_index: int, animate: bool) -> str (HTML).
        final_message (str): Message to yield if no explicit final_outputs provided.
        final_outputs (tuple or None): Final outputs to yield after all steps complete.

    Yields:
        tuple: Outputs to be consumed by the UI after each step and at start/end.
    """
    logging.info("Starting steps_executor with %d steps.", len(steps_info))

    context = {}

    if initial_outputs is not None:
        logging.debug("Yielding initial outputs.")
        yield initial_outputs
        await asyncio.sleep(0.5)

    total_steps = len(steps_info)
    step_names = [step["name"] for step in steps_info]

    for i, step in enumerate(steps_info):
        step_name = step["name"]
        step_key = step["key"]
        step_func = step["func"]
        step_yield = step["yield"] # tuple of lambdas that consume context and return anything based on that context.
        step_yield_before = step["yield_before"] if "yield_before" in step else []

        logging.info("Starting step %d/%d: %s", i + 1, total_steps, step_name)

        # Yield progress UI with animation on current step
        if build_progress_fn:
            progress_html = build_progress_fn(step_names, i, animate=True)
        else:
            progress_html = ""

        # Yield progress update before running the step
        if step_yield_before:
            yield (progress_html, *(f(context) for f in step_yield_before))
        else:
            yield (progress_html, "", "", gr.update(visible=False), gr.update(visible=False))
        await asyncio.sleep(0.5)

        try:
            # Execute the async step function, passing the shared context dict
            step_result = await step_func(context)
            logging.info("Completed step '%s' successfully.", step_name)
        except Exception as e:
            logging.error("Error in step '%s': %s", step_name, e, exc_info=True)
            raise

        # Store the result keyed by step name in context for downstream steps
        context[step_key] = step_result

        # Yield progress UI without animation to indicate step done
        if build_progress_fn:
            progress_html_done = build_progress_fn(step_names, i, animate=False)
        else:
            progress_html_done = ""

        #yield (progress_html_done, "", "", gr.update(visible=False), gr.update(visible=False))
        yield (progress_html_done, *(f(context) for f in step_yield))
        await asyncio.sleep(0.5)

    logging.info("All steps completed.")

    if final_outputs is not None:
        logging.debug("Yielding explicit final outputs.")
        yield final_outputs
        await asyncio.sleep(0.5)
    else:
        logging.debug("Yielding default final message.")
        yield (gr.update(value=final_message, visible=False), *(f(context) for f in step_yield))
        await asyncio.sleep(0.5)


def fn_report_build_progress(steps: list[str], current_step, animate=False):
    """Return HTML showing step progress with optional animation."""
    html = "<ul style='list-style:none;padding:0'>"
    for i, step in enumerate(steps):
        if i < current_step:
            html += f"<li>✅ <b>{step}</b></li>"
        elif i == current_step:
            dots = "." * ((int(time.time() * 2) % 3) + 1) if animate else ""
            html += f"<li>⏳ <b>{step}{dots}</b></li>"
        else:
            html += f"<li>⬜ {step}</li>"
    html += "</ul>"

    percent = int((current_step / len(steps)) * 100)
    html += (
        f"<div style='background:#eee;border-radius:8px;height:12px;overflow:hidden;margin-top:8px'>"
        f"<div style='background:#2563eb;height:100%;width:{percent}%;transition:width 0.3s'></div>"
        f"</div>"
    )
    return html
