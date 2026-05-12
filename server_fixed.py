"""FastAPI server for RAG service."""

"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.cache import cache_manager"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.cache import cache_manager
from src.config.logging_config import RAGLogger
from src.config.settings import settings
from src"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.cache import cache_manager
from src.config.logging_config import RAGLogger
from src.config.settings import settings
from src.generation.generator import AnswerGenerator, ConfidenceEstimator"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.cache import cache_manager
from src.config.logging_config import RAGLogger
from src.config.settings import settings
from src.generation.generator import AnswerGenerator, ConfidenceEstimator
from src.generation.conversation import (
    get_conversation_manager,
    ContextAwareQueryEnh"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.cache import cache_manager
from src.config.logging_config import RAGLogger
from src.config.settings import settings
from src.generation.generator import AnswerGenerator, ConfidenceEstimator
from src.generation.conversation import (
    get_conversation_manager,
    ContextAwareQueryEnhancer,
    ConversationPromptBuilder,
)
from src.retrieval.retriever import Retriever"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.cache import cache_manager
from src.config.logging_config import RAGLogger
from src.config.settings import settings
from src.generation.generator import AnswerGenerator, ConfidenceEstimator
from src.generation.conversation import (
    get_conversation_manager,
    ContextAwareQueryEnhancer,
    ConversationPromptBuilder,
)
from src.retrieval.retriever import RetrieverFactory
from src.retrieval.bilingual import get_language_detector, get_bilingual_query_enh"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.cache import cache_manager
from src.config.logging_config import RAGLogger
from src.config.settings import settings
from src.generation.generator import AnswerGenerator, ConfidenceEstimator
from src.generation.conversation import (
    get_conversation_manager,
    ContextAwareQueryEnhancer,
    ConversationPromptBuilder,
)
from src.retrieval.retriever import RetrieverFactory
from src.retrieval.bilingual import get_language_detector, get_bilingual_query_enhancer
from src.utils.exceptions import RAGError
from src.config.settings import RetrievalMode
"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.cache import cache_manager
from src.config.logging_config import RAGLogger
from src.config.settings import settings
from src.generation.generator import AnswerGenerator, ConfidenceEstimator
from src.generation.conversation import (
    get_conversation_manager,
    ContextAwareQueryEnhancer,
    ConversationPromptBuilder,
)
from src.retrieval.retriever import RetrieverFactory
from src.retrieval.bilingual import get_language_detector, get_bilingual_query_enhancer
from src.utils.exceptions import RAGError
from src.config.settings import RetrievalMode
from src.utils.types import RAGResponse
from src.api.auth import api_auth, get_auth_enabled"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.cache import cache_manager
from src.config.logging_config import RAGLogger
from src.config.settings import settings
from src.generation.generator import AnswerGenerator, ConfidenceEstimator
from src.generation.conversation import (
    get_conversation_manager,
    ContextAwareQueryEnhancer,
    ConversationPromptBuilder,
)
from src.retrieval.retriever import RetrieverFactory
from src.retrieval.bilingual import get_language_detector, get_bilingual_query_enhancer
from src.utils.exceptions import RAGError
from src.config.settings import RetrievalMode
from src.utils.types import RAGResponse
from src.api.auth import api_auth, get_auth_enabled

logger = RAGLogger("api")

#"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.cache import cache_manager
from src.config.logging_config import RAGLogger
from src.config.settings import settings
from src.generation.generator import AnswerGenerator, ConfidenceEstimator
from src.generation.conversation import (
    get_conversation_manager,
    ContextAwareQueryEnhancer,
    ConversationPromptBuilder,
)
from src.retrieval.retriever import RetrieverFactory
from src.retrieval.bilingual import get_language_detector, get_bilingual_query_enhancer
from src.utils.exceptions import RAGError
from src.config.settings import RetrievalMode
from src.utils.types import RAGResponse
from src.api.auth import api_auth, get_auth_enabled

logger = RAGLogger("api")

# Performance metrics tracking
PERFORMANCE_METRICS = {
"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.cache import cache_manager
from src.config.logging_config import RAGLogger
from src.config.settings import settings
from src.generation.generator import AnswerGenerator, ConfidenceEstimator
from src.generation.conversation import (
    get_conversation_manager,
    ContextAwareQueryEnhancer,
    ConversationPromptBuilder,
)
from src.retrieval.retriever import RetrieverFactory
from src.retrieval.bilingual import get_language_detector, get_bilingual_query_enhancer
from src.utils.exceptions import RAGError
from src.config.settings import RetrievalMode
from src.utils.types import RAGResponse
from src.api.auth import api_auth, get_auth_enabled

logger = RAGLogger("api")

# Performance metrics tracking
PERFORMANCE_METRICS = {
    "total_requests": 0,
    "total_errors": 0,
    "total_query"""FastAPI server for RAG service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.cache import cache_manager
from src.config.logging_config import RAGLogger
from src.config.settings import settings
from src.generation.generator import AnswerGenerator, ConfidenceEstimator
from src.generation.conversation import (
    get_conversation_manager,
    ContextAwareQueryEnhancer,
    ConversationPromptBuilder,
)
from src.retrieval.retriever import RetrieverFactory
from src.retrieval.bilingual import get_language_detector, get_bilingual_query_enhancer
from src.utils.exceptions import RAGError
from src.config.settings import RetrievalMode
from src.utils.types import RAGResponse
from src.api.auth import api_auth, get_auth_enabled

logger = RAGLogger("api")

# Performance metrics tracking
PERFORMANCE_METRICS = {
    "total_requests": 0,
    "total_errors": 0,
    "total_query_time_ms": 0.0,
    "request_times": [],  # Last 100 request