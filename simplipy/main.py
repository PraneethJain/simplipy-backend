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
    program_structure: Dict
    ctf_table: Dict[str, Dict[int, int]]


class StepResponse(BaseModel):
    state: Dict
    finished: bool


@app.post("/api/program", response_model=SessionResponse)
async def create_program_session(program_request: ProgramRequest):
    """
    Parses code, creates a session, calculates CTFs, and returns initial state,
    program structure, and CTFs.
    """
    try:
        tree = ast.parse(program_request.code, filename=program_request.filename)
        visitor = Visitor()
        pgm = visitor.parse_pgm(tree)

        state = State(pgm)
        initial_state_dict = state.as_dict()
        program_structure_dict = pgm.to_dict()
        ctf_table = state.ctfs

        session_id = str(uuid4())
        sessions[session_id] = state

        return SessionResponse(
            session_id=session_id,
            initial_state=initial_state_dict,
            program_structure=program_structure_dict,
            ctf_table=ctf_table,
        )

    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Syntax Error: {e}")
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize session: {type(e).__name__}: {e}",
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
        finished = state.is_final()
        if not finished:
            state.step()
            finished = state.is_final()

        current_state_dict = state.as_dict()

        return StepResponse(
            state=current_state_dict,
            finished=finished,
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
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
async def reset_session(
    session_id: str, program_request: Optional[ProgramRequest] = None
):
    """
    Reset a session to its initial state, optionally with new code.
    Returns the session ID, new initial state, program structure, and CTFs.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        if program_request:
            tree = ast.parse(program_request.code, filename=program_request.filename)
            visitor = Visitor()
            pgm = visitor.parse_pgm(tree)
        else:
            pgm = sessions[session_id].pgm

        new_state = State(pgm)
        new_initial_state_dict = new_state.as_dict()
        new_program_structure_dict = pgm.to_dict()
        new_ctf_table = new_state.ctfs

        sessions[session_id] = new_state

        return SessionResponse(
            session_id=session_id,
            initial_state=new_initial_state_dict,
            program_structure=new_program_structure_dict,
            ctf_table=new_ctf_table,
        )

    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Syntax Error: {e}")
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to reset session: {e}")
