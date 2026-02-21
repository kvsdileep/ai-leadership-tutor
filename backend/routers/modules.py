from fastapi import APIRouter
from backend.models import ModuleResponse
from backend.services.tutor_engine import load_curriculum

router = APIRouter(prefix="/api/modules", tags=["modules"])

AVAILABLE_MODULES = ["foundations-of-leadership"]


@router.get("", response_model=list[ModuleResponse])
async def list_modules():
    modules = []
    for module_id in AVAILABLE_MODULES:
        c = load_curriculum(module_id)
        modules.append(ModuleResponse(
            id=c["id"],
            title=c["title"],
            title_hi=c.get("title_hi", c["title"]),
            description=c["description"],
            section_count=len(c["sections"]),
            estimated_minutes=c["estimated_minutes"],
        ))
    return modules


@router.get("/{module_id}", response_model=ModuleResponse)
async def get_module(module_id: str):
    c = load_curriculum(module_id)
    return ModuleResponse(
        id=c["id"],
        title=c["title"],
        title_hi=c.get("title_hi", c["title"]),
        description=c["description"],
        section_count=len(c["sections"]),
        estimated_minutes=c["estimated_minutes"],
    )
