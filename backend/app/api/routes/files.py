from fastapi import APIRouter, UploadFile, File

router = APIRouter(tags=["files"])

@router.get("")
def get_files_placeholder():
    """
    Placeholder endpoint to retrieve uploaded files list.
    """
    return {
        "message": "Files endpoint coming soon."
    }

@router.post("")
def post_files_placeholder(file: UploadFile = File(...)):
    """
    Placeholder endpoint to upload new document files.
    """
    return {
        "message": "Files endpoint coming soon.",
        "filename": file.filename
    }
