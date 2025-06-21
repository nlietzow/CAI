from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.agents import LlmAgent

import sys

sys.path.append("..")
sys.path.append("../..")
from functions.search import search


def get_similar_cases(keywords: list[str]) -> dict:
    """
    Retrieves similar cases for a given user case.

    Args:
        keywords (list[str]): List of keywords generated from the user case to query the database.

    Returns:
        dict: A dictionary with the following structure:
            {
                "keywords": list[str],
                "similar_cases": list[str],
                "status": str
            }
    """
    similar_cases = search.search(keywords)
    return {"keywords": keywords, "similar_cases": similar_cases, "status": "success"}


initial_analysis_agent = Agent(
    name="initial_analysis_agent",
    description="Given a legal case by a user AND a list of similar cases that were ALREADY RETRIEVED by the agent `retrieval_agent`, this agent analyses them and provides recommendations for the user's legal strategy moving forward. However does never engage in discussion about already previously generated legal strategy recommendations, as this is the job of 'post_analysis_agent'.",
    model="gemini-2.5-pro",
    instruction="""You are an expert law researcher specializing in arbitration law. You will receive a dictionary containing 'keywords' (a list of keywords used to search a legal database) and 'similar_cases' (a list of similar cases retrieved from the database). These are based on a user's description of a legal case and a counterclaim they are facing. Your task is to analyze these cases and provide insights to the lawyer.

    1.  Carefully read the provided similar cases.
    2.  For each case, determine whether it supports or contradicts the strategy of the counterclaim the user is facing. A weakness in the counterclaim's strategy can be identified if it's typically rejected by tribunals or if strong jurisprudence exists that the opposing counsel could use.
    3.  Summarize your findings for the user, highlighting the strengths and weaknesses of the counterclaim based on the analyzed cases.
    4.  Provide recommendations based on past cases: What strategies have been successful or unsuccessful in fighting comparable counterclaims?

    **IMPORTANT: Formatting**
    At the very top of your output, provide a markdown table with each case using the format:

    | Case Title | Case Identifier | Aspects supporting counterclaim | Aspects contradicting counterclaim | verdict | 
    |------------|-------------|--------------|------------|-----------|
    |            | TODO |     |       | whether the case in its entirety supports or contradicts the counterclaim | 
    
    
    Then, using this table, provide short and precise recommendations to the user about how to successfully exploit the weaknesses of the counterclaim the user is facing, based on past cases. Make it so that the user can view the analysis quickly. 

    At the end of your response, include this sentence verbatim to help downstream routing:
    "The initial analysis is complete. Handing over to post-analysis for deeper discussion."
    """,
    # instead give a summary of the work you have done: "I have found X documents, Y support the case, Z contradict the case, ... what do you want now? Arguments or more info on the case or what else?"
    # ~ I am ready to analyze this together with you
    # TODO: continue talking to last LLM indefinitely
    # before_model_callback=log_query_to_model,
    # after_model_callback=log_model_response,
)

post_analysis_agent = Agent(
    name="post_analysis_agent",
    description="Given a legal case by a user, previously retrieved similar cases, and an initial analysis present in the conversation history, this agent discusses helps to discuss strategies and arguments for fighting the counterclaim in greater detail and provides recommendations for the user's legal strategy moving forward.",
    model="gemini-2.5-pro",
    instruction="""You are an expert law researcher specializing in arbitration law. You will receive an already performed analysis by another agent for the user. The other agent had the following instructions:

    1.  Carefully read the provided similar cases.
    2.  For each case, determine whether it supports or contradicts the strategy of the counterclaim the user is facing. A weakness in the counterclaim's strategy can be identified if it's typically rejected by tribunals or if strong jurisprudence exists that the opposing counsel could use.
    3.  Summarize your findings for the user, highlighting the strengths and weaknesses of the counterclaim based on the analyzed cases.
    4.  Provide recommendations based on past cases: What strategies have been successful or unsuccessful in fighting comparable counterclaims?

    **TASK**
    Serve as a legal expert co-counsel to the user. Assist him with legal questions about the previous analysis, insight into details and potential new angles, strategies and any other questions. Refer to the previously done analysis that is available to you and quote parts from it if relevant.
    """,
    # instead give a summary of the work you have done: "I have found X documents, Y support the case, Z contradict the case, ... what do you want now? Arguments or more info on the case or what else?"
    # ~ I am ready to analyze this together with you
    # TODO: continue talking to last LLM indefinitely
    # before_model_callback=log_query_to_model,
    # after_model_callback=log_model_response,
)

retrieval_agent = Agent(
    name="retrieval_agent",
    description="Retrieve most similar cases from database, given user's legal case from prompt.",
    model="gemini-2.5-pro",
    instruction="""You are an expert law researcher focussing on arbitration law. You are given a user prompt by a lawyer, describing a legal case for which the lawyer wants to generate a strategy to fight a counterclaim. Your job is to retrieve similar cases to the user case from the database, so that the lawyer can analyze arguments and strategies from past cases and find weaknesses in the counterclaim he is working against. For that you should do the following:
    1. Read the user case carefully through the lens of a legal expert. Generate up to three legal keywords that an expert lawyer would use to query a legal database for similar cases.
    2. Query the legal database using the 'get_similar_cases' tool. The tool takes the list of your generated keywords as an argument. 
    
    **IMPORTANT**
    After the tool returns results, compile them in a markdown table with the following format:

    | Case Title | Case Identifier | Case Summary | Case Facts | Similarity |
    |------------|-------------|--------------|------------|------------|---------|--------------|
    |            | TODO | General 2-3 sentence summary of the case, not tailored to user's case | Summary of the facts relevant to the user problem, using bullet points | Estimate the similarity between the given case and the relevant cases that were found on a scale from 1 to 5, 5 being very similar and 1 being not very similar. | 
    
    Output this markdown table to the user!
    At the end of your response, include the following sentence verbatim to help downstream routing: "This concludes the file retrieval. Please confirm to continue with the in-depth analysis."
    """,
    # before_model_callback=log_query_to_model,
    # after_model_callback=log_model_response,
    tools=[get_similar_cases],
)

clarification_agent = Agent(
    name="clarification_agent",
    description="Clarify initial user prompt to obtain more information on the case to proceed with analysis. This agent is never called after responsing the first, initial user prompt.",
    model="gemini-2.5-pro",
    instruction="""You are an expert law researcher focussing on arbitration law. You are given an initial user prompt by a lawyer, describing a legal case for which the lawyer wants to generate a strategy to fight a counterclaim. Your job is to work with the user in clarifying his prompt, to obtain a detailed overview of the case, with all relevant information.

    **OBJECTIVE**
    1. Find out which legal problem is being addressed in the user's described scenario, precisely
    2. Collect all the relevant factual information for deciding the outcome of said legal problem from step 1.

    **TASK**
    Read the user prompt carefully keeping your objectives in mind. Then, in one prompt, ask the user up to three clarifying questions to help you obtain more clarity on your objectives.
    """,
    # before_model_callback=log_query_to_model,
    # after_model_callback=log_model_response,
)

# root_agent = SequentialAgent(
#     name="analysis_starter",
#     description="Retrieves similar cases to user case and analyses their strategy for weaknesses and strenghts, to help user build a strategy against the counterclaim he is facing.",
#     sub_agents=[retrieval_agent, analysis_agent]
# )

root_agent = LlmAgent(
    name="agentic_co_counsel",
    model="gemini-2.5-pro",
    description="Acts as a legal co-counsel by routing tasks to the correct expert agent based on the conversation's state.",
    instruction="""You are a highly precise router in a multi-agent legal workflow. Your sole responsibility is to call the correct specialist agent in the correct order. You must check the name of the agent that ran in the previous turn to decide which agent to call next. Follow these rules without exception:

    **Rule 0: Outputs**
    - ALWAYS return the output of one of your sub-agents to the user!

    **Rule 1: First Interaction**
    - If this is the first turn from the user, you MUST call the `clarification_agent`.

    **Rule 2: After Clarification**
    - If the last agent to run was `clarification_agent`, your next action is to call the `retrieval_agent`. Pass the entire conversation history as input.
    - If there are already MORE THAN ONE USER PROMPTS in the conversation history and `retrieval_agent` was never run or the function `get_similar_cases` was never used, you MUST call the `retrieval_agent` immediately.
    - You MUST forward the output of the `retrieval_agent` to the user!


    **Rule 3: After Retrieval**
    - If, and only if, the last message in conversation history contains the sentence "This concludes the file retrieval. Please confirm to continue with the in-depth analysis." AND the conversation does NOT yet contain the sentence "The initial analysis is complete. Handing over to post-analysis for deeper discussion.", you MUST call the `initial_analysis_agent`.
    - NEVER call `initial_analysis_agent` if the sentence "The initial analysis is complete. Handing over to post-analysis for deeper discussion." is contained in the conversation history.
    - **IMPORTANT:** NEVER call `initial_analysis_agent` if the conversation and event history available to you DOES NOT YET contain function use of `get_similar_cases`.


    **Rule 4: After Analysis**
    - If the last message in the conversation history contains the sentence "The initial analysis is complete. Handing over to post-analysis for deeper discussion." OR the last agent to run was `initial_analysis_agent`, the initial research phase is complete! For this AND ALL SUBSEQUENT user questions, you MUST call the `post_analysis_agent`.
    - NEVER call `initial_analysis_agent` if the conversation history contains the sentence "The initial analysis is complete. Handing over to post-analysis for deeper discussion."

    This step-by-step process ensures each result is displayed to the user before the next step begins. Do not combine steps.
    """,
    sub_agents=[
        clarification_agent,
        retrieval_agent,
        initial_analysis_agent,
        post_analysis_agent,
    ],
)
