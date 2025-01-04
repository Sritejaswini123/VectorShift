from fastapi import FastAPI, Form,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from huggingface_hub import InferenceApi

app = FastAPI()

#Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://127.0.0.1:3000', 'http://localhost:3000', 'http://127.0.0.1:3001', 'http://localhost:3001'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
    )
# Hugging Face Inference API setup
HF_ACCESS_TOKEN = "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"
model = "gpt2"  # Specify the Hugging Face model to use
inference_api = InferenceApi(repo_id=model, token=HF_ACCESS_TOKEN)

@app.get('/')
def read_root():
    return {'Ping': 'Pong'}



# Request model for the /llm/query endpoint
class LLMRequest(BaseModel):
    prompt: str
# Endpoint to handle LLM queries
@app.post("/llm/query")
def query_llm(request: LLMRequest):
    # Validate the prompt
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    
    # Query Hugging Face API
    try:
        response = inference_api(inputs=request.prompt)
        if not response or "error" in response:
            raise HTTPException(status_code=500, detail="Error querying Hugging Face API.")
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


class PipelineData(BaseModel):
    nodes: list
    edges: list


@app.post('/pipelines/parse')
def parse_pipeline(pipeline: PipelineData):
    print(pipeline)
    print(pipeline.nodes, pipeline.edges)
    num_nodes = len(pipeline.nodes)
    num_edges = len(pipeline.edges)

    #Logic to determine if it is a DAG
    degrees = {}

    stack = []

    for edge in pipeline.edges:
        if edge["target"] in degrees:
            degrees[edge["target"]] += 1
        else:
            degrees[edge["target"]] = 1

    for node in pipeline.nodes:
        if node["id"] not in degrees:
            stack.append(node["id"])

    
    while len(stack) > 0 :
        #get first element of stack
        currentNode = stack.pop(0)

        #find the connections of that node in edges
        for edge in pipeline.edges:
            if currentNode == edge["source"]:
                connection = edge["target"]
                print(connection)
                degrees[connection] -= 1
                if degrees[connection] == 0:
                    stack.append(edge["target"])

    dag = True

    #loop through
    for connection in degrees.values():
        if connection > 0:
            dag = False
            break

    return {'num_nodes': num_nodes, 'num_edges': num_edges, 'is_dag': dag}

