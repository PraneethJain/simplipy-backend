from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import ast
from simplipy.parse.parse import Visitor
from simplipy.semantics.state import State
from uuid import uuid4

app = FastAPI(title="SimpliPy Debugger API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: dict[str, State] = {}


class ProgramRequest(BaseModel):
    code: str
    filename: Optional[str] = "program.py"


class SessionResponse(BaseModel):
    session_id: str
    initial_state: Dict


class StepResponse(BaseModel):
    state: Dict
    finished: bool


@app.post("/api/program", response_model=SessionResponse)
async def create_program(program: ProgramRequest):
    """
    Create a new session with the provided code.
    Returns the session ID and initial program state.
    """
    try:
        tree = ast.parse(program.code, filename=program.filename)
        visitor = Visitor()
        pgm = visitor.parse_pgm(tree)

        state = State(pgm)
        session_id = str(uuid4())
        sessions[session_id] = state
        initial_state = state.as_dict()

        return {"session_id": session_id, "initial_state": initial_state}

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to parse program: {str(e)}"
        )


@app.get("/api/step/{session_id}", response_model=StepResponse)
async def step_program(session_id: str):
    """
    Execute the next step in the program and return the updated state.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[session_id]

    try:
        if state.is_final():
            return state.as_dict()

        state.step()

        current_state = state.as_dict()

        return {
            "state": current_state,
            "finished": state.is_final(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during program execution: {e}"
        )


@app.get("/api/state/{session_id}")
async def get_state(session_id: str):
    """
    Get the current state of the program without stepping.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[session_id]

    return state.as_dict()


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a debugging session.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del sessions[session_id]
    return {"message": "Session deleted successfully"}


@app.post("/api/reset/{session_id}")
async def reset_session(session_id: str, program: Optional[ProgramRequest] = None):
    """
    Reset a session to its initial state or with new code.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    if program:
        try:
            tree = ast.parse(program.code, filename=program.filename)
            visitor = Visitor()
            pgm = visitor.parse_pgm(tree)
            sessions[session_id] = State(pgm)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to parse program: {str(e)}"
            )
    else:
        try:
            state = sessions[session_id]
            pgm = state.pgm
            sessions[session_id] = State(pgm)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to reset session: {str(e)}"
            )

    state = sessions[session_id]
    initial_state = state.as_dict()

    return {"session_id": session_id, "initial_state": initial_state}


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app, host="0.0.0.0", port=8000)
