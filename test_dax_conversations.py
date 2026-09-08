import os
import sys
import asyncio

# Ensure backend and tests paths are loaded
sys.path.insert(0, os.path.abspath('backend'))
sys.path.insert(0, os.path.abspath('tests'))

from test_dax_conversations import run_dax_conversation_suite

if __name__ == "__main__":
    asyncio.run(run_dax_conversation_suite())
