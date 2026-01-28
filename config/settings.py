# =============================================================================
# AI Graph Generator - Configuration Settings
# =============================================================================

# -----------------------------------------------------------------------------
# File Upload Settings
# -----------------------------------------------------------------------------
ALLOWED_EXTENSIONS = [".xlsx", ".xls", ".csv"]
MAX_FILE_SIZE_MB = 50
MAX_FILES = 10
MAX_TOTAL_SIZE_MB = 200

# -----------------------------------------------------------------------------
# Sandbox / Security Settings
# -----------------------------------------------------------------------------
TIMEOUT_SECONDS = 30
MAX_MEMORY_MB = 512

BLOCKED_OPERATIONS = [
    "exec",
    "eval",
    "compile",
    "__import__",
    "open",
    "os.system",
    "subprocess",
    "shutil.rmtree",
    "os.remove",
    "os.rmdir",
    "os.unlink",
    "pathlib.Path.unlink",
    "pathlib.Path.rmdir",
]

ALLOWED_MODULES = [
    "pandas",
    "numpy",
    "plotly",
    "plotly.express",
    "plotly.graph_objects",
    "plotly.subplots",
    "math",
    "statistics",
    "datetime",
    "re",
    "json",
    "collections",
    "itertools",
    "functools",
]

# -----------------------------------------------------------------------------
# Claude API Settings
# -----------------------------------------------------------------------------
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# -----------------------------------------------------------------------------
# Application Settings
# -----------------------------------------------------------------------------
APP_TITLE = "AI Graph Generator"

# Modes
SIMPLE_MODE = "simple"
ADVANCED_MODE = "advanced"
