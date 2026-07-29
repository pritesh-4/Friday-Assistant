from enum import Enum


class IntentType(str, Enum):
    CONVERSATION = "Conversation"
    PROGRAMMING = "Programming"
    DEBUGGING = "Debugging"
    LEARNING = "Learning"
    RESEARCH = "Research"
    PLANNING = "Planning"
    WRITING = "Writing"
    CREATIVE = "Creative"
    MEMORY_RECALL = "Memory Recall"
    AUTOMATION = "Automation"
    REPOSITORY_ANALYSIS = "Repository Analysis"
    CODE_GENERATION = "Code Generation"
    CODE_REVIEW = "Code Review"
    DEPLOYMENT = "Deployment"
    FILE_ANALYSIS = "File Analysis"
    IMAGE_ANALYSIS = "Image Analysis"
    VISION = "Vision"
    VOICE_COMMAND = "Voice Command"
    SYSTEM_COMMAND = "System Command"
    SCHEDULING = "Scheduling"
    SEARCH = "Search"
    GENERAL_QUESTION = "General Question"
    UNKNOWN = "Unknown"


class RiskLevel(str, Enum):
    SAFE = "Safe"
    NEEDS_CONFIRMATION = "Needs Confirmation"
    HIGH_IMPACT = "High Impact"
    DESTRUCTIVE = "Destructive"
    EXPENSIVE = "Expensive"
    REQUIRES_AUTH = "Requires Authentication"
    REQUIRES_CLARIFICATION = "Requires Clarification"


class ProviderType(str, Enum):
    CLAUDE = "Claude"
    GEMINI = "Gemini"
    GPT = "GPT"
    LIGHTWEIGHT = "Lightweight"
    VISION_MODEL = "Vision"
    CODER_MODEL = "Coder"


class ToolType(str, Enum):
    REPOSITORY_ANALYZER = "Repository Analyzer"
    WEB_SEARCH = "Web Search"
    MEMORY_RETRIEVAL = "Memory Retrieval"
    CALCULATOR = "Calculator"
    PLANNER = "Planner"
    VISION = "Vision"
    OCR = "OCR"
    CODE_EXECUTOR = "Code Executor"
    DEPLOYMENT_INSPECTOR = "Deployment Inspector"
    GIT_ANALYZER = "Git Analyzer"
    VOICE = "Voice"
    IMAGE_GENERATOR = "Image Generator"


class ContextSource(str, Enum):
    CONVERSATION = "Conversation"
    LONG_TERM_MEMORY = "Long-term Memory"
    REPOSITORY = "Repository"
    CURRENT_WORKSPACE = "Current Workspace"
    FILES = "Files"
    IMAGES = "Images"
    WEB_SEARCH = "Web Search"
    CALENDAR = "Calendar"
    AUTOMATION_STATE = "Automation State"
    VOICE_CONTEXT = "Voice Context"
    VISION_CONTEXT = "Vision Context"
    SYSTEM_STATE = "System State"
