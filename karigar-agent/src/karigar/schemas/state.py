from typing import TypedDict, List, Optional
from langgraph.graph.message import add_messages
from typing import Annotated

class KarigarState(TypedDict):
    messages: Annotated[list, add_messages]
    artisan_id: str
    material_request: Optional[dict]
    supplier_quotes: List[dict]
    selected_quote: Optional[dict]
    order_details: Optional[dict]
    store_url: Optional[str]
    status: str