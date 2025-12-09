# AI-based threat detection in Large Language Models
Evaluated guardrails, prompt design and a classification model to assess their effectiveness in mitigating direct prompt injection attacks. Integrated the Model Context Protocol to standardize and secure API interaction. Setup a sandbox mode to provide hands-on experience.

My main contributions:
Everyhing except [Homepage.py](Homepage.py) was fully written by me. [Homepage.py](Homepage.py) is inspired by another project and has been extended to include a sandbox mode.

Security-Evaluation on custom dataset:

<img height="250" alt="image" src="results/evaluation.png" />


User-Application to try custom security setups:

<img height="400" alt="image" src="results/user_application.png" />


## 1 Setup Environment
Note: You will have to install GuardrailsAI manually (see Section 2)

To set up a new Conda environment with Python 3.10 and install the required dependencies:

```bash
conda create --name hacking_bot python=3.10 -y
conda activate hacking_bot
pip install -r requirements.txt
```
## 2 Manual GuardrailsAI setup
To install guardrail from GuardrailsAI use:
```
guardrails configure
guardrails hub install hub://guardrails/guardrails_pii
```
Note: You will have to get an API key from their service.

## 3 OpenAI API key

Create a file secrets.toml in .streamlit/ and add your OpenAI key as OPENAI_API_KEY="..."

## 4 How to Run the Application

```bash
streamlit run Homepage.py
```


## 5 How to Debug an MCP server
```bash
mcp dev src/utils/mcp_server.py
```
more information here: https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file
The mcp dev seems to be buggy from time to time.
It worked after waiting 10-20s and just then start.
